from cyberfusion.BorgSupport.exceptions import (
    LoggedCommandFailedError,
    RegularCommandFailedError,
)


def test_LoggedCommandFailedError_string():
    COMMAND = ["foobar"]
    RETURN_CODE = 1
    OUTPUT_FILE_PATH = "/tmp/foobar"

    assert (
        str(
            LoggedCommandFailedError(
                command=COMMAND,
                output_file_path=OUTPUT_FILE_PATH,
                return_code=RETURN_CODE,
            )
        )
        == f"Command '{COMMAND}' failed with RC {RETURN_CODE}. Output was logged to {OUTPUT_FILE_PATH}"
    )


def test_RegularCommandFailedError_string():
    COMMAND = ["foobar"]
    RETURN_CODE = 1
    STDERR = "foobar"

    assert (
        str(
            RegularCommandFailedError(
                command=COMMAND, stderr=STDERR, return_code=RETURN_CODE
            )
        )
        == f"Command '{COMMAND}' failed with RC {RETURN_CODE}. Stderr:\n\n{STDERR}"
    )
