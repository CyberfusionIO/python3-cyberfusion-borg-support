from pathlib import Path
from typing import Dict, Generator, List, Optional

import pytest
from pytest_mock import MockerFixture

from cyberfusion.BorgSupport.archives import Archive
from cyberfusion.BorgSupport.borg_cli import BorgCommand
from cyberfusion.BorgSupport.exceptions import LoggedCommandFailedError
from cyberfusion.BorgSupport.operations import Operation
from cyberfusion.BorgSupport.repositories import Repository


NON_STRICT_RETURN_CODES = [100, 107]


@pytest.fixture
def progress_file(tmp_path: Path) -> str:
    path = tmp_path / "progress.log"

    path.touch()

    return str(path)


@pytest.mark.parametrize("return_code", NON_STRICT_RETURN_CODES)
def test_archive_create_non_strict_ignores_common_warnings(
    mocker: MockerFixture,
    repository_init: Generator[Repository, None, None],
    progress_file: str,
    return_code: int,
) -> None:
    def execute_side_effect(
        *,
        command: str,
        arguments: List[str],
        identity_file_path: Optional[str] = None,
        working_directory: Optional[str] = None,
        environment: Optional[Dict[str, str]] = None,
        run: bool = True,
    ) -> None:
        raise LoggedCommandFailedError(
            command=[BorgCommand.BORG_BIN, command],
            output_file_path=progress_file,
            return_code=return_code,
        )

    mocker.patch(
        "cyberfusion.BorgSupport.borg_cli.BorgLoggedCommand.execute",
        side_effect=execute_side_effect,
    )

    mocker.patch(
        "cyberfusion.BorgSupport.borg_cli.BorgLoggedCommand.file",
        new=mocker.PropertyMock(return_value=progress_file),
    )

    archive = Archive(repository=repository_init, name="test", comment="")

    result = archive.create(paths=["/tmp/x"], excludes=[], strict=False)

    assert isinstance(result, Operation)

    mocker.stopall()  # Unlock for teardown


def test_archive_create_non_strict_reraises_other_return_code(
    mocker: MockerFixture,
    repository_init: Generator[Repository, None, None],
    progress_file: str,
) -> None:
    def execute_side_effect(
        *,
        command: str,
        arguments: List[str],
        identity_file_path: Optional[str] = None,
        working_directory: Optional[str] = None,
        environment: Optional[Dict[str, str]] = None,
        run: bool = True,
    ) -> None:
        raise LoggedCommandFailedError(
            command=[BorgCommand.BORG_BIN, command],
            output_file_path=progress_file,
            return_code=2,
        )

    mocker.patch(
        "cyberfusion.BorgSupport.borg_cli.BorgLoggedCommand.execute",
        side_effect=execute_side_effect,
    )

    mocker.patch(
        "cyberfusion.BorgSupport.borg_cli.BorgLoggedCommand.file",
        new=mocker.PropertyMock(return_value=progress_file),
    )

    archive = Archive(repository=repository_init, name="test", comment="")

    with pytest.raises(LoggedCommandFailedError) as exc_info:
        archive.create(paths=["/tmp/x"], excludes=[], strict=False)

    assert exc_info.value.return_code == 2

    mocker.stopall()  # Unlock for teardown


@pytest.mark.parametrize("return_code", NON_STRICT_RETURN_CODES)
def test_archive_create_strict_reraises_swallowable_return_code(
    mocker: MockerFixture,
    repository_init: Generator[Repository, None, None],
    progress_file: str,
    return_code: int,
) -> None:
    """Test that strict propagates even an RC that would otherwise be swallowed."""

    def execute_side_effect(
        *,
        command: str,
        arguments: List[str],
        identity_file_path: Optional[str] = None,
        working_directory: Optional[str] = None,
        environment: Optional[Dict[str, str]] = None,
        run: bool = True,
    ) -> None:
        raise LoggedCommandFailedError(
            command=[BorgCommand.BORG_BIN, command],
            output_file_path=progress_file,
            return_code=return_code,
        )

    mocker.patch(
        "cyberfusion.BorgSupport.borg_cli.BorgLoggedCommand.execute",
        side_effect=execute_side_effect,
    )

    mocker.patch(
        "cyberfusion.BorgSupport.borg_cli.BorgLoggedCommand.file",
        new=mocker.PropertyMock(return_value=progress_file),
    )

    archive = Archive(repository=repository_init, name="test", comment="")

    with pytest.raises(LoggedCommandFailedError) as exc_info:
        archive.create(paths=["/tmp/x"], excludes=[], strict=True)

    assert exc_info.value.return_code == return_code

    mocker.stopall()  # Unlock for teardown
