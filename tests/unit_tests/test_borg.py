from cyberfusion.BorgSupport import Borg


def test_borg_version() -> None:
    assert Borg().version == (1, 2, 2)
