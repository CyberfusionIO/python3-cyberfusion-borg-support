from typing import Generator

from cyberfusion.BorgSupport.repositories import Repository


def test_repository_cli_options(
    repository: Generator[Repository, None, None],
) -> None:
    assert repository._cli_options == {
        "identity_file_path": None,
    }
