import os
import shutil
from typing import Generator, List

import pytest
from pytest_mock import MockerFixture  # type: ignore[attr-defined]

from cyberfusion.BorgSupport.archives import (
    Archive,
    ArchiveRestoration,
    UNIXFileTypes,
)
from cyberfusion.BorgSupport.repositories import Repository


def test_archive_restoration_path_no_leading_slash(
    repository_init: Generator[Repository, None, None],
    archives: Generator[List[Archive], None, None],
    workspace_directory: Generator[str, None, None],
):
    dir1 = os.path.join(workspace_directory, "backmeupdir1")[
        len(os.path.sep) :
    ]

    with pytest.raises(ValueError):
        ArchiveRestoration(
            archive=archives[0],
            path=dir1,
            temporary_path_root_path=workspace_directory,
        )


def test_archive_restoration_path_unsupported_type(
    repository_init: Generator[Repository, None, None],
    archives: Generator[List[Archive], None, None],
    workspace_directory: Generator[str, None, None],
):
    with pytest.raises(NotImplementedError):
        ArchiveRestoration(
            archive=archives[0],
            path=os.path.join(
                workspace_directory, "backmeupdir2", "symlink.txt"
            ),
            temporary_path_root_path=workspace_directory,
        )


def test_archive_restoration_directory_attributes(
    repository_init: Generator[Repository, None, None],
    archives: Generator[List[Archive], None, None],
    workspace_directory: Generator[str, None, None],
):
    dir2_with_leading_slash = os.path.join(workspace_directory, "backmeupdir2")
    dir2_without_leading_slash = os.path.join(
        workspace_directory, "backmeupdir2"
    )[len(os.path.sep) :]

    archive_restoration = ArchiveRestoration(
        archive=archives[0],
        path=dir2_with_leading_slash,
        temporary_path_root_path=workspace_directory,
    )

    assert archive_restoration.archive == archives[0]
    assert archive_restoration._path == dir2_with_leading_slash
    assert not archive_restoration._enforce_home_directory
    assert archive_restoration.temporary_path.startswith(
        f"{workspace_directory}/.archive-restore-"
    )
    assert archive_restoration.type_ == UNIXFileTypes.DIRECTORY
    assert archive_restoration.filesystem_path == dir2_with_leading_slash
    assert archive_restoration.archive_path == dir2_without_leading_slash
    assert archive_restoration.strip_components == 2
    assert archive_restoration.bak_path == dir2_with_leading_slash + ".bak"

    assert os.path.isdir(archive_restoration.temporary_path)
    assert os.stat(archive_restoration.temporary_path).st_mode == 16832


def test_archive_restoration_regular_file_attributes(
    repository_init: Generator[Repository, None, None],
    archives: Generator[List[Archive], None, None],
    workspace_directory: Generator[str, None, None],
):
    file_with_leading_slash = os.path.join(
        workspace_directory, "backmeupdir2", "test2.txt"
    )
    file_without_leading_slash = os.path.join(
        workspace_directory, "backmeupdir2", "test2.txt"
    )[len(os.path.sep) :]

    archive_restoration = ArchiveRestoration(
        archive=archives[0],
        path=file_with_leading_slash,
        temporary_path_root_path=workspace_directory,
    )

    assert archive_restoration.archive == archives[0]
    assert archive_restoration._path == file_with_leading_slash
    assert not archive_restoration._enforce_home_directory
    assert archive_restoration.temporary_path.startswith(
        f"{workspace_directory}/.archive-restore-"
    )
    assert archive_restoration.type_ == UNIXFileTypes.REGULAR_FILE
    assert archive_restoration.filesystem_path == file_with_leading_slash
    assert archive_restoration.archive_path == file_without_leading_slash
    assert archive_restoration.strip_components == 3
    with pytest.raises(Exception):
        assert archive_restoration.bak_path

    assert os.path.isdir(archive_restoration.temporary_path)
    assert os.stat(archive_restoration.temporary_path).st_mode == 16832


def test_archive_restoration_path_not_in_home_directory(
    repository_init: Generator[Repository, None, None],
    archives: Generator[List[Archive], None, None],
    workspace_directory: Generator[str, None, None],
):
    dir2_with_leading_slash = os.path.join(workspace_directory, "backmeupdir2")

    with pytest.raises(ValueError):
        ArchiveRestoration(
            archive=archives[0],
            path=dir2_with_leading_slash,
            enforce_home_directory=True,
            temporary_path_root_path=workspace_directory,
        )


def test_archive_restoration_restore_regular_file(
    mocker: MockerFixture,
    repository_init: Generator[Repository, None, None],
    archives: Generator[List[Archive], None, None],
    workspace_directory: Generator[str, None, None],
):
    path = os.path.join(workspace_directory, "backmeupdir2", "test2.txt")

    archive_restoration = ArchiveRestoration(
        archive=archives[0],
        path=path,
        temporary_path_root_path=workspace_directory,
    )

    spy = mocker.spy(shutil, "move")

    archive_restoration.replace()

    spy.assert_called_once_with(
        archive_restoration.temporary_path + "/" + "test2.txt", path
    )


def test_archive_restoration_restore_directory_not_exists(
    mocker: MockerFixture,
    repository_init: Generator[Repository, None, None],
    archives: Generator[List[Archive], None, None],
    workspace_directory: Generator[str, None, None],
):
    path = os.path.join(workspace_directory, "backmeupdir2")

    archive_restoration = ArchiveRestoration(
        archive=archives[0],
        path=path,
        temporary_path_root_path=workspace_directory,
    )

    spy_isdir = mocker.spy(os.path, "isdir")
    mock_move = mocker.patch.object(
        shutil, "move", return_value=None
    )  # Don't actually move temporary path to filesystem path

    archive_restoration.filesystem_path = "/tmp/doesnotexist"  # Temporarily override so that os.path.isdir returns False
    archive_restoration.replace()

    spy_isdir.assert_has_calls(
        [
            mocker.call(archive_restoration.filesystem_path),
            mocker.call(archive_restoration.bak_path),
        ],
    )
    mock_move.assert_called_once_with(
        archive_restoration.temporary_path + "/" + "backmeupdir2",
        archive_restoration.filesystem_path,
    )


def test_archive_restoration_restore_directory_exists(
    mocker: MockerFixture,
    repository_init: Generator[Repository, None, None],
    archives: Generator[List[Archive], None, None],
    workspace_directory: Generator[str, None, None],
):
    path = os.path.join(workspace_directory, "backmeupdir2")

    archive_restoration = ArchiveRestoration(
        archive=archives[0],
        path=path,
        temporary_path_root_path=workspace_directory,
    )

    spy_isdir = mocker.spy(os.path, "isdir")
    spy_rename = mocker.spy(os, "rename")
    spy_shutil_move = mocker.spy(shutil, "move")
    spy_shutil_rmtree = mocker.spy(shutil, "rmtree")

    archive_restoration.replace()

    spy_isdir.assert_has_calls(
        [
            mocker.call(archive_restoration.filesystem_path),
            mocker.call(archive_restoration.bak_path),
        ],
    )
    assert spy_rename.call_args_list[0] == mocker.call(
        archive_restoration.filesystem_path, archive_restoration.bak_path
    )
    spy_shutil_move.assert_called_once_with(
        archive_restoration.temporary_path + "/" + "backmeupdir2",
        archive_restoration.filesystem_path,
    )
    spy_shutil_rmtree.assert_called_once_with(archive_restoration.bak_path)
