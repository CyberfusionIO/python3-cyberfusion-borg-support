from typing import Generator

from pytest_mock import MockerFixture

from cyberfusion.BorgSupport import BorgCommand
from cyberfusion.BorgSupport.exceptions import RegularCommandFailedError
from cyberfusion.BorgSupport.repositories import Repository
from typing import Optional, Dict, List


def test_repository_cli_options(
    repository: Generator[Repository, None, None],
) -> None:
    assert repository._cli_options == {
        "identity_file_path": None,
    }


def test_repository_is_locked_without_msgid(
    mocker: MockerFixture, repository_init: Generator[Repository, None, None]
) -> None:
    """Test that lines without `msgid` are skipped."""

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
            raise RegularCommandFailedError(
                command=[
                    BorgCommand.BORG_BIN,
                    "with-lock",
                    "--log-json",
                    repository_init.path,
                    "/bin/true",
                ],
                stderr='{"type": "log_message", "time": 1770126671.9034498, "message": "Remote: Warning: Permanently added \'borg0-0.ha.cyberfusion.cloud\' (ED25519) to the list of known hosts.", "levelname": "WARNING", "name": "root"}',
                return_code=2,
            )

        return mocker.DEFAULT

    mocker.patch(
        "cyberfusion.BorgSupport.borg_cli.BorgRegularCommand.execute",
        side_effect=execute_side_effect,
    )

    repository_init.is_locked

    mocker.stopall()  # Unlock for teardown
