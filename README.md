# python3-cyberfusion-borg-support

Library for [Borg](https://www.borgbackup.org/).

# Install

## Generic

Run the following command to create a source distribution:

    python3 setup.py sdist

Next, install Borg according to the [documentation](https://borgbackup.readthedocs.io/en/stable/installation.html#distribution-package).

## Debian

Run the following commands to build a Debian package:

    mk-build-deps -i -t 'apt -o Debug::pkgProblemResolver=yes --no-install-recommends -y'
    dpkg-buildpackage -us -uc

## PyPI

Run the following command to install the package from PyPI:

    pip3 install python3-cyberfusion-borg-support

Next, install Borg according to the [documentation](https://borgbackup.readthedocs.io/en/stable/installation.html#distribution-package).

# Configure

No configuration is supported.

# Usage

## Example

```python
import os

from cyberfusion.BorgSupport.repositories import Repository
from cyberfusion.BorgSupport.archives import Archive

repository = Repository(path="/home/example/repository", passphrase="test", identity_file_path=None, create_if_not_exists=True)
archive = Archive(repository=repository, name="example", comment="Example")
```

# Tests

Run tests with pytest:

    pytest tests/

The tests must be run from the project root.
