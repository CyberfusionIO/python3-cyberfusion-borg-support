"""Classes for interacting with Borg operations."""

import json
from enum import Enum
from typing import List, Optional, Union

from cyberfusion.BorgSupport.exceptions import OperationLineNotImplementedError


class JSONLineType(Enum):
    """JSON line types."""

    ARCHIVE_PROGRESS = "archive_progress"
    PROGRESS_MESSAGE = "progress_message"
    PROGRESS_PERCENT = "progress_percent"
    # FILE_STATUS = "file_status"
    LOG_MESSAGE = "log_message"


class MessageID(Enum):
    """Message IDs.

    From https://borgbackup.readthedocs.io/en/stable/internals/frontends.html#message-ids
    """

    # LOCK_ERROR = "LockError"  # Documented
    LOCK_TIMEOUT = "LockTimeout"  # Not documented


class ArchiveProgressLine:
    """Abstraction of JSON line in progress file."""

    def __init__(self, line: dict) -> None:
        """Set attributes."""
        self._line = line


class ProgressMessageLine:
    """Abstraction of JSON line in progress file."""

    def __init__(self, line: dict) -> None:
        """Set attributes."""
        self._line = line

    @property
    def finished(self) -> bool:
        """Get finished attribute."""
        return self._line["finished"]


class ProgressPercentLine:
    """Abstraction of JSON line in progress file."""

    def __init__(self, line: dict) -> None:
        """Set attributes."""
        self._line = line

    @property
    def finished(self) -> bool:
        """Get finished attribute."""
        return self._line["finished"]


class Operation:
    """Abstraction of Borg operation."""

    def __init__(self, *, progress_file: str) -> None:
        """Set attributes."""
        self.progress_file = progress_file

        self._lines = self.get_lines()

    def get_lines(
        self,
    ) -> List[
        Union[ArchiveProgressLine, ProgressMessageLine, ProgressPercentLine]
    ]:
        """Get JSON lines from progress file.

        Each line is a JSON document, see https://borgbackup.readthedocs.io/en/stable/internals/frontends.html#logging
        """
        lines: List[
            Union[
                ArchiveProgressLine, ProgressMessageLine, ProgressPercentLine
            ]
        ] = []

        with open(self.progress_file, "r") as f:
            for _line in f.read().splitlines():
                line = json.loads(_line)

                if line["type"] == JSONLineType.ARCHIVE_PROGRESS.value:
                    lines.append(ArchiveProgressLine(line))

                elif line["type"] == JSONLineType.PROGRESS_MESSAGE.value:
                    lines.append(ProgressMessageLine(line))

                elif line["type"] == JSONLineType.PROGRESS_PERCENT.value:
                    lines.append(ProgressPercentLine(line))

                else:
                    raise OperationLineNotImplementedError(
                        f"Got unknown line of type '{line['type']}': '{line}'"
                    )

        return lines

    @property
    def last_line(
        self,
    ) -> Optional[
        Union[ArchiveProgressLine, ProgressMessageLine, ProgressPercentLine]
    ]:
        """Get last JSON line from progress file.

        The last line contains the most recent status.
        """
        try:
            return self._lines[-1]
        except IndexError:
            # No lines yet

            return None
