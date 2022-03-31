import os

import pytest

from cyberfusion.BorgSupport.archives import Archive, UNIXFileTypes
from cyberfusion.BorgSupport.repositories import Repository
from cyberfusion.Common.Command import CommandNonZeroError


@pytest.mark.order(1)
def test_archive_setup(repository: Repository) -> None:
    """Test creating archive, and repository prune, size, archives and extract."""

    name = "test"
    NAME_ARCHIVE = "/tmp/backup::test"

    # Create directories and files to test archive extract and contents

    os.mkdir("/tmp/backmeupdir1")
    os.mkdir("/tmp/backmeupdir2")

    with open("/tmp/backmeupdir1/test1.txt", "w") as f:
        f.write("Hi! 1")

    with open("/tmp/backmeupdir2/test2.txt", "w") as f:
        f.write("Hi! 2")

    os.symlink("/tmp/backmeupdir2/test2.txt", "/tmp/backmeupdir2/symlink.txt")

    with open("/tmp/backmeupdir1/pleaseexcludeme", "w") as f:
        f.write("Please exclude me")

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

    assert repository.size == 42345

    # Create archive

    operation = archive.create(
        paths=["/tmp/backmeupdir1", "/tmp/backmeupdir2"],
        excludes=["/tmp/backmeupdir1/pleaseexcludeme"],
    )

    # Test archive created

    assert NAME_ARCHIVE in [a.name for a in repository.archives]

    # Test repository not empty

    assert repository.size != 42345

    # Test we can't create existing archive again

    with pytest.raises(CommandNonZeroError):
        archive.create(
            paths=["/tmp/backmeupdir1", "/tmp/backmeupdir2"],
            excludes=["/tmp/backmeupdir1/pleaseexcludeme"],
        )

    # Extract archive

    operation = archive.extract(
        destination_path="/tmp",
        restore_paths=["tmp/backmeupdir1/", "tmp/backmeupdir2/"],
    )  # Archive created before

    # Test archive extracted

    assert open("/tmp/tmp/backmeupdir1/test1.txt", "r").read() == "Hi! 1"
    assert open("/tmp/tmp/backmeupdir2/test2.txt", "r").read() == "Hi! 2"
    assert (
        os.readlink("/tmp/tmp/backmeupdir2/symlink.txt")
        == "/tmp/backmeupdir2/test2.txt"
    )
    assert not os.path.exists("/tmp/tmp/backmeupdir1/pleaseexcludeme")

    # Test archive contents from the root

    contents = archive.contents(path=None)

    assert len(contents) == 5

    assert contents[0].type_ == UNIXFileTypes.DIRECTORY
    assert contents[0].symbolic_mode == "drwxr-xr-x"
    assert contents[0].user == "root"
    assert contents[0].group == "root"
    assert contents[0].path == "tmp/backmeupdir1"
    assert contents[0].link_target is None
    assert contents[0].modification_time
    assert contents[0].size is None

    assert contents[1].type_ == UNIXFileTypes.REGULAR_FILE
    assert contents[1].symbolic_mode == "-rw-r--r--"
    assert contents[1].user == "root"
    assert contents[1].group == "root"
    assert contents[1].path == "tmp/backmeupdir1/test1.txt"
    assert contents[1].link_target is None
    assert contents[1].modification_time
    assert contents[1].size != 0

    assert contents[2].type_ == UNIXFileTypes.DIRECTORY
    assert contents[2].symbolic_mode == "drwxr-xr-x"
    assert contents[2].user == "root"
    assert contents[2].group == "root"
    assert contents[2].path == "tmp/backmeupdir2"
    assert contents[2].link_target is None
    assert contents[2].modification_time
    assert contents[2].size is None

    assert contents[3].type_ == UNIXFileTypes.REGULAR_FILE
    assert contents[3].symbolic_mode == "-rw-r--r--"
    assert contents[3].user == "root"
    assert contents[3].group == "root"
    assert contents[3].path == "tmp/backmeupdir2/test2.txt"
    assert contents[3].link_target is None
    assert contents[3].modification_time
    assert contents[3].size != 0

    assert contents[4].type_ == UNIXFileTypes.SYMBOLIC_LINK
    assert contents[4].symbolic_mode == "lrwxrwxrwx"
    assert contents[4].user == "root"
    assert contents[4].group == "root"
    assert contents[4].path == "tmp/backmeupdir2/symlink.txt"
    assert contents[4].link_target == "/tmp/backmeupdir2/test2.txt"
    assert contents[4].modification_time
    assert contents[4].size is None

    # Test archive contents from directory

    contents = archive.contents(path="tmp/backmeupdir1")

    assert len(contents) == 2

    assert contents[0].type_ == UNIXFileTypes.DIRECTORY
    assert contents[0].path == "tmp/backmeupdir1"

    assert contents[1].type_ == UNIXFileTypes.REGULAR_FILE
    assert contents[1].path == "tmp/backmeupdir1/test1.txt"

    # Test archive contents from file

    contents = archive.contents(path="tmp/backmeupdir1/test1.txt")

    assert len(contents) == 1

    assert contents[0].type_ == UNIXFileTypes.REGULAR_FILE
    assert contents[0].path == "tmp/backmeupdir1/test1.txt"

    # Prune repository now that is has an archive to prune. Use all keep_*
    # possibilities to test each 'if keep_*:' statement

    repository.prune(keep_hourly=1)
    repository.prune(keep_daily=1)
    repository.prune(keep_weekly=1)
    repository.prune(keep_monthly=1)
    repository.prune(keep_yearly=1)

    # Delete repository

    repository.delete()
