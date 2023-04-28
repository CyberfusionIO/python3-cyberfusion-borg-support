import os
import subprocess
from typing import Dict, Generator, List, Optional

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
    assert len(repository_init.archives()) == 1

    assert archives[0].repository == repository_init
    assert archives[0]._name == "test"
    assert archives[0]._comment == "Free-form comment!"
    assert (
        archives[0].name
        == os.path.join(workspace_directory, "repository2") + "::test"
    )
    assert archives[0].comment == "Free-form comment!"


def test_repository_not_exists_directory_exists(
    repository: Generator[Repository, None, None]
) -> None:
    os.mkdir(repository.path)

    assert not repository.exists


def test_repository_not_exists_directory_not_exists(
    repository: Generator[Repository, None, None]
) -> None:
    assert not repository.exists


def test_repository_exists(
    repository_init: Generator[Repository, None, None]
) -> None:
    assert repository_init.exists


def test_repository_exists_failure(
    mocker: MockerFixture, repository_init: Generator[Repository, None, None]
) -> None:
    """Test that original exception is raised when self.exists can't get archives list due to error."""

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
        if command == "list":
            raise subprocess.CalledProcessError(
                cmd=[
                    BorgCommand.BORG_BIN,
                    "list",
                    repository_init.path,
                ],
                stderr="Something went wrong",
                returncode=2,
            )

        return mocker.DEFAULT

    mocker.patch(
        "cyberfusion.BorgSupport.borg_cli.BorgRegularCommand.execute",
        side_effect=execute_side_effect,
    )

    with pytest.raises(subprocess.CalledProcessError):
        repository_init.exists

    mocker.stopall()  # Unlock for teardown


def test_repository_exists_locked(
    mocker: MockerFixture, repository_init: Generator[Repository, None, None]
) -> None:
    """Test that no exception is raised when self.exists can't get archives due to lock."""

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
        if command == "list":
            raise subprocess.CalledProcessError(
                cmd=[
                    BorgCommand.BORG_BIN,
                    "list",
                    repository_init.path,
                ],
                stderr="Failed to create/acquire the lock /Users/williamedwards/borg/test/lock.exclusive (timeout).",
                returncode=2,
            )

        return mocker.DEFAULT

    mocker.patch(
        "cyberfusion.BorgSupport.borg_cli.BorgRegularCommand.execute",
        side_effect=execute_side_effect,
    )

    assert repository_init.exists

    mocker.stopall()  # Unlock for teardown


def test_repository_size(
    repository_init: Generator[Repository, None, None]
) -> None:
    assert repository_init.size


def test_repository_not_locked(
    repository_init: Generator[Repository, None, None]
) -> None:
    assert not repository_init.is_locked


def test_repository_not_exists_create_if_not_exists(
    mocker: MockerFixture,
    passphrase_file: Generator[str, None, None],
    workspace_directory: Generator[str, None, None],
) -> None:
    """Test that if repository does not exist and 'create_if_not_exists' is true, repository is created."""
    path = os.path.join(workspace_directory, "repository3")

    spy_create = mocker.spy(Repository, "create")

    repository = Repository(
        path=path,
        passphrase_file=passphrase_file,
        create_if_not_exists=True,
    )

    spy_create.assert_called_once()
    assert repository.exists


def test_repository_not_exists_not_create_if_not_exists(
    mocker: MockerFixture,
    passphrase_file: Generator[str, None, None],
    workspace_directory: Generator[str, None, None],
) -> None:
    """Test that if repository does not exist and 'create_if_not_exists' is false, repository is not created."""
    path = os.path.join(workspace_directory, "repository3")

    spy_create = mocker.spy(Repository, "create")

    repository = Repository(
        path=path,
        passphrase_file=passphrase_file,
        create_if_not_exists=False,
    )

    assert not spy_create.called
    assert not repository.exists


def test_repository_exists_not_create_if_not_exists(
    mocker: MockerFixture, repository_init: Generator[Repository, None, None]
) -> None:
    """Test that if repository exists and 'create_if_not_exists' is false, repository is not created."""
    spy_create = mocker.spy(Repository, "create")

    repository = Repository(
        path=repository_init._path,
        passphrase_file=repository_init._passphrase_file,
        identity_file_path=repository_init.identity_file_path,
        create_if_not_exists=False,
    )

    assert not spy_create.called
    assert repository.exists


def test_repository_exists_create_if_not_exists(
    mocker: MockerFixture, repository_init: Generator[Repository, None, None]
) -> None:
    """Test that if repository exists and 'create_if_not_exists' is true, repository is not created."""
    spy_create = mocker.spy(Repository, "create")

    repository = Repository(
        path=repository_init._path,
        passphrase_file=repository_init._passphrase_file,
        identity_file_path=repository_init.identity_file_path,
        create_if_not_exists=True,
    )

    assert not spy_create.called
    assert repository.exists


def test_repository_locked(
    mocker: MockerFixture, repository_init: Generator[Repository, None, None]
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
            raise subprocess.CalledProcessError(
                cmd=[
                    BorgCommand.BORG_BIN,
                    "with-lock",
                    "--log-json",
                    repository_init.path,
                    "/bin/true",
                ],
                stderr='{"type": "log_message", "time": 1654268720.0201778, "message": "Failed to create/acquire the lock /Users/wedwards/repo/lock.exclusive (timeout).", "levelname": "ERROR", "name": "borg.archiver", "msgid": "LockTimeout"}',
                returncode=2,
            )

        return mocker.DEFAULT

    mocker.patch(
        "cyberfusion.BorgSupport.borg_cli.BorgRegularCommand.execute",
        side_effect=execute_side_effect,
    )

    result = repository_init.is_locked

    assert result is True

    mocker.stopall()  # Unlock for teardown


def test_repository_not_locked_line_type(
    mocker: MockerFixture, repository_init: Generator[Repository, None, None]
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
            raise subprocess.CalledProcessError(
                cmd=[
                    BorgCommand.BORG_BIN,
                    "with-lock",
                    "--log-json",
                    repository_init.path,
                    "/bin/true",
                ],
                stderr='{"type": "progress_percent", "time": 1654268720.0201778, "message": "Failed to create/acquire the lock /Users/wedwards/repo/lock.exclusive (timeout).", "levelname": "ERROR", "name": "borg.archiver", "msgid": "LockTimeout"}',
                returncode=2,
            )

        return mocker.DEFAULT

    mocker.patch(
        "cyberfusion.BorgSupport.borg_cli.BorgRegularCommand.execute",
        side_effect=execute_side_effect,
    )

    result = repository_init.is_locked

    assert result is False

    mocker.stopall()  # Unlock for teardown


def test_repository_not_locked_line_msgid(
    mocker: MockerFixture, repository_init: Generator[Repository, None, None]
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
            raise subprocess.CalledProcessError(
                cmd=[
                    BorgCommand.BORG_BIN,
                    "with-lock",
                    "--log-json",
                    repository_init.path,
                    "/bin/true",
                ],
                stderr='{"type": "log_message", "time": 1654268720.0201778, "message": "Failed to create/acquire the lock /Users/wedwards/repo/lock.exclusive (timeout).", "levelname": "ERROR", "name": "borg.archiver", "msgid": "LockError"}',
                returncode=2,
            )

        return mocker.DEFAULT

    mocker.patch(
        "cyberfusion.BorgSupport.borg_cli.BorgRegularCommand.execute",
        side_effect=execute_side_effect,
    )

    result = repository_init.is_locked

    assert result is False

    mocker.stopall()  # Unlock for teardown


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
    with pytest.raises(subprocess.CalledProcessError):
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
    mocker: MockerFixture, repository_init: Generator[Repository, None, None]
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
            raise subprocess.CalledProcessError(
                cmd=[BorgCommand.BORG_BIN, "check", repository_init.path],
                stderr=None,
                returncode=2,
            )

        return mocker.DEFAULT

    mocker.patch(
        "cyberfusion.BorgSupport.borg_cli.BorgLoggedCommand.execute",
        side_effect=execute_side_effect,
    )

    result = repository_init.check()

    assert result is False

    mocker.stopall()  # Unlock for teardown


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
    repository_init: Generator[Repository, None, None],
    dummy_files: Generator[None, None, None],
    workspace_directory: Generator[str, None, None],
) -> None:
    Archive(
        repository=repository_init,
        name="prunetest1",
        comment="Free-form comment!",
    ).create(
        paths=[
            os.path.join(workspace_directory, "backmeupdir1")
        ],  # Created by dummy_files fixture
        excludes=[],
    )

    Archive(
        repository=repository_init,
        name="prunetest2",
        comment="Free-form comment!",
    ).create(
        paths=[
            os.path.join(workspace_directory, "backmeupdir1")
        ],  # Created by dummy_files fixture
        excludes=[],
    )

    Archive(
        repository=repository_init,
        name="prunetest3",
        comment="Free-form comment!",
    ).create(
        paths=[
            os.path.join(workspace_directory, "backmeupdir1")
        ],  # Created by dummy_files fixture
        excludes=[],
    )

    assert all(
        a._name in ["prunetest1", "prunetest2", "prunetest3"]
        for a in repository_init.archives()
    )

    assert repository_init.prune(keep_last=1) == ["prunetest1", "prunetest2"]

    assert all(
        a._name not in ["prunetest1", "prunetest2"]
        for a in repository_init.archives()
    )
    assert all(a._name in ["prunetest3"] for a in repository_init.archives())


def test_repository_prune_keep_last(
    repository_init: Generator[Repository, None, None]
) -> None:
    repository_init.prune(keep_last=1)


def test_repository_prune_keep_hourly(
    repository_init: Generator[Repository, None, None]
) -> None:
    repository_init.prune(keep_hourly=1)


def test_repository_prune_keep_daily(
    repository_init: Generator[Repository, None, None]
) -> None:
    repository_init.prune(keep_daily=1)


def test_repository_prune_keep_weekly(
    repository_init: Generator[Repository, None, None]
) -> None:
    repository_init.prune(keep_weekly=1)


def test_repository_prune_keep_monthly(
    repository_init: Generator[Repository, None, None]
) -> None:
    repository_init.prune(keep_monthly=1)


def test_repository_prune_keep_yearly(
    repository_init: Generator[Repository, None, None]
) -> None:
    repository_init.prune(keep_yearly=1)


def test_repository_prune_compacted_from_120(
    mocker: MockerFixture, repository_init: Generator[Repository, None, None]
) -> None:
    """Test that compact was called with Borg version >= 1.2.0."""
    mocker.patch(
        "cyberfusion.BorgSupport.Borg.version",
        new=mocker.PropertyMock(return_value=(1, 2, 1)),
    )

    spy_compact = mocker.spy(repository_init, "compact")

    repository_init.prune(keep_yearly=1)

    spy_compact.assert_called_once()


def test_repository_prune_not_compacted_before_120(
    mocker: MockerFixture, repository_init: Generator[Repository, None, None]
) -> None:
    """Test that compact was not called with Borg version < 1.2.0."""
    mocker.patch(
        "cyberfusion.BorgSupport.Borg.version",
        new=mocker.PropertyMock(return_value=(1, 1, 8)),
    )

    spy_compact = mocker.spy(repository_init, "compact")

    repository_init.prune(keep_yearly=1)

    spy_compact.assert_not_called()


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
