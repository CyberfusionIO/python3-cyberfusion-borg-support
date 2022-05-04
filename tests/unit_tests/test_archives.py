import os
import tarfile
from pathlib import Path
from typing import Generator, List

import pytest

from cyberfusion.BorgSupport.archives import Archive, UNIXFileTypes
from cyberfusion.BorgSupport.repositories import Repository
from cyberfusion.Common.Command import CommandNonZeroError


def test_archive_extract(
    repository_init: Generator[Repository, None, None],
    archives: Generator[List[Archive], None, None],
    workspace_directory: Generator[str, None, None],
) -> None:
    dir1 = os.path.join(workspace_directory, "backmeupdir1")[
        len(os.path.sep) :
    ]
    dir2 = os.path.join(workspace_directory, "backmeupdir2")[
        len(os.path.sep) :
    ]

    # Extract archive

    operation, destination_path = archives[0].extract(
        destination_path="/tmp",
        restore_paths=[dir1, dir2],
    )

    assert destination_path == "/tmp"

    # Test extracted

    assert open(f"/tmp/{dir1}/test1.txt", "r").read() == "Hi! 1"
    assert open(f"/tmp/{dir2}/test2.txt", "r").read() == "Hi! 2"
    assert os.readlink(f"/tmp/{dir2}/symlink.txt") == f"/{dir2}/test2.txt"
    assert not os.path.exists(f"/tmp/{dir1}/pleaseexcludeme")


def test_archive_export_tar(
    archives: Generator[List[Archive], None, None],
    workspace_directory: Generator[str, None, None],
) -> None:
    dir1 = os.path.join(workspace_directory, "backmeupdir1")[
        len(os.path.sep) :
    ]
    dir2 = os.path.join(workspace_directory, "backmeupdir2")[
        len(os.path.sep) :
    ]

    path = f"{workspace_directory}/mytar.tar.gz"

    # Export archive to tarball

    operation, destination_path = archives[0].export_tar(
        destination_path=path,
        restore_paths=[dir1, dir2],
        strip_components=1,
    )

    assert destination_path == path
    assert os.path.isfile(destination_path)

    # Test tarball contents

    assert tarfile.open(path).getnames() == [
        str(Path(*Path(dir1).parts[1:])),
        str(Path(*Path(f"{dir1}/test1.txt").parts[1:])),
        str(Path(*Path(dir2).parts[1:])),
        str(Path(*Path(f"{dir2}/test2.txt").parts[1:])),
        str(Path(*Path(f"{dir2}/symlink.txt").parts[1:])),
    ]


def test_archive_contents(
    archives: Generator[List[Archive], None, None],
    workspace_directory: Generator[str, None, None],
) -> None:
    dir1 = os.path.join(workspace_directory, "backmeupdir1")[
        len(os.path.sep) :
    ]
    dir2 = os.path.join(workspace_directory, "backmeupdir2")[
        len(os.path.sep) :
    ]

    # Test archive contents from the root

    contents = archives[0].contents(path=None)

    assert len(contents) == 5

    assert contents[0].type_ == UNIXFileTypes.DIRECTORY
    assert contents[0].symbolic_mode == "drwxr-xr-x"
    assert contents[0].user
    assert contents[0].group
    assert contents[0].path == dir1
    assert contents[0].link_target is None
    assert contents[0].modification_time
    assert contents[0].size is None

    assert contents[1].type_ == UNIXFileTypes.REGULAR_FILE
    assert contents[1].symbolic_mode == "-rw-r--r--"
    assert contents[1].user
    assert contents[1].group
    assert contents[1].path == f"{dir1}/test1.txt"
    assert contents[1].link_target is None
    assert contents[1].modification_time
    assert contents[1].size != 0

    assert contents[2].type_ == UNIXFileTypes.DIRECTORY
    assert contents[2].symbolic_mode == "drwxr-xr-x"
    assert contents[2].user
    assert contents[2].group
    assert contents[2].path == dir2
    assert contents[2].link_target is None
    assert contents[2].modification_time
    assert contents[2].size is None

    assert contents[3].type_ == UNIXFileTypes.REGULAR_FILE
    assert contents[3].symbolic_mode == "-rw-r--r--"
    assert contents[3].user
    assert contents[3].group
    assert contents[3].path == f"{dir2}/test2.txt"
    assert contents[3].link_target is None
    assert contents[3].modification_time
    assert contents[3].size != 0

    assert contents[4].type_ == UNIXFileTypes.SYMBOLIC_LINK
    assert (
        contents[4].symbolic_mode == "lrwxrwxrwx"
        or contents[4].symbolic_mode == "lrwxr-xr-x"
    )  # Different on macOS
    assert contents[4].user
    assert contents[4].group
    assert contents[4].path == f"{dir2}/symlink.txt"
    assert contents[4].link_target == f"/{dir2}/test2.txt"
    assert contents[4].modification_time
    assert contents[4].size is None

    # Test archive contents from directory

    contents = archives[0].contents(path=dir1)

    assert len(contents) == 2

    assert contents[0].type_ == UNIXFileTypes.DIRECTORY
    assert contents[0].path == dir1

    assert contents[1].type_ == UNIXFileTypes.REGULAR_FILE
    assert contents[1].path == f"{dir1}/test1.txt"

    # Test archive contents from file

    contents = archives[0].contents(path=f"{dir1}/test1.txt")

    assert len(contents) == 1

    assert contents[0].type_ == UNIXFileTypes.REGULAR_FILE
    assert contents[0].path == f"{dir1}/test1.txt"
