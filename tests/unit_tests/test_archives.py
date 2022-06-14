import os
import shutil
import tarfile
from pathlib import Path
from typing import Generator, List

import pytest
from pytest_mock import MockerFixture  # type: ignore[attr-defined]

from cyberfusion.BorgSupport.archives import Archive, UNIXFileTypes
from cyberfusion.BorgSupport.exceptions import RepositoryLockedError
from cyberfusion.BorgSupport.repositories import Repository
from cyberfusion.Common.Command import CommandNonZeroError


def test_archive_extract_locked(
    mocker: MockerFixture,
    archives: Generator[List[Archive], None, None],
    workspace_directory: Generator[str, None, None],
) -> None:
    mocker.patch(
        "cyberfusion.BorgSupport.repositories.Repository.is_locked",
        return_value=True,
    )

    with pytest.raises(RepositoryLockedError):
        archives[0].extract(
            destination_path="/tmp",
            restore_paths=[],
        )

    mocker.stopall()  # Unlock for teardown


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
    assert os.path.isdir(f"/tmp/{dir1}/testdir")
    assert open(f"/tmp/{dir1}/testdir/test3.txt", "r").read() == "Hi! 3"
    assert open(f"/tmp/{dir2}/test2.txt", "r").read() == "Hi! 2"
    assert os.readlink(f"/tmp/{dir2}/symlink.txt") == f"/{dir2}/test2.txt"
    assert not os.path.exists(f"/tmp/{dir1}/pleaseexcludeme")


def test_archive_export_tar_locked(
    mocker: MockerFixture,
    archives: Generator[List[Archive], None, None],
    workspace_directory: Generator[str, None, None],
) -> None:
    mocker.patch(
        "cyberfusion.BorgSupport.repositories.Repository.is_locked",
        return_value=True,
    )

    with pytest.raises(RepositoryLockedError):
        archives[0].export_tar(
            destination_path=f"{workspace_directory}/mytar.tar.gz",
            restore_paths=[],
            strip_components=1,
        )

    mocker.stopall()  # Unlock for teardown


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

    assert sorted(tarfile.open(path).getnames()) == sorted(
        [
            str(Path(*Path(dir1).parts[1:])),
            str(Path(*Path(f"{dir1}/test1.txt").parts[1:])),
            str(Path(*Path(f"{dir1}/testdir").parts[1:])),
            str(Path(*Path(f"{dir1}/testdir/test3.txt").parts[1:])),
            str(Path(*Path(dir2).parts[1:])),
            str(Path(*Path(f"{dir2}/symlink.txt").parts[1:])),
            str(Path(*Path(f"{dir2}/test2.txt").parts[1:])),
        ]
    )


def test_archive_create_locked(
    mocker: MockerFixture,
    repository_init: Generator[Repository, None, None],
    workspace_directory: Generator[str, None, None],
) -> None:
    archive = Archive(
        repository=repository_init, name="test", comment="Free-form comment!"
    )

    mocker.patch(
        "cyberfusion.BorgSupport.repositories.Repository.is_locked",
        return_value=True,
    )

    with pytest.raises(RepositoryLockedError):
        archive.create(paths=[], excludes=[])

    mocker.stopall()  # Unlock for teardown


def test_archive_contents_locked(
    mocker: MockerFixture,
    archives: Generator[List[Archive], None, None],
    workspace_directory: Generator[str, None, None],
) -> None:
    mocker.patch(
        "cyberfusion.BorgSupport.repositories.Repository.is_locked",
        return_value=True,
    )

    with pytest.raises(RepositoryLockedError):
        archives[0].contents(path=None)

    mocker.stopall()  # Unlock for teardown


def test_archive_contents_without_path(
    archives: Generator[List[Archive], None, None],
    workspace_directory: Generator[str, None, None],
) -> None:
    dir1 = os.path.join(workspace_directory, "backmeupdir1")[
        len(os.path.sep) :
    ]
    dir2 = os.path.join(workspace_directory, "backmeupdir2")[
        len(os.path.sep) :
    ]

    contents = archives[0].contents(path=None)

    assert len(contents) == 7

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
        and content.path == f"{dir1}/testdir"
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
        and content.path == f"{dir1}/testdir/test3.txt"
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


def test_archive_contents_with_path(
    archives: Generator[List[Archive], None, None],
    workspace_directory: Generator[str, None, None],
) -> None:
    dir1 = os.path.join(workspace_directory, "backmeupdir1")[
        len(os.path.sep) :
    ]

    # Test archive contents from directory

    contents = archives[0].contents(path=dir1)

    assert len(contents) == 4

    assert contents[0].type_ == UNIXFileTypes.DIRECTORY
    assert contents[0].path == dir1

    assert contents[1].type_ == UNIXFileTypes.REGULAR_FILE
    assert contents[1].path == f"{dir1}/test1.txt"

    assert contents[2].type_ == UNIXFileTypes.DIRECTORY
    assert contents[2].path == f"{dir1}/testdir"

    assert contents[3].type_ == UNIXFileTypes.REGULAR_FILE
    assert contents[3].path == f"{dir1}/testdir/test3.txt"

    # Test archive contents from file

    contents = archives[0].contents(path=f"{dir1}/test1.txt")

    assert len(contents) == 1

    assert contents[0].type_ == UNIXFileTypes.REGULAR_FILE
    assert contents[0].path == f"{dir1}/test1.txt"


def test_archive_contents_not_recursive(
    archives: Generator[List[Archive], None, None],
    workspace_directory: Generator[str, None, None],
) -> None:
    dir1 = os.path.join(workspace_directory, "backmeupdir1")[
        len(os.path.sep) :
    ]

    contents = archives[0].contents(path=dir1, recursive=False)

    assert len(contents) == 3

    # Path itself is included (path_is_parent)

    assert contents[0].type_ == UNIXFileTypes.DIRECTORY
    assert contents[0].path == dir1

    # 'testdir/test3.txt' is not included, so recursive=False works

    assert contents[1].type_ == UNIXFileTypes.REGULAR_FILE
    assert contents[1].path == f"{dir1}/test1.txt"

    assert contents[2].type_ == UNIXFileTypes.DIRECTORY
    assert contents[2].path == f"{dir1}/testdir"
