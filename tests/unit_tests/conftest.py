import pytest

from cyberfusion.BorgSupport.borg_cli import (
    BorgLoggedCommand,
    BorgRegularCommand,
)
from cyberfusion.BorgSupport.repositories import Repository


@pytest.fixture
def repository() -> Repository:
    return Repository(path="/tmp/backup", passphrase="test")


@pytest.fixture(scope="session")
def repository_init() -> Repository:
    """Already initted repository."""
    repository = Repository(path="/tmp/anotherbackup", passphrase="test")

    repository.create(encryption="keyfile-blake2")

    return repository


@pytest.fixture
def borg_regular_command() -> BorgRegularCommand:
    return BorgRegularCommand()


@pytest.fixture
def borg_logged_command() -> BorgLoggedCommand:
    return BorgLoggedCommand()
