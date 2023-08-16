import itertools
from typing import TextIO


def output_same_line(text: str) -> None:
    """Output to the same line"""
    print("\x1b[2K\r" + text, end="", flush=True)


class BColors:
    OK_BLUE = "\033[94m"
    OK_GREEN = "\033[92m"
    FAIL = "\033[91m"
    END = "\033[0m"


def filename_color(text: str) -> str:
    return f"{BColors.OK_BLUE}{text}{BColors.END}"


def done_color(text: str) -> str:
    return f"{BColors.OK_GREEN}{text}{BColors.END}"


def failed_color(text: str) -> str:
    return f"{BColors.FAIL}{text}{BColors.END}"


def load_passwords(pwd_file: TextIO) -> list[str]:
    """passwords file should be like:
    ```
    password_one_in_second_group
    password_two_in_second_group

    password_one_in_first_group
    password_two_in_first_group
    ```
    """
    lines = [line.strip() for line in pwd_file.readlines()]

    def strip_list(to_strip, rem):
        to_strip = list(itertools.dropwhile(lambda x: x == rem, to_strip))
        to_strip = list(itertools.dropwhile(lambda x: x == rem, to_strip[::-1]))
        return to_strip[::-1]

    lines = strip_list(lines, "")
    delimiter = ""
    if delimiter not in lines:
        return lines
    groups = [
        list(y)
        for x, y in itertools.groupby(lines, lambda z: z == delimiter)
        if not x
    ]
    return list(itertools.chain.from_iterable(groups[::-1]))
