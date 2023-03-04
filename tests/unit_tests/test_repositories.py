from typing import Generator

from cyberfusion.BorgSupport.repositories import Repository


def test_repository_safe_cli_options(
    repository: Generator[Repository, None, None],
    passphrase_file: Generator[str, None, None],
) -> None:
    assert repository._safe_cli_options == {
        "environment": {"BORG_PASSCOMMAND": f"/bin/cat {passphrase_file}"},
        "identity_file_path": None,
    }


def test_repository_dangerous_cli_options(
    repository: Generator[Repository, None, None],
    passphrase_file: Generator[str, None, None],
) -> None:
    assert repository._dangerous_cli_options == {
        "environment": {
            "BORG_PASSCOMMAND": f"/bin/cat {passphrase_file}",
            "BORG_DELETE_I_KNOW_WHAT_I_AM_DOING": "YES",
        },
        "identity_file_path": None,
    }
