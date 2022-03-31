import os
import shutil

import pytest

from cyberfusion.BorgSupport.repositories import Repository
from cyberfusion.Common.Command import CommandNonZeroError


def test_repository_safe_cli_options(repository: Repository) -> None:
    assert repository._safe_cli_options == {
        "environment": {"BORG_PASSPHRASE": "test"},
        "identity_file_path": None,
    }


def test_repository_dangerous_cli_options(repository: Repository) -> None:
    assert repository._dangerous_cli_options == {
        "environment": {
            "BORG_PASSPHRASE": "test",
            "BORG_DELETE_I_KNOW_WHAT_I_AM_DOING": "YES",
        },
        "identity_file_path": None,
    }


def test_repository_attributes(repository: Repository) -> None:
    assert repository.path == "/tmp/backup"
    assert repository.passphrase == "test"
    assert repository.identity_file_path is None


@pytest.mark.order(2)
def test_repository_setup_teardown(repository: Repository) -> None:
    """Test creating and deleting repository."""

    # Test repository does not exist at first

    assert not os.path.isdir("/tmp/backup")
    assert not repository.exists

    # Create repository

    repository.create(encryption="keyfile-blake2")

    # Test repository empty

    assert not repository.archives
    assert repository.size == 42345

    # Test repository created

    assert os.path.isdir("/tmp/backup")
    assert repository.exists

    # Test we can't create existing repository again

    with pytest.raises(CommandNonZeroError):
        repository.create(encryption="keyfile-blake2")

    # Delete repository

    repository.delete()

    # Test repository deleted

    assert not os.path.isdir("/tmp/backup")
    assert not repository.exists


@pytest.mark.order(3)
def test_repository_check(repository: Repository) -> None:
    """Test repository check."""

    # Create repository

    repository.create(encryption="keyfile-blake2")

    # Test repository check successful

    assert repository.check()

    # Damage repository

    shutil.move(os.path.join("/tmp/backup", "data"), "/tmp/moveddata")

    # Test check fails

    assert not repository.check()

    # Restore repository

    shutil.move("/tmp/moveddata", os.path.join("/tmp/backup", "data"))

    # Test repository check successful

    assert repository.check()

    # Delete repository

    repository.delete()
