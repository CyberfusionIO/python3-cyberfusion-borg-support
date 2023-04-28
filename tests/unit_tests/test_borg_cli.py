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
)
from cyberfusion.BorgSupport.repositories import Repository


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
