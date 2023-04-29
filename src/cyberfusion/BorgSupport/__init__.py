"""Classes for basic interaction with Borg."""

import os
from typing import Dict, Tuple

from cyberfusion.BorgSupport.borg_cli import BorgCommand, BorgRegularCommand
from cyberfusion.BorgSupport.utilities import find_executable, get_tmp_file

CAT_BIN = find_executable("cat")


class Borg:
    """Abstraction of Borg."""

    def __init__(self) -> None:
        """Do nothing."""
        pass

    @property
    def version(self) -> Tuple[int, int, int]:
        """Get Borg version."""

        # Execute command

        command = BorgRegularCommand()

        command.execute(command=BorgCommand.SUBCOMMAND_VERSION)

        # Get version

        _, version = command.stdout.split(" ")

        # Remove trailing newline from version

        version = version.rstrip()

        # Split version parts

        major, minor, point = version.split(".")

        # Cast to ints and return

        return int(major), int(minor), int(point)


class PassphraseFile:
    """Abstraction of passphrase file.

    Automatically creates and deletes.
    """

    def __init__(self, passphrase: str) -> None:
        """Set attributes."""
        self.path = get_tmp_file()

        self._passphrase = passphrase

    def __enter__(self) -> Dict[str, str]:
        """Create file and write passphrase.

        Returns environment variable for use with Borg CLI.
        """
        with open(self.path, "w") as f:
            f.write(self._passphrase + "\n")

        # The passphrase is retrieved by passing a command to BORG_PASSCOMMAND. This
        # is used instead of BORG_PASSPHRASE in order to to prevent the passphrase
        # from showing up in the environment variables. See:

        # https://borgbackup.readthedocs.io/en/stable/faq.html#how-can-i-specify-the-encryption-passphrase-programmatically

        return {"BORG_PASSCOMMAND": CAT_BIN + " " + self.path}

    def __exit__(self, type, value, traceback) -> None:  # type: ignore[no-untyped-def]
        """Delete file."""
        os.unlink(self.path)
