import os
import shutil
from typing import Generator, List

import pytest

from cyberfusion.BorgSupport.archives import Archive
from cyberfusion.BorgSupport.borg_cli import (
    BorgLoggedCommand,
    BorgRegularCommand,
)
from cyberfusion.BorgSupport.repositories import Repository
from cyberfusion.Common import generate_random_string, get_tmp_file


@pytest.fixture(scope="session")
def workspace_directory() -> Generator[str, None, None]:
    path = os.path.join(
        os.path.sep, "tmp", "borg-" + generate_random_string().lower()
    )

    # Create

    os.mkdir(path)

    yield path

    # Clean up

    shutil.rmtree(path)


@pytest.fixture(scope="session")
def passphrase_file(
    workspace_directory: Generator[str, None, None]
) -> Generator[str, None, None]:
    path = os.path.join(workspace_directory, "passphrase")

    # Create

    with open(path, "w") as f:
        f.write("test")

    yield path

    # Clean up

    os.unlink(path)


@pytest.fixture
def repository(
    passphrase_file: Generator[str, None, None],
    workspace_directory: Generator[str, None, None],
) -> Generator[Repository, None, None]:
    path = os.path.join(workspace_directory, "repository1")

    yield Repository(path=path, passphrase_file=passphrase_file)


@pytest.fixture
def repository_init(
    passphrase_file: Generator[str, None, None],
    workspace_directory: Generator[str, None, None],
) -> Generator[Repository, None, None]:
    """Already initted repository.

    Size of empty repository is 42345 bytes.
    """

    # Create

    path = os.path.join(workspace_directory, "repository2")

    repository = Repository(path=path, passphrase_file=passphrase_file)

    repository.create(encryption="keyfile-blake2")

    yield repository

    # Clean up

    repository.delete()


@pytest.fixture(scope="session")
def dummy_files(
    workspace_directory: Generator[str, None, None]
) -> Generator[None, None, None]:
    dir1 = os.path.join(workspace_directory, "backmeupdir1")
    dir2 = os.path.join(workspace_directory, "backmeupdir2")

    # Create

    os.mkdir(dir1)
    os.mkdir(dir2)

    with open(f"{dir1}/test1.txt", "w") as f:
        f.write("Hi! 1")

    with open(f"{dir2}/test2.txt", "w") as f:
        f.write("Hi! 2")

    os.symlink(f"{dir2}/test2.txt", f"{dir2}/symlink.txt")

    with open(f"{dir1}/pleaseexcludeme", "w") as f:
        f.write("Please exclude me")

    yield

    # Clean up

    shutil.rmtree(dir1)
    shutil.rmtree(dir2)


@pytest.fixture
def archives(
    repository_init: Generator[Repository, None, None],
    dummy_files: Generator[None, None, None],
    workspace_directory: Generator[str, None, None],
) -> Generator[List[Archive], None, None]:
    archives = []

    # Create

    archive = Archive(
        repository=repository_init, name="test", comment="Free-form comment!"
    )
    archive.create(
        paths=[
            os.path.join(workspace_directory, "backmeupdir1"),
            os.path.join(workspace_directory, "backmeupdir2"),
        ],  # Created by dummy_files fixture
        excludes=[
            os.path.join(
                workspace_directory, "backmeupdir1", "pleaseexcludeme"
            )
        ],
    )
    archives.append(archive)

    yield archives

    # Clean up. Not implemented.

    pass


@pytest.fixture
def borg_regular_command() -> BorgRegularCommand:
    return BorgRegularCommand()


@pytest.fixture
def borg_logged_command() -> BorgLoggedCommand:
    return BorgLoggedCommand()
