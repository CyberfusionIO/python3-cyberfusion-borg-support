"""Classes for managing repositories."""

import json
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
from urllib.parse import urlparse

from cyberfusion.BorgSupport import Borg, PassphraseFile
from cyberfusion.BorgSupport.archives import Archive
from cyberfusion.BorgSupport.borg_cli import (
    BorgCommand,
    BorgLoggedCommand,
    BorgRegularCommand,
)
from cyberfusion.BorgSupport.exceptions import (
    ArchiveNotExistsError,
    LoggedCommandFailedError,
    RegularCommandFailedError,
    RepositoryLockedError,
    RepositoryPathInvalidError,
)
from cyberfusion.BorgSupport.operations import JSONLineType, MessageID

SCHEME_SSH = "ssh"
DEFAULT_PORT_SSH = 22

CHARACTER_AT = "@"


F = TypeVar("F", bound=Callable[..., Any])


def check_repository_not_locked(f: F) -> Any:
    """Check that repository is not locked."""

    def wrapper(self: Any, *args: tuple, **kwargs: dict) -> Any:
        if self.is_locked:
            raise RepositoryLockedError

        return f(self, *args, **kwargs)

    return wrapper


def compact_repository(f: F) -> Any:
    """Run repository compact."""

    def wrapper(self: Any, *args: tuple, **kwargs: dict) -> Any:
        result = f(self, *args, **kwargs)

        if Borg().version >= (1, 2, 0):
            self.compact()

        return result

    return wrapper


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
        create_if_not_exists: bool = False,
    ) -> None:
        """Set variables.

        Set 'identity_file_path' only when the repository is remote.

        The specified identity file may not be protected by a passphrase. If the
        private SSH key leaks, the attacker does NOT have access to the repository,
        as they also need the passphrase. The remote SSH server should use `borg
        serve` so that an attacker would not have regular shell access either.

        If 'create_if_not_exists' is true, Borg repository will be created if
        it does not exist yet. The encryption 'KEYFILE_BLAKE2' will be used. Note
        that using this option causes a slight delay, as it checks whether the
        repository exists or not.
        """
        self._path = path
        self.passphrase = passphrase
        self.identity_file_path = identity_file_path

        if create_if_not_exists:
            if not self.exists:
                self.create(
                    encryption=BorgRepositoryEncryptionName.KEYFILE_BLAKE2.value
                )

    @property
    def path(self) -> str:
        """Get repository path.

        Path can be one of two things:

        - Local: directory on the local filesystem
        - Remote: URI that starts with 'ssh://'

        More information: https://borgbackup.readthedocs.io/en/stable/usage/general.html#repository-urls
        """

        # Borg also supports a scheme-less and portless URI, which defaults to
        # 'ssh://' on port 22. Such a URI is not allowed because it makes it
        # harder to detect if we're dealing with a local or remote repository.
        # Clients of this library may use the constants Repository.SCHEME_SSH
        # and Repository.DEFAULT_PORT_SSH to create a valid URI.
        #
        # When the URI contains '@', but no scheme, this is a scheme-less and
        # portless URI.
        # E.g.: 'user@host:/path/to/repo' -> 'ssh://user@host:port/path/to/repo'

        if CHARACTER_AT in self._path and not urlparse(self._path).scheme:
            raise RepositoryPathInvalidError

        return self._path

    @property
    def _is_remote(self) -> bool:
        """Get if repository is remote."""
        return urlparse(self.path).scheme == SCHEME_SSH

    @property
    def _cli_options(
        self,
    ) -> Dict[str, Union[Optional[str], Dict[str, str]]]:
        """Get CLI options for Borg command."""
        return {
            "identity_file_path": self.identity_file_path,
        }

    @check_repository_not_locked
    def create(self, *, encryption: BorgRepositoryEncryptionName) -> None:
        """Create repository."""

        # Construct arguments

        arguments = [f"--encryption={encryption}", self.path]

        # Execute command

        with PassphraseFile(self.passphrase) as environment:
            BorgRegularCommand().execute(
                command=BorgCommand.SUBCOMMAND_INIT,
                arguments=arguments,
                **self._cli_options,
                environment=environment,
            )

    @check_repository_not_locked
    def delete(self) -> None:
        """Delete repository."""

        # Construct arguments

        arguments = [self.path]

        # Execute command

        with PassphraseFile(self.passphrase) as environment:
            BorgRegularCommand().execute(
                command=BorgCommand.SUBCOMMAND_DELETE,
                arguments=arguments,
                **self._cli_options,
                environment=environment
                | {"BORG_DELETE_I_KNOW_WHAT_I_AM_DOING": "YES"},
            )

    @property
    def exists(self) -> bool:
        """Determine if repository exists.

        Borg does not provide a neat way of checking whether a repository exists.
        Therefore, we try getting archives. Inspired by:
        https://github.com/borgbackup/borg/issues/271#issuecomment-378091437
        """
        MESSAGE_FAILED_ACQUIRE_LOCK = "Failed to create/acquire the lock"

        try:
            with PassphraseFile(self.passphrase) as environment:
                BorgRegularCommand().execute(
                    command=BorgCommand.SUBCOMMAND_LIST,
                    arguments=[self.path],
                    capture_stderr=True,
                    **self._cli_options,
                    environment=environment,
                )
        except RegularCommandFailedError as e:
            lines = e.stderr.splitlines()

            # Directory does not exist

            if f"Repository {self.path} does not exist." in lines:
                return False

            # Directory exists, but does not contain repository

            if (
                f"{self.path} is not a valid repository. Check repo config."
                in lines
            ):
                return False

            # Repository exists, but is locked

            if any(
                line.startswith(MESSAGE_FAILED_ACQUIRE_LOCK) for line in lines
            ):
                return True

            # Unexpected error occurred

            raise

        return True

    @property
    def is_locked(self) -> bool:
        """Get if repository is locked by Borg.

        Borg does not provide a more neat way of checking this than below.
        """

        # Construct arguments

        arguments = ["--log-json", self.path, BorgCommand.TRUE_BIN]

        # Execute command

        command = BorgRegularCommand()

        try:
            with PassphraseFile(self.passphrase) as environment:
                command.execute(
                    command=BorgCommand.SUBCOMMAND_WITH_LOCK,
                    arguments=arguments,
                    capture_stderr=True,
                    **self._cli_options,
                    environment=environment,
                )
        except RegularCommandFailedError as e:
            # When RC is not 0, Borg will most likely have logged something. If
            # any of these log lines say that the command failed because there
            # was a lock, return False.

            for line in e.stderr.splitlines():
                line = json.loads(line)

                if line["type"] != JSONLineType.LOG_MESSAGE.value:
                    continue

                if line["msgid"] != MessageID.LOCK_TIMEOUT.value:
                    continue

                return True

        # RC is 0, so there was no lock

        return False

    def get_archive(self, name: str) -> Archive:
        """Get archive by name."""
        for archive in self.archives():
            if archive.name != name:
                continue

            return archive

        raise ArchiveNotExistsError

    @check_repository_not_locked
    def archives(self) -> List[Archive]:
        """Get archives in repository."""
        results = []

        # Construct arguments

        arguments = [self.path, "--format='{comment}'"]

        # Execute command

        command = BorgRegularCommand()

        with PassphraseFile(self.passphrase) as environment:
            command.execute(
                command=BorgCommand.SUBCOMMAND_LIST,
                arguments=arguments,
                json_format=True,
                **self._cli_options,
                environment=environment,
            )

        for archive in command.stdout["archives"]:
            results.append(
                Archive(
                    repository=self,
                    name=archive["name"],
                    comment=archive["comment"],
                )
            )

        return results

    @check_repository_not_locked
    def check(self) -> bool:
        """Check repository.

        Returns False in case issues were found.
        """

        # Construct arguments

        arguments = [self.path]

        # Execute command

        try:
            with PassphraseFile(self.passphrase) as environment:
                BorgLoggedCommand().execute(
                    command=BorgCommand.SUBCOMMAND_CHECK,
                    arguments=arguments,
                    **self._cli_options,
                    environment=environment,
                )
        except LoggedCommandFailedError:
            return False

        return True

    @check_repository_not_locked
    @compact_repository
    def prune(
        self,
        *,
        keep_last: Optional[int] = None,
        keep_hourly: Optional[int] = None,
        keep_daily: Optional[int] = None,
        keep_weekly: Optional[int] = None,
        keep_monthly: Optional[int] = None,
        keep_yearly: Optional[int] = None,
    ) -> List[str]:
        """Prune repository archives."""
        pruned_archives_names = []

        # Get archives before prune

        before_archives_names = [a.name for a in self.archives()]

        # Construct arguments

        arguments = []

        if keep_last:
            arguments.append(f"--keep-last={keep_last}")

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

        with PassphraseFile(self.passphrase) as environment:
            BorgRegularCommand().execute(
                command=BorgCommand.SUBCOMMAND_PRUNE,
                arguments=arguments,
                **self._cli_options,
                environment=environment,
            )

        # Get archives after prune

        after_archives_names = [a.name for a in self.archives()]

        # Get removed archives (in before list, not in after list)
        #
        # Not possible to get neatly, see: https://github.com/borgbackup/borg/discussions/7021

        for archive_name in before_archives_names:
            if archive_name in after_archives_names:
                continue

            pruned_archives_names.append(archive_name)

        return pruned_archives_names

    @check_repository_not_locked
    def compact(self) -> None:
        """Compact repository.

        Run after deleting archives. See: https://borgbackup.readthedocs.io/en/stable/usage/notes.html#separate-compaction
        """

        # Construct arguments

        arguments = [self.path]

        # Execute command

        with PassphraseFile(self.passphrase) as environment:
            BorgRegularCommand().execute(
                command=BorgCommand.SUBCOMMAND_COMPACT,
                arguments=arguments,
                **self._cli_options,
                environment=environment,
            )
