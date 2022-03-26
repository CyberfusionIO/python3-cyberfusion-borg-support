from cyberfusion.BorgSupport import (
    ArchiveProgressLine,
    Operation,
    ProgressMessageLine,
    ProgressPercentLine,
)


def test_operation_attributes(operation: Operation) -> None:
    # Test progress_file

    assert operation.progress_file == "/tmp/progress_file.txt"

    # Test _lines

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
