"""Classes for managing archives."""

from typing import TYPE_CHECKING, List

from cyberfusion.BorgSupport import Operation
from cyberfusion.BorgSupport.borg_cli import BorgCommand, BorgLoggedCommand

if TYPE_CHECKING:  # pragma: no cover
    from cyberfusion.BorgSupport.repositories import Repository


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

    def create(self, *, paths: List[str]) -> Operation:
        """Create archive."""
        command = BorgLoggedCommand()
        command.execute(
            command=BorgCommand.SUBCOMMAND_CREATE,
            arguments=["--one-file-system", self.name] + paths,
            **self.repository._safe_cli_options,
        )

        return Operation(progress_file=command.file)

    def extract(
        self, *, destination_path: str, restore_paths: List[str]
    ) -> None:
        """Extract paths in archive to destination."""
        command = BorgLoggedCommand()
        command.execute(
            command=BorgCommand.SUBCOMMAND_EXTRACT,
            arguments=[self.name] + restore_paths,
            working_directory=destination_path,  # Borg extracts in working directory
            **self.repository._safe_cli_options,
        )

        return Operation(progress_file=command.file)
