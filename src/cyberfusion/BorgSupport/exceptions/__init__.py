"""Generic exceptions."""


class RepositoryLockedError(Exception):
    """Exception to raise if repository is locked."""

    pass


class RepositoryPathInvalidError(Exception):
    """Exception to raise if repository path is not supported by this library."""

    pass


class OperationLineNotImplementedError(Exception):
    """Exception to raise if line in operation progress file is not supported by this library."""

    pass
