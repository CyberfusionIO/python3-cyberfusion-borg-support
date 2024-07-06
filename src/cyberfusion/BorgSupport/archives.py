"""Classes for managing archives."""

import json
import os
import shutil
from datetime import datetime
from enum import Enum
from pathlib import Path, PosixPath
from typing import TYPE_CHECKING, Any, Callable, List, Optional, Tuple, TypeVar

from cached_property import cached_property

from cyberfusion.BorgSupport import PassphraseFile
from cyberfusion.BorgSupport.borg_cli import (
    BorgCommand,
    BorgLoggedCommand,
    BorgRegularCommand,
)
from cyberfusion.BorgSupport.exceptions import (
    PathNotExistsError,
    RepositoryLockedError,
)
from cyberfusion.BorgSupport.operations import Operation
from cyberfusion.BorgSupport.utilities import (
    generate_random_string,
    get_md5_hash,
)

if TYPE_CHECKING:  # pragma: no cover
    from cyberfusion.BorgSupport.repositories import Repository

F = TypeVar("F", bound=Callable[..., Any])


def archive_check_repository_not_locked(f: F) -> Any:
    """Check that repository is not locked for Archive class."""

    def wrapper(self: Any, *args: tuple, **kwargs: dict) -> Any:
        if self.repository.is_locked:
            raise RepositoryLockedError

        return f(self, *args, **kwargs)

    return wrapper


def archive_restoration_check_repository_not_locked(f: F) -> Any:
    """Check that repository is not locked for ArchiveRestoration class."""

    def wrapper(self: Any, *args: tuple, **kwargs: dict) -> Any:
        if self.archive.repository.is_locked:
            raise RepositoryLockedError

        return f(self, *args, **kwargs)

    return wrapper


class UNIXFileType(Enum):
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
    def type_(self) -> UNIXFileType:
        """Get object type.

        Should only be one of the following in practice:

        * UNIXFileType.REGULAR_FILE
        * UNIXFileType.DIRECTORY
        * UNIXFileType.SYMBOLIC_LINK
        """
        return UNIXFileType(self._line["type"])

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
        if self.type_ != UNIXFileType.SYMBOLIC_LINK:
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
        if self.type_ != UNIXFileType.REGULAR_FILE:
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

        self.name = name
        self._comment = comment

    @property
    def full_name(self) -> str:
        """Get archive name with repository path.

        Borg needs this format to identify the repository and archive.
        """
        return self.repository.path + "::" + self.name

    @property
    def comment(self) -> str:
        """Get archive comment.

        This is a free-form attribute.
        """
        return self._comment

    @archive_check_repository_not_locked
    def contents(
        self, *, path: Optional[str], recursive: bool = True
    ) -> List[FilesystemObject]:
        """Get contents of archive.

        If 'path' is None, no path will be passed to Borg. As far as we are aware,
        this is equal to starting at the root, i.e. specifying '/' as path.

        If 'recursive' is True, all contents from the given path, including
        those in subdirectories, are returned. This is the default behaviour
        by Borg. If 'recursive' is False, only the contents in the given path
        and the filesystem object of that path itself are returned.

        Contents are filesystem objects, i.e. directories and files.
        """

        # Construct arguments

        arguments = ["--json-lines", self.full_name]

        if path:
            arguments.append(path)

        # Execute command

        results = []

        command = BorgRegularCommand()

        with PassphraseFile(self.repository.passphrase) as environment:
            command.execute(
                command=BorgCommand.SUBCOMMAND_LIST,
                arguments=arguments,
                **self.repository._cli_options,
                environment=environment,
            )

        lines = command.stdout.splitlines()

        if (
            lines == []
        ):  # See https://github.com/borgbackup/borg/discussions/8273
            raise PathNotExistsError

        for _line in lines:
            line = json.loads(_line)

            # If not recursive, skip if the path of this filesystem object is
            # not the given path or directly inside the given path. Borg does
            # not support doing this natively, see the dead end at https://mail.python.org/pipermail/borgbackup/2017q4/000928.html

            if path and not recursive:
                is_path = line["path"] == path

                path_is_parent = Path(
                    os.path.join(
                        os.path.sep, line["path"]
                    )  # Convert from relative to absolute for check
                ).parent == PosixPath(os.path.join(os.path.sep, path))

                if not path_is_parent and not is_path:
                    continue

            results.append(FilesystemObject(line))

        return results

    @archive_check_repository_not_locked
    def create(
        self,
        *,
        paths: List[str],
        excludes: List[str],
        working_directory: str = os.path.sep,
        remove_paths_if_file: bool = False,
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

        arguments.append(self.full_name)
        arguments.extend(paths)

        # Execute command

        command = BorgLoggedCommand()

        with PassphraseFile(self.repository.passphrase) as environment:
            command.execute(
                command=BorgCommand.SUBCOMMAND_CREATE,
                arguments=arguments,
                working_directory=working_directory,
                **self.repository._cli_options,
                environment=environment,
            )

        # Remove paths

        if remove_paths_if_file:
            for path in paths:
                if not os.path.isfile(path):
                    continue

                os.unlink(path)

        return Operation(progress_file=command.file)

    @archive_check_repository_not_locked
    def extract(
        self,
        *,
        destination_path: str,
        restore_paths: List[str],
        strip_components: Optional[int] = None,
    ) -> Tuple[Operation, str]:
        """Extract paths in archive to destination.

        The given destination path will be created with 0700 permissions if it
        does not exist.
        """

        # Construct arguments

        arguments = []

        if strip_components:
            arguments.append(f"--strip-components={strip_components}")

        arguments.append(self.full_name)
        arguments.extend(restore_paths)

        # Create directory with correct permissions

        if not os.path.isdir(destination_path):
            os.mkdir(destination_path)
            os.chmod(destination_path, 0o700)

        # Execute command

        command = BorgLoggedCommand()

        with PassphraseFile(self.repository.passphrase) as environment:
            command.execute(
                command=BorgCommand.SUBCOMMAND_EXTRACT,
                arguments=arguments,
                working_directory=destination_path,  # Borg extracts in working directory
                **self.repository._cli_options,
                environment=environment,
            )

        return Operation(progress_file=command.file), destination_path

    @archive_check_repository_not_locked
    def export_tar(
        self,
        *,
        destination_path: str,
        restore_paths: List[str],
        strip_components: int,
    ) -> Tuple[Operation, str, str]:
        """Export archive to tarball.

        The given destination path will be created with 0600 permissions.
        """

        # Construct arguments

        arguments = [
            f"--strip-components={strip_components}",
            self.full_name,
            destination_path,
        ]
        arguments.extend(restore_paths)

        # Create file with correct permissions

        with open(destination_path, "w"):
            pass

        os.chmod(destination_path, 0o600)

        # Execute command

        command = BorgLoggedCommand()

        with PassphraseFile(self.repository.passphrase) as environment:
            command.execute(
                command=BorgCommand.SUBCOMMAND_EXPORT_TAR,
                arguments=arguments,
                **self.repository._cli_options,
                environment=environment,
            )

        return (
            Operation(progress_file=command.file),
            destination_path,
            get_md5_hash(destination_path),
        )


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

    # Ensure all restore-related directories start with this prefix. The prefix
    # might be used by other systems to recognise directories that are related
    # to a Borg archive restore.

    PREFIX_RESTORE_FILESYSTEM_OBJECT = ".archive-restore-"

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
        if self.type_ in [UNIXFileType.DIRECTORY, UNIXFileType.REGULAR_FILE]:
            return

        raise NotImplementedError

    @property
    def type_(self) -> UNIXFileType:
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
        return os.path.relpath(self._path, os.path.sep)

    def _create_temporary_path(self, *, root_path: str) -> str:
        """Generate and create temporary path."""
        temporary_path = os.path.join(
            root_path,
            self.PREFIX_RESTORE_FILESYSTEM_OBJECT
            + "tmp."
            + os.path.basename(self.filesystem_path)
            + "-"
            + generate_random_string(8),
        )

        os.mkdir(temporary_path)
        os.chmod(temporary_path, 0o700)

        return temporary_path

    @cached_property
    def old_path(self) -> str:
        """Set old path."""

        # Add dot prefix to prevent access, and add random string in case filesystem
        # object without random string already exists

        return os.path.join(
            Path(self.filesystem_path).parent,
            self.PREFIX_RESTORE_FILESYSTEM_OBJECT
            + "old."
            + os.path.basename(self.filesystem_path)
            + "-"
            + generate_random_string(8),
        )

    @cached_property
    def new_path(self) -> str:
        """Set new path."""

        # Add dot prefix to prevent access, and add random string in case filesystem
        # object without random string already exists

        return os.path.join(
            Path(self.filesystem_path).parent,
            self.PREFIX_RESTORE_FILESYSTEM_OBJECT
            + "new."
            + os.path.basename(self.filesystem_path)
            + "-"
            + generate_random_string(8),
        )

    @property
    def strip_components(self) -> int:
        """Set amount of components to strip."""
        return len(Path(self.archive_path).parts) - 1

    # @archive_restoration_check_repository_not_locked  # Function is only for internal use. Caller should already have this decorator.
    def _extract(self) -> None:
        """Extract archive path to temporary path."""
        self.archive.extract(
            destination_path=self.temporary_path,
            restore_paths=[self.archive_path],
            strip_components=self.strip_components,
        )

    @archive_restoration_check_repository_not_locked
    def replace(self) -> None:
        """Replace object on local filesystem with object from archive.

        This is a nearly atomic process. I.e. there is almost no downtime when
        replacing.
        """

        # Extract archive. The filesystem path remains untouched until this is
        # completed. This ensures that the filesystem is not left in a broken
        # state if the extraction fails.

        self._extract()

        # Move the extracted filesystem objects to the new path. As these may be
        # on different filesystems, the move could take a while. We restore to the
        # new path instead of to the filesystem path. If we restored to the filesystem
        # path, we would have to get the original filesystem object out of the way,
        # leaving the filesystem structure in a 'broken' state, while the move could
        # take a while. In order to prevent downtime, we restore to this temporary
        # new directory first.

        shutil.move(
            os.path.join(
                self.temporary_path, os.path.basename(self.archive_path)
            ),
            self.new_path,
        )

        # If the filesystem path already exists, move it out of the way so that
        # we can move the new path to it. This procedure is also followed for
        # regular files. Unlike non-empty directories, regular files can be
        # overwritten without having to ensure the filesystem object does not
        # exist at the path, unless the regular file is write-protected (e.g.
        # if it has permissions 0400).

        if os.path.lexists(self.filesystem_path):
            os.rename(self.filesystem_path, self.old_path)

        # Move the new path to the filesystem path. This completes the restore.

        os.rename(self.new_path, self.filesystem_path)

        # Remove the old path if it exists (it exists if the filesystem path
        # existed before doing the restore, see above).

        if os.path.lexists(self.old_path):
            if self.type_ == UNIXFileType.DIRECTORY:
                shutil.rmtree(self.old_path)

                return

            os.unlink(self.old_path)
