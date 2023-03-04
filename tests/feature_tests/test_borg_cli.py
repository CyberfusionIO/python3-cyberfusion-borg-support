import os
from typing import Generator

import pytest

from cyberfusion.BorgSupport.borg_cli import (
    BorgLoggedCommand,
    BorgRegularCommand,
)
from cyberfusion.BorgSupport.repositories import Repository
from cyberfusion.Common.Command import CommandNonZeroError


def test_borg_regular_command_attributes_stdout(
    borg_regular_command: BorgRegularCommand,
) -> None:
    borg_regular_command.execute(
        command=None,
        arguments=["--version"],
        capture_stderr=False,
    )

    assert borg_regular_command.stdout.startswith("borg ")
    assert borg_regular_command.stderr is None
    assert borg_regular_command.rc == 0


def test_borg_regular_command_attributes_stderr(
    borg_regular_command: BorgRegularCommand,
) -> None:
    with pytest.raises(CommandNonZeroError) as e:
        borg_regular_command.execute(
            command=None,
            arguments=["--doesntexist"],
            capture_stderr=True,
        )

    assert e.value.stdout is not None
    assert e.value.stderr is not None
    assert e.value.rc == 2


def test_borg_logged_command_attributes(
    repository_init: Generator[Repository, None, None],
    borg_logged_command: BorgLoggedCommand,
    workspace_directory: Generator[str, None, None],
) -> None:
    borg_logged_command.execute(
        command="create",
        arguments=[
            os.path.join(workspace_directory, "repository2")
            + "::testarchivename",
            "/bin/sh",
        ],
        **repository_init._safe_cli_options,
    )

    assert borg_logged_command.file
    assert borg_logged_command.rc == 0
