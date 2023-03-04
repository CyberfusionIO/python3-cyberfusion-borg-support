"""Classes for basic interaction with Borg."""

from typing import Tuple

from cyberfusion.BorgSupport.borg_cli import BorgCommand, BorgRegularCommand


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
