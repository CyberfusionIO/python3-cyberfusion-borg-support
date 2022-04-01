import os

import pytest

from cyberfusion.BorgSupport.borg_cli import (
    BorgLoggedCommand,
    BorgRegularCommand,
)
from cyberfusion.BorgSupport.repositories import Repository
from cyberfusion.Common import get_tmp_file


@pytest.fixture(scope="session")
def passphrase_file() -> str:
    path = "/tmp/testingpassphrase"

    with open(path, "w") as f:
        f.write("test")

    return path


@pytest.fixture
def repository(passphrase_file: str) -> Repository:
    return Repository(path="/tmp/backup", passphrase_file=passphrase_file)


@pytest.fixture(scope="session")
def repository_init(passphrase_file: str) -> Repository:
    """Already initted repository.

    Size of empty repository is 42345 bytes.
    """
    repository = Repository(
        path="/tmp/anotherbackup", passphrase_file=passphrase_file
    )

    repository.create(encryption="keyfile-blake2")

    return repository


@pytest.fixture
def borg_regular_command() -> BorgRegularCommand:
    return BorgRegularCommand()


@pytest.fixture
def borg_logged_command() -> BorgLoggedCommand:
    return BorgLoggedCommand()
