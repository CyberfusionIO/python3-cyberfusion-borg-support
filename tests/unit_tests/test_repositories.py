import os
import shutil
from typing import Dict, Generator, List, Optional
from unittest import mock

import pytest
from pytest_mock import MockerFixture  # type: ignore[attr-defined]

from cyberfusion.BorgSupport.archives import Archive
from cyberfusion.BorgSupport.borg_cli import BorgCommand
from cyberfusion.BorgSupport.exceptions import (
    RepositoryLockedError,
    RepositoryNotLocalError,
    RepositoryPathInvalidError,
)
from cyberfusion.BorgSupport.repositories import Repository
from cyberfusion.Common.Command import CommandNonZeroError


def test_repository_safe_cli_options(
    repository: Generator[Repository, None, None],
    passphrase_file: Generator[str, None, None],
) -> None:
    assert repository._safe_cli_options == {
        "environment": {"BORG_PASSCOMMAND": f"/bin/cat {passphrase_file}"},
        "identity_file_path": None,
    }


def test_repository_dangerous_cli_options(
    repository: Generator[Repository, None, None],
    passphrase_file: Generator[str, None, None],
) -> None:
    assert repository._dangerous_cli_options == {
        "environment": {
            "BORG_PASSCOMMAND": f"/bin/cat {passphrase_file}",
            "BORG_DELETE_I_KNOW_WHAT_I_AM_DOING": "YES",
        },
        "identity_file_path": None,
    }


def test_repository_attributes(
    repository: Generator[Repository, None, None],
    passphrase_file: Generator[str, None, None],
) -> None:
    assert repository._passphrase_file == passphrase_file
    assert repository.passcommand == f"/bin/cat {passphrase_file}"
    assert repository.identity_file_path is None


def test_repository_archives(
    repository_init: Generator[Repository, None, None],
    archives: Generator[List[Archive], None, None],
    workspace_directory: Generator[str, None, None],
) -> None:
    assert len(repository_init.archives) == 1

    assert archives[0].repository == repository_init
    assert archives[0]._name == "test"
    assert archives[0]._comment == "Free-form comment!"
    assert (
        archives[0].name
        == os.path.join(workspace_directory, "repository2") + "::test"
    )
    assert archives[0].comment == "Free-form comment!"


def test_repository_not_exists(
    repository: Generator[Repository, None, None]
) -> None:
    assert not repository.exists


def test_repository_exists(
    repository_init: Generator[Repository, None, None]
) -> None:
    assert repository_init.exists


def test_repository_size(
    repository_init: Generator[Repository, None, None]
) -> None:
    assert repository_init.size


def test_repository_not_locked(
    repository_init: Generator[Repository, None, None]
) -> None:
    assert not repository_init.is_locked


def test_repository_locked(
    repository_init: Generator[Repository, None, None]
) -> None:
    def execute_side_effect(
        *,
        command: Optional[str],
        arguments: Optional[List[str]] = None,
        json_format: bool = False,
        identity_file_path: Optional[str] = None,
        environment: Optional[Dict[str, str]] = None,
        run: bool = True,
        capture_stderr: bool = False,
    ) -> None:
        """Raise exception if command is expected. Call original method otherwise."""
        if command == "with-lock":
            raise CommandNonZeroError(
                command=[
                    BorgCommand.BORG_BIN,
                    "with-lock",
                    "--log-json",
                    repository_init.path,
                    "/bin/true",
                ],
                stdout=None,
                stderr='{"type": "log_message", "time": 1654268720.0201778, "message": "Failed to create/acquire the lock /Users/wedwards/repo/lock.exclusive (timeout).", "levelname": "ERROR", "name": "borg.archiver", "msgid": "LockTimeout"}',
                rc=2,
            )

        return mock.DEFAULT

    with mock.patch(
        "cyberfusion.BorgSupport.borg_cli.BorgRegularCommand.execute",
        side_effect=execute_side_effect,
    ):
        result = repository_init.is_locked

    assert result is True


def test_repository_not_locked_line_type(
    repository_init: Generator[Repository, None, None]
) -> None:
    """Test that repository is not marked as locked because of type in line."""

    def execute_side_effect(
        *,
        command: Optional[str],
        arguments: Optional[List[str]] = None,
        json_format: bool = False,
        identity_file_path: Optional[str] = None,
        environment: Optional[Dict[str, str]] = None,
        run: bool = True,
        capture_stderr: bool = False,
    ) -> None:
        """Raise exception if command is expected. Call original method otherwise."""
        if command == "with-lock":
            raise CommandNonZeroError(
                command=[
                    BorgCommand.BORG_BIN,
                    "with-lock",
                    "--log-json",
                    repository_init.path,
                    "/bin/true",
                ],
                stdout=None,
                stderr='{"type": "progress_percent", "time": 1654268720.0201778, "message": "Failed to create/acquire the lock /Users/wedwards/repo/lock.exclusive (timeout).", "levelname": "ERROR", "name": "borg.archiver", "msgid": "LockTimeout"}',
                rc=2,
            )

        return mock.DEFAULT

    with mock.patch(
        "cyberfusion.BorgSupport.borg_cli.BorgRegularCommand.execute",
        side_effect=execute_side_effect,
    ):
        result = repository_init.is_locked

    assert result is False


def test_repository_not_locked_line_msgid(
    repository_init: Generator[Repository, None, None]
) -> None:
    """Test that repository is not marked as locked because of msgid in line."""

    def execute_side_effect(
        *,
        command: Optional[str],
        arguments: Optional[List[str]] = None,
        json_format: bool = False,
        identity_file_path: Optional[str] = None,
        environment: Optional[Dict[str, str]] = None,
        run: bool = True,
        capture_stderr: bool = False,
    ) -> None:
        """Raise exception if command is expected. Call original method otherwise."""
        if command == "with-lock":
            raise CommandNonZeroError(
                command=[
                    BorgCommand.BORG_BIN,
                    "with-lock",
                    "--log-json",
                    repository_init.path,
                    "/bin/true",
                ],
                stdout=None,
                stderr='{"type": "log_message", "time": 1654268720.0201778, "message": "Failed to create/acquire the lock /Users/wedwards/repo/lock.exclusive (timeout).", "levelname": "ERROR", "name": "borg.archiver", "msgid": "LockError"}',
                rc=2,
            )

        return mock.DEFAULT

    with mock.patch(
        "cyberfusion.BorgSupport.borg_cli.BorgRegularCommand.execute",
        side_effect=execute_side_effect,
    ):
        result = repository_init.is_locked

    assert result is False


def test_repository_remote_size(
    passphrase_file: Generator[str, None, None]
) -> None:
    repository = Repository(
        path="ssh://user@host:22/path/to/repo", passphrase_file=passphrase_file
    )

    with pytest.raises(RepositoryNotLocalError):
        repository.size


def test_repository_attributes_remote_without_scheme(
    passphrase_file: Generator[str, None, None],
) -> None:
    repository = Repository(
        path="user@host:/path/to/repo", passphrase_file=passphrase_file
    )

    with pytest.raises(RepositoryPathInvalidError):
        repository.path


def test_repository_attributes_remote_with_scheme(
    passphrase_file: Generator[str, None, None],
) -> None:
    repository = Repository(
        path="ssh://user@host:22/path/to/repo", passphrase_file=passphrase_file
    )

    assert repository.path == "ssh://user@host:22/path/to/repo"
    assert repository._is_remote


def test_repository_attributes_local(
    passphrase_file: Generator[str, None, None],
    workspace_directory: Generator[str, None, None],
) -> None:
    path = os.path.join(workspace_directory, "repository3")

    repository = Repository(path=path, passphrase_file=passphrase_file)

    assert repository.path == path
    assert not repository._is_remote


def test_repository_init_already_exists(
    repository_init: Generator[Repository, None, None]
) -> None:
    with pytest.raises(CommandNonZeroError):
        repository_init.create(encryption="keyfile-blake2")


def test_repository_init_locked(
    mocker: MockerFixture, repository_init: Generator[Repository, None, None]
) -> None:
    mocker.patch(
        "cyberfusion.BorgSupport.repositories.Repository.is_locked",
        return_value=True,
    )

    with pytest.raises(RepositoryLockedError):
        repository_init.create(encryption="keyfile-blake2")

    mocker.stopall()  # Unlock for teardown


def test_repository_check_locked(
    mocker: MockerFixture, repository_init: Generator[Repository, None, None]
) -> None:
    mocker.patch(
        "cyberfusion.BorgSupport.repositories.Repository.is_locked",
        return_value=True,
    )

    with pytest.raises(RepositoryLockedError):
        repository_init.check()

    mocker.stopall()  # Unlock for teardown


def test_repository_check_has_integrity(
    repository_init: Generator[Repository, None, None]
) -> None:
    assert repository_init.check()


def test_repository_check_has_no_integrity(
    repository_init: Generator[Repository, None, None]
) -> None:
    def execute_side_effect(
        *,
        command: Optional[str],
        arguments: Optional[List[str]] = None,
        json_format: bool = False,
        identity_file_path: Optional[str] = None,
        environment: Optional[Dict[str, str]] = None,
        run: bool = True,
        capture_stderr: bool = False,
    ) -> None:
        """Raise exception if command is expected. Call original method otherwise."""
        if command == "check":
            raise CommandNonZeroError(
                command=[BorgCommand.BORG_BIN, "check", repository_init.path],
                stdout=None,
                stderr=None,
                rc=2,
            )

        return mock.DEFAULT

    with mock.patch(
        "cyberfusion.BorgSupport.borg_cli.BorgRegularCommand.execute",
        side_effect=execute_side_effect,
    ):
        result = repository_init.check()

    assert result is False


def test_repository_prune_locked(
    mocker: MockerFixture, repository_init: Generator[Repository, None, None]
) -> None:
    mocker.patch(
        "cyberfusion.BorgSupport.repositories.Repository.is_locked",
        return_value=True,
    )

    with pytest.raises(RepositoryLockedError):
        repository_init.prune()

    mocker.stopall()  # Unlock for teardown


def test_repository_prune(
    repository_init: Generator[Repository, None, None]
) -> None:
    repository_init.prune(keep_hourly=1)
    repository_init.prune(keep_daily=1)
    repository_init.prune(keep_weekly=1)
    repository_init.prune(keep_monthly=1)
    repository_init.prune(keep_yearly=1)


def test_repository_delete_locked(
    mocker: MockerFixture, repository_init: Generator[Repository, None, None]
) -> None:
    mocker.patch(
        "cyberfusion.BorgSupport.repositories.Repository.is_locked",
        return_value=True,
    )

    with pytest.raises(RepositoryLockedError):
        repository_init.delete()

    mocker.stopall()  # Unlock for teardown


def test_repository_compact_locked(
    mocker: MockerFixture, repository_init: Generator[Repository, None, None]
) -> None:
    mocker.patch(
        "cyberfusion.BorgSupport.repositories.Repository.is_locked",
        return_value=True,
    )

    with pytest.raises(RepositoryLockedError):
        repository_init.compact()

    mocker.stopall()  # Unlock for teardown


def test_repository_compact(
    repository_init: Generator[Repository, None, None]
) -> None:
    repository_init.compact()
