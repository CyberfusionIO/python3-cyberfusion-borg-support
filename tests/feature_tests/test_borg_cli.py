import os
from typing import Generator


from cyberfusion.BorgSupport import PassphraseFile
from cyberfusion.BorgSupport.borg_cli import (
    BorgLoggedCommand,
    BorgRegularCommand,
)
from cyberfusion.BorgSupport.repositories import Repository


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


def test_borg_regular_command_attributes_stderr(
    borg_regular_command: BorgRegularCommand,
) -> None:
    borg_regular_command.execute(
        command=None,
        arguments=[
            "--version",  # Writes to stdout
            "--show-rc",  # Writes to stderr
        ],
        capture_stderr=True,
    )

    assert borg_regular_command.stdout is not None
    assert borg_regular_command.stderr is not None


def test_borg_logged_command_attributes(
    repository_init: Generator[Repository, None, None],
    borg_logged_command: BorgLoggedCommand,
    workspace_directory: Generator[str, None, None],
) -> None:
    with PassphraseFile(repository_init.passphrase) as environment:
        borg_logged_command.execute(
            command="create",
            arguments=[
                os.path.join(workspace_directory, "repository2") + "::testarchivename",
                "/bin/sh",
            ],
            environment=environment,
            **repository_init._cli_options,
        )

    assert borg_logged_command.file
