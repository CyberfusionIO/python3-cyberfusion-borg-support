import os

from cyberfusion.BorgSupport import CAT_BIN, PassphraseFile


def test_passphrase_file_attributes(passphrase: str) -> None:
    passphrase_file = PassphraseFile(passphrase=passphrase)

    assert passphrase_file.path
    assert passphrase_file._passphrase == passphrase


def test_passphrase_file_enter_result(passphrase: str) -> None:
    passphrase_file = PassphraseFile(passphrase=passphrase)

    with passphrase_file as pf:
        assert pf == {"BORG_PASSCOMMAND": CAT_BIN + " " + passphrase_file.path}


def test_passphrase_file_contents_before_enter(passphrase: str) -> None:
    passphrase_file = PassphraseFile(passphrase=passphrase)

    assert open(passphrase_file.path).read() == ""


def test_passphrase_file_contents_after_enter(passphrase: str) -> None:
    passphrase_file = PassphraseFile(passphrase=passphrase)

    with passphrase_file:
        assert open(passphrase_file.path).read() == passphrase + "\n"


def test_passphrase_file_not_exists_after_enter(passphrase: str) -> None:
    passphrase_file = PassphraseFile(passphrase=passphrase)

    with passphrase_file:
        assert os.path.exists(passphrase_file.path)

    assert not os.path.exists(passphrase_file.path)
