"""Generic utilities."""

import base64
import os
import secrets
import shutil
import string
import uuid
from hashlib import md5

from cyberfusion.BorgSupport.exceptions import ExecutableNotFoundError


def get_md5_hash(path: str) -> str:
    """Get Base64 encoded 128-bit MD5 digest of file."""
    hash_ = md5()

    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(128 * hash_.block_size), b""):
            hash_.update(chunk)

    return base64.b64encode(hash_.digest()).decode()


def generate_random_string(length: int = 24) -> str:
    """Generate random string."""
    alphabet = string.ascii_letters + string.digits

    return "".join(secrets.choice(alphabet) for i in range(length))


def find_executable(name: str) -> str:
    """Find absolute path of executable.

    Use this function when the executable must exist. This function raises an
    exception if it does not.
    """
    path = shutil.which(name)

    if path:
        return path

    raise ExecutableNotFoundError(name)


def get_tmp_file() -> str:
    """Create tmp file and return path."""
    path = os.path.join(os.path.sep, "tmp", str(uuid.uuid4()))

    with open(path, "w"):
        pass

    os.chmod(path, 0o600)  # Do not allow regular users to view file contents

    return path
