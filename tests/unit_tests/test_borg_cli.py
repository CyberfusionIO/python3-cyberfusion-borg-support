import os
from copy import deepcopy

import pytest

from cyberfusion.BorgSupport.borg_cli import (
    BorgLoggedCommand,
    BorgRegularCommand,
)
from cyberfusion.BorgSupport.repositories import Repository


def test_borg_regular_command_attributes(
    borg_regular_command: BorgRegularCommand,
) -> None:
    borg_regular_command.execute(command=None, arguments=["--version"])

    assert borg_regular_command.stdout.startswith("borg ")
    assert borg_regular_command.rc == 0


def test_borg_logged_command_attributes(
    repository_init: Repository, borg_logged_command: BorgLoggedCommand
) -> None:
    borg_logged_command.execute(
        command="create",
        arguments=["/tmp/anotherbackup::testarchivename", "/root"],
        **repository_init._safe_cli_options,
    )

    assert borg_logged_command.file
    assert borg_logged_command.rc == 0


def test_borg_regular_command_command_and_arguments(
    borg_regular_command: BorgRegularCommand,
) -> None:
    borg_regular_command.execute(
        run=False, command="info", arguments=["--test1=test1", "--test2=test2"]
    )

    assert borg_regular_command.command == [
        "/usr/bin/borg",
        "info",
        "--test1=test1",
        "--test2=test2",
    ]


def test_borg_logged_command_command_and_arguments(
    repository_init: Repository,
    borg_logged_command: BorgLoggedCommand,
) -> None:
    borg_logged_command.execute(
        run=False,
        command="create",
        arguments=["/tmp/anotherbackup::testarchivename", "/root"],
        **repository_init._safe_cli_options,
    )

    assert borg_logged_command.command == [
        "/usr/bin/borg",
        "--progress",
        "--log-json",
        "create",
        "/tmp/anotherbackup::testarchivename",
        "/root",
    ]


def test_borg_regular_command_json(
    borg_regular_command: BorgRegularCommand,
) -> None:
    borg_regular_command.execute(run=False, command="info", json_format=True)

    assert borg_regular_command.command == ["/usr/bin/borg", "info", "--json"]


def test_borg_regular_command_identity_file_path(
    borg_regular_command: BorgRegularCommand,
) -> None:
    borg_regular_command.execute(
        run=False, command="info", identity_file_path="/tmp/test.key"
    )

    assert borg_regular_command.command == [
        "/usr/bin/borg",
        "info",
        "--rsh='ssh -oBatchMode=yes -oStrictHostKeyChecking=no -i /tmp/test.key'",
    ]


def test_borg_logged_command_identity_file_path(
    repository_init: Repository,
    borg_logged_command: BorgLoggedCommand,
) -> None:
    # Remove identity_file_path from default _safe_cli_options, as we need to
    # override the value of None for this test

    _safe_cli_options = deepcopy(repository_init._safe_cli_options)
    del _safe_cli_options["identity_file_path"]

    borg_logged_command.execute(
        run=False,
        command="create",
        arguments=["/tmp/anotherbackup::testarchivename", "/root"],
        identity_file_path="/tmp/test.key",
        **_safe_cli_options,
    )

    assert borg_logged_command.command == [
        "/usr/bin/borg",
        "--progress",
        "--log-json",
        "create",
        "--rsh='ssh -oBatchMode=yes -oStrictHostKeyChecking=no -i /tmp/test.key'",
        "/tmp/anotherbackup::testarchivename",
        "/root",
    ]
