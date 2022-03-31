"""Generic exceptions."""


class RepositoryNotLocalError(Exception):
    """Exception to raise if repository is not on local filesystem when this is required."""

    pass


class RepositoryPathInvalidError(Exception):
    """Exception to raise if repository path is not supported by this library."""

    pass


class OperationLineNotImplementedError(Exception):
    """Exception to raise if line in operation progress file is not supported by this library."""

    pass
