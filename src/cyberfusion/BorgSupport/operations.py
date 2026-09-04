"""Classes for interacting with Borg operations."""

import json
from enum import Enum
from typing import Dict, List, Optional

from cyberfusion.BorgSupport.exceptions import OperationLineNotImplementedError


class JSONLineType(Enum):
    """JSON line types."""

    ARCHIVE_PROGRESS = "archive_progress"
    PROGRESS_MESSAGE = "progress_message"
    PROGRESS_PERCENT = "progress_percent"
    FILE_STATUS = "file_status"
    LOG_MESSAGE = "log_message"


class MessageID(Enum):
    """Message IDs.

    From https://borgbackup.readthedocs.io/en/stable/internals/frontends.html#message-ids
    """

    # Errors

    ERROR = "Error"
    ERROR_WITH_TRACEBACK = "ErrorWithTraceback"
    BUFFER_MEMORY_LIMIT_EXCEEDED = "Buffer.MemoryLimitExceeded"
    EFFICIENT_COLLECTION_QUEUE_SIZE_UNDERFLOW = "EfficientCollectionQueue.SizeUnderflow"
    RT_ERROR = "RTError"
    CANCELLED_BY_USER = "CancelledByUser"
    COMMAND_ERROR = "CommandError"
    PLACEHOLDER_ERROR = "PlaceholderError"
    INVALID_PLACEHOLDER = "InvalidPlaceholder"
    REPOSITORY_ALREADY_EXISTS = "Repository.AlreadyExists"
    REPOSITORY_ATTIC_REPOSITORY = "Repository.AtticRepository"
    REPOSITORY_CHECK_NEEDED = "Repository.CheckNeeded"
    REPOSITORY_DOES_NOT_EXIST = "Repository.DoesNotExist"
    REPOSITORY_INSUFFICIENT_FREE_SPACE_ERROR = "Repository.InsufficientFreeSpaceError"
    REPOSITORY_INVALID_REPOSITORY = "Repository.InvalidRepository"
    REPOSITORY_INVALID_REPOSITORY_CONFIG = "Repository.InvalidRepositoryConfig"
    REPOSITORY_OBJECT_NOT_FOUND = "Repository.ObjectNotFound"
    REPOSITORY_PARENT_PATH_DOES_NOT_EXIST = "Repository.ParentPathDoesNotExist"
    REPOSITORY_PATH_ALREADY_EXISTS = "Repository.PathAlreadyExists"
    REPOSITORY_STORAGE_QUOTA_EXCEEDED = "Repository.StorageQuotaExceeded"
    REPOSITORY_PATH_PERMISSION_DENIED = "Repository.PathPermissionDenied"
    MANDATORY_FEATURE_UNSUPPORTED = "MandatoryFeatureUnsupported"
    NO_MANIFEST_ERROR = "NoManifestError"
    UNSUPPORTED_MANIFEST_ERROR = "UnsupportedManifestError"
    ARCHIVE_ALREADY_EXISTS = "Archive.AlreadyExists"
    ARCHIVE_DOES_NOT_EXIST = "Archive.DoesNotExist"
    ARCHIVE_INCOMPATIBLE_FILESYSTEM_ENCODING_ERROR = (
        "Archive.IncompatibleFilesystemEncodingError"
    )
    KEYFILE_INVALID_ERROR = "KeyfileInvalidError"
    KEYFILE_MISMATCH_ERROR = "KeyfileMismatchError"
    KEYFILE_NOT_FOUND_ERROR = "KeyfileNotFoundError"
    NOT_A_BORG_KEY_FILE = "NotABorgKeyFile"
    REPO_KEY_NOT_FOUND_ERROR = "RepoKeyNotFoundError"
    REPO_ID_MISMATCH = "RepoIdMismatch"
    UNENCRYPTED_REPO = "UnencryptedRepo"
    UNKNOWN_KEY_TYPE = "UnknownKeyType"
    UNSUPPORTED_PAYLOAD_ERROR = "UnsupportedPayloadError"
    NO_PASSPHRASE_FAILURE = "NoPassphraseFailure"
    PASSCOMMAND_FAILURE = "PasscommandFailure"
    PASSPHRASE_WRONG = "PassphraseWrong"
    PASSWORD_RETRIES_EXCEEDED = "PasswordRetriesExceeded"
    CACHE_CACHE_INIT_ABORTED_ERROR = "Cache.CacheInitAbortedError"
    CACHE_ENCRYPTION_METHOD_MISMATCH = "Cache.EncryptionMethodMismatch"
    CACHE_REPOSITORY_ACCESS_ABORTED = "Cache.RepositoryAccessAborted"
    CACHE_REPOSITORY_ID_NOT_UNIQUE = "Cache.RepositoryIDNotUnique"
    CACHE_REPOSITORY_REPLAY = "Cache.RepositoryReplay"
    LOCK_ERROR = "LockError"
    LOCK_ERROR_T = "LockErrorT"
    LOCK_FAILED = "LockFailed"
    LOCK_TIMEOUT = "LockTimeout"
    NOT_LOCKED = "NotLocked"
    NOT_MY_LOCK = "NotMyLock"
    CONNECTION_CLOSED = "ConnectionClosed"
    CONNECTION_CLOSED_WITH_HINT = "ConnectionClosedWithHint"
    INVALID_RPC_METHOD = "InvalidRPCMethod"
    PATH_NOT_ALLOWED = "PathNotAllowed"
    REMOTE_REPOSITORY_RPC_SERVER_OUTDATED = "RemoteRepository.RPCServerOutdated"
    UNEXPECTED_RPC_DATA_FORMAT_FROM_CLIENT = "UnexpectedRPCDataFormatFromClient"
    UNEXPECTED_RPC_DATA_FORMAT_FROM_SERVER = "UnexpectedRPCDataFormatFromServer"
    CONNECTION_BROKEN_WITH_HINT = "ConnectionBrokenWithHint"
    INTEGRITY_ERROR = "IntegrityError"
    FILE_INTEGRITY_ERROR = "FileIntegrityError"
    DECOMPRESSION_ERROR = "DecompressionError"
    ARCHIVE_TAM_INVALID = "ArchiveTAMInvalid"
    ARCHIVE_TAM_REQUIRED_ERROR = "ArchiveTAMRequiredError"
    TAM_INVALID = "TAMInvalid"
    TAM_REQUIRED_ERROR = "TAMRequiredError"
    TAM_UNSUPPORTED_SUITE_ERROR = "TAMUnsupportedSuiteError"

    # Warnings

    BORG_WARNING = "BorgWarning"
    BACKUP_WARNING = "BackupWarning"
    FILE_CHANGED_WARNING = "FileChangedWarning"
    INCLUDE_PATTERN_NEVER_MATCHED_WARNING = "IncludePatternNeverMatchedWarning"
    BACKUP_ERROR = "BackupError"
    BACKUP_RACE_CONDITION_ERROR = "BackupRaceConditionError"
    BACKUP_OS_ERROR = "BackupOSError"
    BACKUP_PERMISSION_ERROR = "BackupPermissionError"
    BACKUP_IO_ERROR = "BackupIOError"
    BACKUP_FILE_NOT_FOUND_ERROR = "BackupFileNotFoundError"


# Mapping between Borg exit codes (with BORG_EXIT_CODES=modern) and their message ID.
# From https://borgbackup.readthedocs.io/en/stable/internals/frontends.html#return-codes

EXIT_CODE_MESSAGE_IDS: Dict[int, MessageID] = {
    1: MessageID.BORG_WARNING,
    2: MessageID.ERROR,
    3: MessageID.CANCELLED_BY_USER,
    4: MessageID.COMMAND_ERROR,
    5: MessageID.PLACEHOLDER_ERROR,
    6: MessageID.INVALID_PLACEHOLDER,
    10: MessageID.REPOSITORY_ALREADY_EXISTS,
    11: MessageID.REPOSITORY_ATTIC_REPOSITORY,
    12: MessageID.REPOSITORY_CHECK_NEEDED,
    13: MessageID.REPOSITORY_DOES_NOT_EXIST,
    14: MessageID.REPOSITORY_INSUFFICIENT_FREE_SPACE_ERROR,
    15: MessageID.REPOSITORY_INVALID_REPOSITORY,
    16: MessageID.REPOSITORY_INVALID_REPOSITORY_CONFIG,
    17: MessageID.REPOSITORY_OBJECT_NOT_FOUND,
    18: MessageID.REPOSITORY_PARENT_PATH_DOES_NOT_EXIST,
    19: MessageID.REPOSITORY_PATH_ALREADY_EXISTS,
    20: MessageID.REPOSITORY_STORAGE_QUOTA_EXCEEDED,
    21: MessageID.REPOSITORY_PATH_PERMISSION_DENIED,
    25: MessageID.MANDATORY_FEATURE_UNSUPPORTED,
    26: MessageID.NO_MANIFEST_ERROR,
    27: MessageID.UNSUPPORTED_MANIFEST_ERROR,
    30: MessageID.ARCHIVE_ALREADY_EXISTS,
    31: MessageID.ARCHIVE_DOES_NOT_EXIST,
    32: MessageID.ARCHIVE_INCOMPATIBLE_FILESYSTEM_ENCODING_ERROR,
    40: MessageID.KEYFILE_INVALID_ERROR,
    41: MessageID.KEYFILE_MISMATCH_ERROR,
    42: MessageID.KEYFILE_NOT_FOUND_ERROR,
    43: MessageID.NOT_A_BORG_KEY_FILE,
    44: MessageID.REPO_KEY_NOT_FOUND_ERROR,
    45: MessageID.REPO_ID_MISMATCH,
    46: MessageID.UNENCRYPTED_REPO,
    47: MessageID.UNKNOWN_KEY_TYPE,
    48: MessageID.UNSUPPORTED_PAYLOAD_ERROR,
    50: MessageID.NO_PASSPHRASE_FAILURE,
    51: MessageID.PASSCOMMAND_FAILURE,
    52: MessageID.PASSPHRASE_WRONG,
    53: MessageID.PASSWORD_RETRIES_EXCEEDED,
    60: MessageID.CACHE_CACHE_INIT_ABORTED_ERROR,
    61: MessageID.CACHE_ENCRYPTION_METHOD_MISMATCH,
    62: MessageID.CACHE_REPOSITORY_ACCESS_ABORTED,
    63: MessageID.CACHE_REPOSITORY_ID_NOT_UNIQUE,
    64: MessageID.CACHE_REPOSITORY_REPLAY,
    70: MessageID.LOCK_ERROR,
    71: MessageID.LOCK_ERROR_T,
    72: MessageID.LOCK_FAILED,
    73: MessageID.LOCK_TIMEOUT,
    74: MessageID.NOT_LOCKED,
    75: MessageID.NOT_MY_LOCK,
    80: MessageID.CONNECTION_CLOSED,
    81: MessageID.CONNECTION_CLOSED_WITH_HINT,
    82: MessageID.INVALID_RPC_METHOD,
    83: MessageID.PATH_NOT_ALLOWED,
    84: MessageID.REMOTE_REPOSITORY_RPC_SERVER_OUTDATED,
    85: MessageID.UNEXPECTED_RPC_DATA_FORMAT_FROM_CLIENT,
    86: MessageID.UNEXPECTED_RPC_DATA_FORMAT_FROM_SERVER,
    87: MessageID.CONNECTION_BROKEN_WITH_HINT,
    90: MessageID.INTEGRITY_ERROR,
    91: MessageID.FILE_INTEGRITY_ERROR,
    92: MessageID.DECOMPRESSION_ERROR,
    95: MessageID.ARCHIVE_TAM_INVALID,
    96: MessageID.ARCHIVE_TAM_REQUIRED_ERROR,
    97: MessageID.TAM_INVALID,
    98: MessageID.TAM_REQUIRED_ERROR,
    99: MessageID.TAM_UNSUPPORTED_SUITE_ERROR,
    100: MessageID.FILE_CHANGED_WARNING,
    101: MessageID.INCLUDE_PATTERN_NEVER_MATCHED_WARNING,
    102: MessageID.BACKUP_ERROR,
    103: MessageID.BACKUP_RACE_CONDITION_ERROR,
    104: MessageID.BACKUP_OS_ERROR,
    105: MessageID.BACKUP_PERMISSION_ERROR,
    106: MessageID.BACKUP_IO_ERROR,
    107: MessageID.BACKUP_FILE_NOT_FOUND_ERROR,
}


class Line:
    def __init__(self, line: dict) -> None:
        """Set attributes."""
        self._line = line


class ArchiveProgressLine(Line):
    pass


class ProgressMessageLine(Line):
    @property
    def finished(self) -> bool:
        """Get finished attribute."""
        return self._line["finished"]


class ProgressPercentLine(Line):
    @property
    def finished(self) -> bool:
        """Get finished attribute."""
        return self._line["finished"]


class FileStatusLine(Line):
    pass


class LogMessageLine(Line):
    pass


class Operation:
    """Abstraction of Borg operation."""

    def __init__(self, *, progress_file: str) -> None:
        """Set attributes."""
        self.progress_file = progress_file

        self._lines = self.get_lines()

    def get_lines(
        self,
    ) -> List[Line]:
        """Get JSON lines from progress file.

        Each line is a JSON document, see https://borgbackup.readthedocs.io/en/stable/internals/frontends.html#logging
        """
        lines: List[Line] = []

        with open(self.progress_file, "r") as f:
            for _line in f.read().splitlines():
                line = json.loads(_line)

                if line["type"] == JSONLineType.ARCHIVE_PROGRESS.value:
                    lines.append(ArchiveProgressLine(line))
                elif line["type"] == JSONLineType.PROGRESS_MESSAGE.value:
                    lines.append(ProgressMessageLine(line))
                elif line["type"] == JSONLineType.PROGRESS_PERCENT.value:
                    lines.append(ProgressPercentLine(line))
                elif line["type"] == JSONLineType.FILE_STATUS.value:
                    lines.append(FileStatusLine(line))
                elif line["type"] == JSONLineType.LOG_MESSAGE.value:
                    lines.append(LogMessageLine(line))
                else:
                    raise OperationLineNotImplementedError(
                        f"Got unknown line of type '{line['type']}': '{line}'"
                    )

        return lines

    @property
    def last_line(
        self,
    ) -> Optional[Line]:
        """Get last JSON line from progress file.

        The last line contains the most recent status.
        """
        try:
            return self._lines[-1]
        except IndexError:
            # No lines yet

            return None
