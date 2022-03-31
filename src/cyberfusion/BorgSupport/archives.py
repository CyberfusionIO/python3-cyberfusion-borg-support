"""Classes for managing archives."""

import json
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from cyberfusion.BorgSupport.borg_cli import (
    BorgCommand,
    BorgLoggedCommand,
    BorgRegularCommand,
)
from cyberfusion.BorgSupport.operations import Operation

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

    def __init__(self, *, repository: "Repository", name: str) -> None:
        """Set variables."""
        self.repository = repository
        self._name = name

    @property
    def name(self) -> str:
        """Get archive name with repository path.

        Borg needs this format to identify the repository and archive.
        """
        return self.repository.path + "::" + self._name

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

    def create(self, *, paths: List[str], excludes: List[str]) -> Operation:
        """Create archive.

        Excludes use the default pattern for --exclude, Fnmatch. See https://borgbackup.readthedocs.io/en/stable/usage/help.html
        """

        # Construct arguments

        arguments = ["--one-file-system"]

        for exclude in excludes:
            arguments.append(f"--exclude={exclude}")

        arguments.append(self.name)
        arguments.extend(paths)

        # Execute command

        command = BorgLoggedCommand()
        command.execute(
            command=BorgCommand.SUBCOMMAND_CREATE,
            arguments=arguments,
            **self.repository._safe_cli_options,
        )

        return Operation(progress_file=command.file)

    def extract(
        self, *, destination_path: str, restore_paths: List[str]
    ) -> None:
        """Extract paths in archive to destination."""

        # Construct arguments

        arguments = [self.name]
        arguments.extend(restore_paths)

        # Execute command

        command = BorgLoggedCommand()
        command.execute(
            command=BorgCommand.SUBCOMMAND_EXTRACT,
            arguments=arguments,
            working_directory=destination_path,  # Borg extracts in working directory
            **self.repository._safe_cli_options,
        )

        return Operation(progress_file=command.file)
