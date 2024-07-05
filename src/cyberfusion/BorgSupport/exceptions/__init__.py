"""Exceptions."""

from dataclasses import dataclass
from typing import List


class RepositoryLockedError(Exception):
    """Exception to raise if repository is locked."""

    pass


class RepositoryPathInvalidError(Exception):
    """Exception to raise if repository path is not supported by this library."""

    pass


class OperationLineNotImplementedError(Exception):
    """Exception to raise if line in operation progress file is not supported by this library."""

    pass


@dataclass
class ExecutableNotFoundError(Exception):
    """Exception to raise when executable was not found."""

    name: str


@dataclass
class CommandFailedError(Exception):
    """Exception to raise when command failed."""

    return_code: int
    command: List[str]


@dataclass
class LoggedCommandFailedError(CommandFailedError):
    """Exception to raise when logged command failed."""

    output_file_path: str

    def __str__(self) -> str:
        """Get string representation."""
        return f"Command '{self.command}' failed with RC {self.return_code}. Output was logged to {self.output_file_path}"


@dataclass
class RegularCommandFailedError(CommandFailedError):
    """Exception to raise when regular command failed."""

    stderr: str

    def __str__(self) -> str:
        """Get string representation."""
        return f"Command '{self.command}' failed with RC {self.return_code}. Stderr:\n\n{self.stderr}"


class PathNotExistsError(Exception):
    """Exception to raise when path doesn't exist."""

    pass
