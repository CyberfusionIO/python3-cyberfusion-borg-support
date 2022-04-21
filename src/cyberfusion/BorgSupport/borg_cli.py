"""Classes for interaction with Borg CLI.

Follow 'good and preferred' order at https://borgbackup.readthedocs.io/en/stable/usage/general.html?highlight=positional#positional-arguments-and-options-order-matters
"""

import json
import os
from typing import Dict, List, Optional

from cyberfusion.Common.Command import CyberfusionCommand


class BorgCommand:
    """Constants for Borg CLI."""

    BORG_BIN = os.path.join(CyberfusionCommand.PATH_USR_BIN, "borg")

    SUBCOMMAND_DELETE = "delete"
    SUBCOMMAND_PRUNE = "prune"
    SUBCOMMAND_LIST = "list"
    SUBCOMMAND_CHECK = "check"
    SUBCOMMAND_EXTRACT = "extract"
    SUBCOMMAND_INIT = "init"
    SUBCOMMAND_CREATE = "create"


def _get_rsh_argument(identity_file_path: str) -> List[str]:
    """Get value of '--rsh' argument for Borg CLI commands.

    When connecting over SSH, set:

    - BatchMode (see https://borgbackup.readthedocs.io/en/stable/usage/notes.html?highlight=borg%20serve#ssh-batch-mode)
    - StrictHostKeyChecking, as host is unknown on first run, so non-interactive scripts would block otherwise
    - Path to identity file
    """
    return [
        "--rsh",
        f"ssh -oBatchMode=yes -oStrictHostKeyChecking=no -i {identity_file_path}",
    ]


class BorgRegularCommand:
    """Abstract Borg CLI implementation for use in scripts."""

    def __init__(self) -> None:
        """Do nothing."""
        pass

    def execute(
        self,
        *,
        command: Optional[str],
        arguments: Optional[List[str]] = None,
        json_format: bool = False,
        identity_file_path: Optional[str] = None,
        environment: Optional[Dict[str, str]] = None,
        run: bool = True,
    ) -> None:
        """Set attributes and execute command."""
        self.command = [BorgCommand.BORG_BIN]

        # Add command

        if command is not None:
            self.command.append(command)

        # Add --json if JSON

        if json_format:
            self.command.append("--json")

        # Add arguments

        if identity_file_path:
            self.command.extend(_get_rsh_argument(identity_file_path))

        if arguments is not None:
            self.command.extend(arguments)

        # Execute command

        if not run:
            return

        output = CyberfusionCommand(
            self.command,
            environment=environment,
        )

        # Set attributes

        self.rc = output.rc
        self.stdout = output.stdout

        # Cast if JSON

        if json_format:
            self.stdout = json.loads(self.stdout)


class BorgLoggedCommand:
    """Abstract Borg CLI implementation for use in scripts, for running logged commands.

    Borg is able to write logs to stderr, see: https://borgbackup.readthedocs.io/en/stable/internals/frontends.html#logging

    This can be used to monitor progress. This class implements the Borg CLI for
    commands that should be run in this way. It only captures stderr, not stdout.
    """

    def __init__(self) -> None:
        """Do nothing."""
        pass

    def execute(
        self,
        *,
        command: str,
        arguments: List[str],
        identity_file_path: Optional[str] = None,
        working_directory: Optional[str] = None,
        environment: Optional[Dict[str, str]] = None,
        run: bool = True,
    ) -> None:
        """Set attributes and execute command."""
        self.command = [
            BorgCommand.BORG_BIN,
            "--progress",
            "--log-json",
            command,
        ]

        # Add arguments

        if identity_file_path:
            self.command.extend(_get_rsh_argument(identity_file_path))

        self.command.extend(arguments)

        # Execute command

        if not run:
            return

        # Execute command

        output = CyberfusionCommand(
            self.command,
            environment=environment,
            path=working_directory,
            read=False,
            unlink=False,
            capture_stdout=False,
            capture_stderr=True,
        )

        # Set attributes

        self.file = output.stderr_file
        self.rc = output.rc
