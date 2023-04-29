import os

import pytest

from cyberfusion.BorgSupport.exceptions import ExecutableNotFoundError
from cyberfusion.BorgSupport.utilities import (
    find_executable,
    generate_random_string,
    get_md5_hash,
    get_tmp_file,
)


def test_get_md5_hash() -> None:
    tmp_file = get_tmp_file()

    with open(tmp_file, "w") as f:
        f.write(
            """[section]
key = value
"""
        )

    assert get_md5_hash(tmp_file) == "hBsHfRYSEt9be/4VhWwbAw=="


def test_generate_random_string_length() -> None:
    assert len(generate_random_string()) == 24


def test_find_executable_found() -> None:
    assert find_executable("true")


def test_find_executable_not_found() -> None:
    name = "doesnotexist"

    with pytest.raises(ExecutableNotFoundError) as e:
        find_executable(name)

    assert e.value.name == name


def test_get_tmp_file_path() -> None:
    assert get_tmp_file().startswith("/tmp/")


def test_get_tmp_file_permissions() -> None:
    assert os.stat(get_tmp_file()).st_mode == 33152
