"""Classes for managing archives."""

import json
import os
import shutil
from datetime import datetime
from enum import Enum
from pathlib import Path, PosixPath
from typing import TYPE_CHECKING, List, Optional, Tuple

from cyberfusion.BorgSupport.borg_cli import (
    BorgCommand,
    BorgLoggedCommand,
    BorgRegularCommand,
)
from cyberfusion.BorgSupport.operations import Operation
from cyberfusion.Common import generate_random_string

if TYPE_CHECKING:  # pragma: no cover
    from cyberfusion.BorgSupport.repositories import Repository


class UNIXFileTypes(Enum):
    """UNIX file types.

    These are not complete (e.g. some specific file types for Cray DMF, Solaris,
    HP-UX are missing). However, we don't expect those in any case. Some of the
    types that could exist in theory but shouldn't, such as 'FIFO' and 'SOCKET',
    are present, but commented out.
    """

    REGULAR_FILE = "-"
    # BLOCK_SPECIAL_FILE = 'b'
    # CHARACTER_SPECIAL_FILE ='c'
    DIRECTORY = "d"
    SYMBOLIC_LINK = "l"
    # FIFO='p'
    # SOCKET = 's'
    # OTHER = '?'


class FilesystemObject:
    """Abstraction of filesystem object in archive contents.

    The following keys that are present in the line cannot be accessed as we deem
    them irrelevant:

    * uid: use 'user' instead; the username is more relevant than the UID
    * gid: use 'group' instead; the group name is more relevant than the GID
    * healthy: if a file is 'broken', 'borg check' should already catch that
      the repository/archive is not consistent. The 'check' operation should be
      run regularly. The user shouldn't even get this far if the repository or
      archive is corrupt, so a 'broken' file is not the concern of this code,
      and therefore this attribute not returned.
    * source: we doubt the user is interested in this, and hard links should be rarely used
    * flags: we doubt the user is interested in this, and is usually 'null'
    """

    def __init__(self, line: dict) -> None:
        """Set attributes."""
        self._line = line

    @property
    def type_(self) -> UNIXFileTypes:
        """Get object type.

        Should only be one of the following in practice:

        * UNIXFileTypes.REGULAR_FILE
        * UNIXFileTypes.DIRECTORY
        * UNIXFileTypes.SYMBOLIC_LINK
        """
        return UNIXFileTypes(self._line["type"])

    @property
    def symbolic_mode(self) -> str:
        """Get symbolic mode.

        This method is named the way it is so that we can add conversion to other
        representations of the mode later (e.g. symbolic -> octal -> numeric).
        """
        return self._line["mode"]

    @property
    def user(self) -> str:
        """Get user."""
        return self._line["user"]

    @property
    def group(self) -> str:
        """Get group."""
        return self._line["group"]

    @property
    def path(self) -> str:
        """Get path."""
        return self._line["path"]

    @property
    def link_target(self) -> Optional[str]:
        """Get link target.

        If the object type is not a symlink, None is returned.
        """
        if self.type_ != UNIXFileTypes.SYMBOLIC_LINK:
            return None

        # For symlinks, 'source' and 'linktarget' both refer to the target. However,
        # for regular files, 'source' refers to the hard link master. As by now we know
        # we're dealing with a symlink, it doesn't matter if we use the value of 'source'
        # or 'linktarget'.
        #
        # Source: https://github.com/borgbackup/borg/issues/2324#issuecomment-289253843

        return self._line["linktarget"]

    @property
    def modification_time(self) -> datetime:
        """Get modification time.

        A naive timestamp is returned. The time is the local timezone.

        The modification time is most relevant for users (as opposed to ctime).
        """

        # There is no difference between 'iso*time' and '*time' when using JSON

        return datetime.strptime(self._line["mtime"], "%Y-%m-%dT%H:%M:%S.%f")

    @property
    def size(self) -> Optional[int]:
        """Get size of object in archive in bytes.

        If the object type is not a regular file, None is returned. Borg does
        return a size for such object types, but their values are irrelevant.

        Note that the size of the original object, and the size of the object in
        the archive may differ.
        """
        if self.type_ != UNIXFileTypes.REGULAR_FILE:
            return None

        return self._line["size"]


class Archive:
    """Abstraction of Borg archive."""

    def __init__(
        self,
        *,
        repository: "Repository",
        name: str,
        comment: str,
    ) -> None:
        """Set variables."""
        self.repository = repository

        self._name = name
        self._comment = comment

    @property
    def name(self) -> str:
        """Get archive name with repository path.

        Borg needs this format to identify the repository and archive.
        """
        return self.repository.path + "::" + self._name

    @property
    def comment(self) -> str:
        """Get archive comment.

        This is a free-form attribute.
        """
        return self._comment

    def contents(self, *, path: Optional[str]) -> List[FilesystemObject]:
        """Get contents of archive.

        If 'path' is None, no path will be passed to Borg. As far as we are aware,
        this is equal to starting at the root, i.e. specifying '/' as path.

        Contents are filesystem objects, i.e. directories and files.
        """

        # Construct arguments

        arguments = ["--json-lines", self.name]

        if path:
            arguments.append(path)

        # Execute command

        results = []

        command = BorgRegularCommand()
        command.execute(
            command=BorgCommand.SUBCOMMAND_LIST,
            arguments=arguments,
            **self.repository._safe_cli_options,
        )

        for (
            _line
        ) in command.stdout.splitlines():  # Each line is a JSON document
            line = json.loads(_line)

            results.append(FilesystemObject(line))

        return results

    def create(
        self,
        *,
        paths: List[str],
        excludes: List[str],
        working_directory: str = os.path.sep,
    ) -> Operation:
        """Create archive.

        For excludes, see https://borgbackup.readthedocs.io/en/stable/usage/help.html

        When creating a Borg archive, all paths are included, starting from the
        working directory.

        E.g. if `borg create` runs in the working directory `/`, and the path
        `/home/test/domains` is included in the archive, the archive contains
        the directory structure `home/test/domains/`.

        E.g. if `borg create` runs in the working directory `/home/test`, and
        the path `domains` is included in the archive, the archive contains the
        directory structure `domains/`.

        From https://borgbackup.readthedocs.io/en/stable/usage/create.html#borg-create

        > This command creates a backup archive containing all files found while
        > recursively traversing all paths specified. Paths are added to the
        > archive as they are given, that means if relative paths are desired,
        > the command has to be run from the correct directory.
        """

        # Construct arguments

        arguments = ["--one-file-system", "--comment", self.comment]

        for exclude in excludes:
            arguments.extend(["--exclude", exclude])

        arguments.append(self.name)
        arguments.extend(paths)

        # Execute command

        command = BorgLoggedCommand()
        command.execute(
            command=BorgCommand.SUBCOMMAND_CREATE,
            arguments=arguments,
            working_directory=working_directory,
            **self.repository._safe_cli_options,
        )

        return Operation(progress_file=command.file)

    def extract(
        self,
        *,
        destination_path: str,
        restore_paths: List[str],
        strip_components: Optional[int] = None,
    ) -> Tuple[Operation, str]:
        """Extract paths in archive to destination."""

        # Construct arguments

        arguments = []

        if strip_components:
            arguments.append(f"--strip-components={strip_components}")

        arguments.append(self.name)
        arguments.extend(restore_paths)

        # Execute command

        command = BorgLoggedCommand()
        command.execute(
            command=BorgCommand.SUBCOMMAND_EXTRACT,
            arguments=arguments,
            working_directory=destination_path,  # Borg extracts in working directory
            **self.repository._safe_cli_options,
        )

        return Operation(progress_file=command.file), destination_path

    def export_tar(
        self,
        *,
        destination_path: str,
        restore_paths: List[str],
        strip_components: int,
    ) -> Tuple[Operation, str]:
        """Export archive to tarball."""

        # Construct arguments

        arguments = [
            f"--strip-components={strip_components}",
            self.name,
            destination_path,
        ]
        arguments.extend(restore_paths)

        # Execute command

        command = BorgLoggedCommand()
        command.execute(
            command=BorgCommand.SUBCOMMAND_EXPORT_TAR,
            arguments=arguments,
            **self.repository._safe_cli_options,
        )

        return Operation(progress_file=command.file), destination_path


class ArchiveRestoration:
    """Abstraction of Borg archive restore process.

    Restores path in archive to path on local filesystem.

    Borg does not have built-in support for 'restores'. This function extracts
    the given path in the Borg archive to a temporary directory. It then
    replaces the path on the local filesystem with the temporary directory.

    This only works when the relative path in the archive is the full path
    to the absolute path on the local filesystem, i.e. the archive was created
    in / (see Archive.create docstring). We rely on this logic as Borg does
    not keep track of the original location of files explicitly.

    'path' should be the absolute path on the local filesystem. The leading
    slash is automatically stripped when referencing the file in the archive.
    """

    PREFIX_RESTORE_FILESYSTEM_OBJECT = ".archive-restore"

    def __init__(
        self,
        *,
        archive: Archive,
        path: str,
        temporary_path_root_path: str,
        enforce_home_directory: bool = False,
    ):
        """Set attributes."""
        if not path.startswith(os.path.sep):
            raise ValueError(f"Path has to start with {os.path.sep}")

        self.archive = archive
        self._path = path
        self._enforce_home_directory = enforce_home_directory
        self.filesystem_path = self._path

        self._check_type()
        self.temporary_path = self._create_temporary_path(
            root_path=temporary_path_root_path
        )

    def _check_type(self) -> None:
        """Raise exception if type of filesystem object is not supported."""
        if self.type_ in [UNIXFileTypes.DIRECTORY, UNIXFileTypes.REGULAR_FILE]:
            return

        raise NotImplementedError

    @property
    def type_(self) -> UNIXFileTypes:
        """Set type of filesystem object at path."""
        return next(  # Raises StopIteration if no results
            filter(
                lambda x: x.path == self.archive_path,
                self.archive.contents(path=self.archive_path),
            )
        ).type_

    @property
    def filesystem_path(self) -> str:
        """Set filesystem path.

        Path on local filesystem is absolute, so is path with leading slash. See
        docstring for more information.
        """
        return self._filesystem_path

    @filesystem_path.setter
    def filesystem_path(self, value: str) -> None:
        """Set filesystem path.

        Checks if filesystem path is in user home directory.
        Path is 1) the path that is restored from the archive and 2) the
        restore destination on the local filesystem. Restoring an arbitrary
        path from the archive is relatively safe, as it should never contain
        paths other than those owned by the user. Nonetheless, it's not neat
        to be able to restore to an arbitrary path on the local filesystem.
        Therefore, we explicitly check if the path is in the home directory
        of the user executing this script.
        """
        if (
            self._enforce_home_directory
            and Path.home() not in PosixPath(value).parents
        ):
            raise ValueError("Path must be in user home directory")

        self._filesystem_path = value

    @property
    def archive_path(self) -> str:
        """Set archive path.

        Path in archive is relative, so is path without leading slash. See docstring
        for more information.
        """
        return self._path[len(os.path.sep) :]

    def _create_temporary_path(self, *, root_path: str) -> str:
        """Generate and create temporary path."""
        temporary_path = os.path.join(
            root_path,
            self.PREFIX_RESTORE_FILESYSTEM_OBJECT
            + "-"
            + generate_random_string(),
        )

        os.mkdir(temporary_path)
        os.chmod(temporary_path, 0o700)

        return temporary_path

    @property
    def bak_path(self) -> str:
        """Set bak path."""
        return self.filesystem_path + ".bak"

    @property
    def strip_components(self) -> int:
        """Set amount of components to strip."""
        if self.type_ != UNIXFileTypes.DIRECTORY:
            return len(Path(self.archive_path).parts) - 1

        return len(
            Path(self.archive_path).parts
        )  # Make sure directory contents are in root

    def extract(self) -> None:
        """Extract archive path to temporary path."""
        self.archive.extract(
            destination_path=self.temporary_path,
            restore_paths=[self.archive_path],
            strip_components=self.strip_components,
        )

    def replace(self) -> None:
        """Replace object on local filesystem with object from archive.

        This should be a nearly race-free process, i.e. there should be almost no
        downtime when replacing. This is done by following these steps:

        - Filesystem object is extracted from archive to temporary path on the
          local filesystem.
        - Current filesystem path on local filesystem is moved to the bak path.
          The structure is now 'broken'.
        - The filesystem object is moved from the temporary path on the local
          filesystem to the filesystem path on the local filesystem. The structure
          is now 'restored'.
        """
        self.extract()

        if self.type_ == UNIXFileTypes.REGULAR_FILE:
            shutil.move(
                os.path.join(
                    self.temporary_path, os.path.basename(self.archive_path)
                ),
                self.filesystem_path,
            )

            return

        # When we get here, we know self.type_ is UNIXFileTypes.DIRECTORY (see
        # self._check_type)

        if os.path.isdir(
            self.filesystem_path
        ):  # Directory could have been removed between archive create and restore
            os.rename(self.filesystem_path, self.bak_path)

        os.rename(self.temporary_path, self.filesystem_path)

        if os.path.isdir(self.bak_path):
            shutil.rmtree(self.bak_path)
