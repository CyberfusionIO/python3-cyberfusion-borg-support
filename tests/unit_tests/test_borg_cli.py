import os
from copy import deepcopy
from typing import Generator

import pytest
from pytest_mock import MockerFixture  # type: ignore[attr-defined]

from cyberfusion.BorgSupport.borg_cli import (
    BorgCommand,
    BorgLoggedCommand,
    BorgRegularCommand,
    _get_rsh_argument,
    get_borg_bin,
    get_true_bin,
)
from cyberfusion.BorgSupport.repositories import Repository
from cyberfusion.Common.Command import CommandNonZeroError


def test_borg_bin_local(mocker: MockerFixture) -> None:
    def isfile_side_effect(path: str) -> bool:
        """Pretend that /usr/local/bin/borg and /usr/bin/borg both exist."""
        if path == "/usr/local/bin/borg":
            return True

        elif path == "/usr/bin/borg":
            return True

        return os.path.isfile(path)

    mocker.patch(
        "os.path.isfile", new=mocker.Mock(side_effect=isfile_side_effect)
    )

    assert get_borg_bin() == "/usr/local/bin/borg"


def test_borg_bin_system(mocker: MockerFixture) -> None:
    def isfile_side_effect(path: str) -> bool:
        """Pretend that /usr/local/bin/borg does not exist, and /usr/bin/borg exists."""
        if path == "/usr/local/bin/borg":
            return False

        elif path == "/usr/bin/borg":
            return True

        return os.path.isfile(path)

    mocker.patch(
        "os.path.isfile", new=mocker.Mock(side_effect=isfile_side_effect)
    )

    assert get_borg_bin() == "/usr/bin/borg"


def test_true_bin_system(mocker: MockerFixture) -> None:
    def isfile_side_effect(path: str) -> bool:
        """Pretend that /bin/true and /usr/bin/true both exist."""
        if path == "/bin/true":
            return True

        elif path == "/usr/bin/true":
            return True

        return os.path.isfile(path)

    mocker.patch(
        "os.path.isfile", new=mocker.Mock(side_effect=isfile_side_effect)
    )

    assert get_true_bin() == "/bin/true"


def test_true_bin_user(mocker: MockerFixture) -> None:
    def isfile_side_effect(path: str) -> bool:
        """Pretend that /bin/true does not exist, and /usr/bin/true exists."""
        if path == "/bin/true":
            return False

        elif path == "/usr/bin/true":
            return True

        return os.path.isfile(path)

    mocker.patch(
        "os.path.isfile", new=mocker.Mock(side_effect=isfile_side_effect)
    )

    assert get_true_bin() == "/usr/bin/true"


def test_get_rsh_argument() -> None:
    assert _get_rsh_argument("/tmp/test.key") == [
        "--rsh",
        "ssh -oBatchMode=yes -oStrictHostKeyChecking=no -i /tmp/test.key",
    ]


def test_borg_regular_command_identity_file_path(
    borg_regular_command: BorgRegularCommand,
) -> None:
    borg_regular_command.execute(
        run=False, command="info", identity_file_path="/tmp/test.key"
    )

    assert borg_regular_command.command == [
        BorgCommand.BORG_BIN,
        "info",
        "--rsh",
        "ssh -oBatchMode=yes -oStrictHostKeyChecking=no -i /tmp/test.key",
    ]


def test_borg_logged_command_identity_file_path(
    repository_init: Generator[Repository, None, None],
    borg_logged_command: BorgLoggedCommand,
    workspace_directory: Generator[str, None, None],
) -> None:
    # Remove identity_file_path from default _safe_cli_options, as we need to
    # override the value of None for this test

    _safe_cli_options = deepcopy(repository_init._safe_cli_options)
    del _safe_cli_options["identity_file_path"]

    borg_logged_command.execute(
        run=False,
        command="create",
        arguments=[
            os.path.join(workspace_directory, "repository2")
            + "::testarchivename",
            "/root",
        ],
        identity_file_path="/tmp/test.key",
        **_safe_cli_options,
    )

    assert borg_logged_command.command == [
        BorgCommand.BORG_BIN,
        "--progress",
        "--log-json",
        "create",
        "--rsh",
        "ssh -oBatchMode=yes -oStrictHostKeyChecking=no -i /tmp/test.key",
        os.path.join(workspace_directory, "repository2") + "::testarchivename",
        "/root",
    ]


def test_borg_regular_command_command_and_arguments(
    borg_regular_command: BorgRegularCommand,
) -> None:
    borg_regular_command.execute(
        run=False, command="info", arguments=["--test1=test1", "--test2=test2"]
    )

    assert borg_regular_command.command == [
        BorgCommand.BORG_BIN,
        "info",
        "--test1=test1",
        "--test2=test2",
    ]


def test_borg_logged_command_command_and_arguments(
    repository_init: Generator[Repository, None, None],
    borg_logged_command: BorgLoggedCommand,
    workspace_directory: Generator[str, None, None],
) -> None:
    borg_logged_command.execute(
        run=False,
        command="create",
        arguments=[
            os.path.join(workspace_directory, "repository2")
            + "::testarchivename",
            "/root",
        ],
        **repository_init._safe_cli_options,
    )

    assert borg_logged_command.command == [
        BorgCommand.BORG_BIN,
        "--progress",
        "--log-json",
        "create",
        os.path.join(workspace_directory, "repository2") + "::testarchivename",
        "/root",
    ]


def test_borg_regular_command_json(
    borg_regular_command: BorgRegularCommand,
) -> None:
    borg_regular_command.execute(run=False, command="info", json_format=True)

    assert borg_regular_command.command == [
        BorgCommand.BORG_BIN,
        "info",
        "--json",
    ]
