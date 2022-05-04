import os
import shutil
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
        str(Path(*Path(f"{dir2}/symlink.txt").parts[1:])),
        str(Path(*Path(f"{dir2}/test2.txt").parts[1:])),
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
    #
    # Order is unknown

    contents = archives[0].contents(path=None)

    assert len(contents) == 5

    assert any(
        content.type_ == UNIXFileTypes.DIRECTORY
        and content.symbolic_mode is not None
        and content.user is not None
        and content.group is not None
        and content.path == dir1
        and content.link_target is None
        and content.modification_time is not None
        and content.size is None
        for content in contents
    )
    assert any(
        content.type_ == UNIXFileTypes.REGULAR_FILE
        and content.symbolic_mode is not None
        and content.user is not None
        and content.group is not None
        and content.path == f"{dir1}/test1.txt"
        and content.link_target is None
        and content.modification_time is not None
        and content.size != 0
        for content in contents
    )
    assert any(
        content.type_ == UNIXFileTypes.DIRECTORY
        and content.symbolic_mode is not None
        and content.user is not None
        and content.group is not None
        and content.path == dir2
        and content.link_target is None
        and content.modification_time is not None
        and content.size is None
        for content in contents
    )
    assert any(
        content.type_ == UNIXFileTypes.REGULAR_FILE
        and content.symbolic_mode is not None
        and content.user is not None
        and content.group is not None
        and content.path == f"{dir2}/test2.txt"
        and content.link_target is None
        and content.modification_time is not None
        and content.size != 0
        for content in contents
    )
    assert any(
        content.type_ == UNIXFileTypes.SYMBOLIC_LINK
        and content.symbolic_mode is not None
        and content.user is not None
        and content.group is not None
        and content.path == f"{dir2}/symlink.txt"
        and content.link_target == f"/{dir2}/test2.txt"
        and content.modification_time is not None
        and content.size is None
        for content in contents
    )

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
