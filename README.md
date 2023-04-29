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

# Configure

No configuration is supported.

# Usage

## Example

```python
from cyberfusion.BorgSupport.repositories import Repository
from cyberfusion.BorgSupport.archives import Archive

repository = Repository(path="/home/example/repository", passphrase_file="/home/example/.passphrase.txt", identity_file_path="/home/example/.ssh/id_rsa", create_if_not_exists=True)
archive = Archive(repository=repository, name="example", comment="Example", working_directory=os.path.sep, remove_paths_if_file=True)
```

# Tests

Run tests with pytest:

    pytest tests/

The tests must be run from the project root.
