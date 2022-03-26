import pytest

from cyberfusion.BorgSupport.archives import Archive
from cyberfusion.BorgSupport.repositories import Repository
from cyberfusion.Common.Command import CommandNonZeroError


@pytest.mark.order(1)
def test_archive_setup(repository: Repository) -> None:
    """Test creating archive, and repository prune, size, archives and extract."""

    name = "test"
    NAME_ARCHIVE = "/tmp/backup::test"

    # Touch files to test archive extract

    with open("/home/test1.txt", "w") as f:
        f.write("Hi! 1")

    with open("/var/test2.txt", "w") as f:
        f.write("Hi! 2")

    # Create repository

    repository.create(encryption="keyfile-blake2")

    # Set archive

    archive = Archive(repository=repository, name=name)

    # Test archive name

    assert archive.repository == repository
    assert archive._name == name
    assert archive.name == NAME_ARCHIVE

    # Test archive does not exist at first

    assert NAME_ARCHIVE not in [a.name for a in repository.archives]

    # Test repository empty

    assert repository.size == 0

    # Create archive

    operation = archive.create(paths=["/home", "/var"])

    # Test archive created

    assert NAME_ARCHIVE in [a.name for a in repository.archives]

    # Test repository not empty

    assert repository.size != 0

    # Test we can't create existing archive again

    with pytest.raises(CommandNonZeroError):
        archive.create(paths=["/home"])

    # Extract archive

    operation = archive.extract(
        destination_path="/tmp", restore_paths=["home/", "var/"]
    )  # Archive created before

    # Test archive extracted

    assert open("/tmp/home/test1.txt", "r").read() == "Hi! 1"
    assert open("/tmp/var/test2.txt", "r").read() == "Hi! 2"

    # Prune repository now that is has an archive to prune. Use all keep_*
    # possibilities to test each 'if keep_*:' statement

    repository.prune(keep_hourly=1)
    repository.prune(keep_daily=1)
    repository.prune(keep_weekly=1)
    repository.prune(keep_monthly=1)
    repository.prune(keep_yearly=1)

    # Delete repository

    repository.delete()
