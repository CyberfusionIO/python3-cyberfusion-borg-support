"""Classes for managing repositories."""

from enum import Enum
from typing import Dict, List, Optional, Union

from cyberfusion.BorgSupport.archives import Archive
from cyberfusion.BorgSupport.borg_cli import BorgCommand, BorgRegularCommand
from cyberfusion.Common.Command import CommandNonZeroError
from cyberfusion.Common.Filesystem import get_directory_size


class BorgRepositoryEncryptionName(Enum):
    """Repository encryption names."""

    KEYFILE_BLAKE2 = "keyfile-blake2"


class Repository:
    """Abstraction of Borg repository."""

    def __init__(
        self,
        *,
        path: str,
        passphrase: str,
        identity_file_path: Optional[str] = None,
    ) -> None:
        """Set variables."""
        self.path = path
        self.passphrase = passphrase
        self.identity_file_path = identity_file_path

    @property
    def _safe_cli_options(
        self,
    ) -> Dict[str, Union[Optional[str], Dict[str, str]]]:
        """Get safe CLI options for Borg command."""
        return {
            "environment": {"BORG_PASSPHRASE": self.passphrase},
            "identity_file_path": self.identity_file_path,
        }

    @property
    def _dangerous_cli_options(
        self,
    ) -> Dict[str, Union[Optional[str], Dict[str, str]]]:
        """Get dangerous CLI options for Borg command.

        These options are dangerous because it contains an automatic answer for
        delete.
        """
        return {
            "environment": {
                "BORG_PASSPHRASE": self.passphrase,
                "BORG_DELETE_I_KNOW_WHAT_I_AM_DOING": "YES",
            },
            "identity_file_path": self.identity_file_path,
        }

    def create(self, *, encryption: BorgRepositoryEncryptionName) -> None:
        """Create repository."""

        # Construct arguments

        arguments = [f"--encryption={encryption}", self.path]

        # Execute command

        BorgRegularCommand().execute(
            command=BorgCommand.SUBCOMMAND_INIT,
            arguments=arguments,
            **self._safe_cli_options,
        )

    def delete(self) -> None:
        """Delete repository."""

        # Construct arguments

        arguments = [self.path]

        # Execute command

        BorgRegularCommand().execute(
            command=BorgCommand.SUBCOMMAND_DELETE,
            arguments=arguments,
            **self._dangerous_cli_options,
        )

    @property
    def exists(self) -> bool:
        """Determine if repository exists.

        Borg does not provide a more neat way of checking this than below. It
        does not matter if the repository actually has archives. Inspired by
        https://github.com/borgbackup/borg/issues/271#issuecomment-378091437
        """
        try:
            self.archives
        except CommandNonZeroError:
            return False

        return True

    @property
    def size(self) -> int:
        """Get size of repository in bytes.

        This method calculates the size of the repository directory on disk.
        Therefore, it must be run on a machine that has filesystem access to
        the repository directory. This is usually only the Borg server.

        More information: https://github.com/borgbackup/borg/discussions/6509
        """
        return get_directory_size(self.path)

    @property
    def archives(self) -> List[Archive]:
        """Get names of archives in repository."""
        results = []

        # Construct arguments

        arguments = [self.path]

        # Execute command

        command = BorgRegularCommand()
        command.execute(
            command=BorgCommand.SUBCOMMAND_LIST,
            arguments=arguments,
            json_format=True,
            **self._safe_cli_options,
        )

        for archive in command.stdout["archives"]:
            results.append(Archive(repository=self, name=archive["name"]))

        return results

    def check(self) -> bool:
        """Check repository.

        Returns False in case issues were found.
        """

        # Construct arguments

        arguments = [self.path]

        # Execute command

        try:
            BorgRegularCommand().execute(
                command=BorgCommand.SUBCOMMAND_CHECK,
                arguments=arguments,
                **self._safe_cli_options,
            )
        except CommandNonZeroError:
            return False

        return True

    def prune(
        self,
        *,
        keep_hourly: Optional[int] = None,
        keep_daily: Optional[int] = None,
        keep_weekly: Optional[int] = None,
        keep_monthly: Optional[int] = None,
        keep_yearly: Optional[int] = None,
    ) -> None:
        """Prune repository archives."""

        # Construct arguments

        arguments = []

        if keep_hourly:
            arguments.append(f"--keep-hourly={keep_hourly}")

        if keep_daily:
            arguments.append(f"--keep-daily={keep_daily}")

        if keep_weekly:
            arguments.append(f"--keep-weekly={keep_weekly}")

        if keep_monthly:
            arguments.append(f"--keep-monthly={keep_monthly}")

        if keep_yearly:
            arguments.append(f"--keep-yearly={keep_yearly}")

        arguments.append(self.path)

        # Execute command

        BorgRegularCommand().execute(
            command=BorgCommand.SUBCOMMAND_PRUNE,
            arguments=arguments,
            **self._safe_cli_options,
        )
