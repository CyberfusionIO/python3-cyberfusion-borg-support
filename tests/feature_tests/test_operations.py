from typing import Generator

import pytest

from cyberfusion.BorgSupport.exceptions import OperationLineNotImplementedError
from cyberfusion.BorgSupport.operations import (
    ArchiveProgressLine,
    Operation,
    ProgressMessageLine,
    ProgressPercentLine,
)


def test_operation_attributes() -> None:
    # Get operation

    operation = Operation(
        progress_file="/tmp/progress_file_with_known_types.txt"
    )

    # Test progress_file

    assert operation.progress_file == "/tmp/progress_file_with_known_types.txt"

    # Test lines

    assert len(operation._lines) == 12

    assert isinstance(operation._lines[0], ArchiveProgressLine)

    assert isinstance(operation._lines[1], ProgressMessageLine)
    assert not operation._lines[1].finished

    assert isinstance(operation._lines[2], ProgressMessageLine)
    assert not operation._lines[2].finished

    assert isinstance(operation._lines[3], ProgressMessageLine)
    assert not operation._lines[3].finished

    assert isinstance(operation._lines[4], ProgressMessageLine)
    assert operation._lines[4].finished

    assert isinstance(operation._lines[5], ArchiveProgressLine)
    assert isinstance(operation._lines[6], ArchiveProgressLine)

    assert isinstance(operation._lines[7], ProgressMessageLine)
    assert not operation._lines[7].finished

    assert isinstance(operation._lines[8], ProgressMessageLine)
    assert not operation._lines[8].finished

    assert isinstance(operation._lines[9], ProgressMessageLine)
    assert not operation._lines[9].finished

    assert isinstance(operation._lines[10], ProgressPercentLine)
    assert not operation._lines[10].finished

    assert isinstance(operation._lines[11], ProgressMessageLine)
    assert operation._lines[11].finished

    # Test last_line is last line

    assert operation.last_line == operation._lines[-1]


def test_operation_unknown_types_error() -> None:
    with pytest.raises(OperationLineNotImplementedError):
        Operation(progress_file="/tmp/progress_file_with_unknown_types.txt")


def test_operation_no_lines() -> None:
    # Get operation

    operation = Operation(progress_file="/tmp/progress_file_with_no_lines.txt")

    # Test lines is empty

    assert not operation._lines

    # Test last_line is None (as there are no lines)

    assert operation.last_line is None
