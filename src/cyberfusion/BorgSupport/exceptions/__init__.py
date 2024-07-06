"""Exceptions."""

from dataclasses import dataclass
from typing import List


class RepositoryLockedError(Exception):
    """Repository is locked."""

    pass


class RepositoryPathInvalidError(Exception):
    """Repository path is not supported by this library."""

    pass


class OperationLineNotImplementedError(Exception):
    """Line in operation progress file is not supported by this library."""

    pass


@dataclass
class ExecutableNotFoundError(Exception):
    """Executable was not found."""

    name: str


@dataclass
class CommandFailedError(Exception):
    """Command failed."""

    return_code: int
    command: List[str]


@dataclass
class LoggedCommandFailedError(CommandFailedError):
    """Logged command failed."""

    output_file_path: str

    def __str__(self) -> str:
        """Get string representation."""
        return f"Command '{self.command}' failed with RC {self.return_code}. Output was logged to {self.output_file_path}"


@dataclass
class RegularCommandFailedError(CommandFailedError):
    """Regular command failed."""

    stderr: str

    def __str__(self) -> str:
        """Get string representation."""
        return f"Command '{self.command}' failed with RC {self.return_code}. Stderr:\n\n{self.stderr}"


class PathNotExistsError(Exception):
    """Path doesn't exist."""

    pass


class ArchiveNotExistsError(Exception):
    """Archive doesn't exist."""

    pass
