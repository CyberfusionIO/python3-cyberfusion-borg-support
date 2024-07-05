"""Classes for interaction with Borg CLI.

Follow 'good and preferred' order at https://borgbackup.readthedocs.io/en/stable/usage/general.html?highlight=positional#positional-arguments-and-options-order-matters
"""

import json
import subprocess
from typing import Dict, List, Optional

from cyberfusion.BorgSupport.exceptions import (
    LoggedCommandFailedError,
    RegularCommandFailedError,
)
from cyberfusion.BorgSupport.utilities import find_executable, get_tmp_file


class BorgCommand:
    """Constants for Borg CLI."""

    BORG_BIN = find_executable("borg")
    TRUE_BIN = find_executable("true")

    # Subcommands

    SUBCOMMAND_DELETE = "delete"
    SUBCOMMAND_PRUNE = "prune"
    SUBCOMMAND_LIST = "list"
    SUBCOMMAND_CHECK = "check"
    SUBCOMMAND_EXTRACT = "extract"
    SUBCOMMAND_INIT = "init"
    SUBCOMMAND_CREATE = "create"
    SUBCOMMAND_EXPORT_TAR = "export-tar"
    SUBCOMMAND_WITH_LOCK = "with-lock"
    SUBCOMMAND_COMPACT = "compact"
    SUBCOMMAND_VERSION = "--version"


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
        capture_stderr: bool = False,
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

        try:
            output = subprocess.run(
                self.command,
                env=environment,
                check=True,
                stdout=subprocess.PIPE,
                text=True,
                stderr=subprocess.PIPE if capture_stderr else None,
            )
        except subprocess.CalledProcessError as e:
            raise RegularCommandFailedError(
                command=self.command,
                stderr=e.stderr,
                return_code=e.returncode,
            )

        # Set attributes

        self.stdout = output.stdout
        self.stderr = output.stderr

        # Cast if JSON

        if json_format:
            self.stdout = json.loads(self.stdout)


class BorgLoggedCommand:
    """Abstract Borg CLI implementation for use in scripts, for running logged commands.

    Borg is able to write logs to stderr, see: https://borgbackup.readthedocs.io/en/stable/internals/frontends.html#logging
    This can be used to monitor progress. This class implements the Borg CLI for
    commands that should be run in this way.
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

        self.file = get_tmp_file()

        # Add arguments

        if identity_file_path:
            self.command.extend(_get_rsh_argument(identity_file_path))

        self.command.extend(arguments)

        # Execute command

        if not run:
            return

        # Execute command

        with open(self.file, "w") as f:
            try:
                subprocess.run(
                    self.command,
                    env=environment,
                    cwd=working_directory,
                    check=True,
                    # Write to file so that callers can pass this to 'Operation'
                    # as 'progress_file'. Also, stderr should be written to file
                    # as output can be extremely large, mostly with SUBCOMMAND_CHECK.
                    stderr=f,
                )
            except subprocess.CalledProcessError as e:
                raise LoggedCommandFailedError(
                    command=self.command,
                    output_file_path=self.file,
                    return_code=e.returncode,
                )
