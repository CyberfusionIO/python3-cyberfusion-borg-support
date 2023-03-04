from cyberfusion.BorgSupport import Borg


def test_borg_version() -> None:
    major, minor, point = Borg().version

    assert isinstance(major, int)
    assert isinstance(minor, int)
    assert isinstance(point, int)
