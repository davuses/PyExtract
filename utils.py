import itertools


def load_pwd_list(path: str = "E:/linux_windows/passwd.txt") -> list[str]:
    with open(path, "r", encoding="utf-8") as file:
        pwd_list = [line.strip() for line in file.readlines()]
    delimiter = "------"
    pwds_second, pwds_first = [
        list(y)
        for x, y in itertools.groupby(pwd_list, lambda z: z == delimiter)
        if not x
    ]
    ranked_pwd_list = pwds_first + pwds_second
    return ranked_pwd_list


def reprint(text: str) -> None:
    """reprint/overwrite a line"""
    reprinted_text = "\x1b[2K\r" + text
    print(reprinted_text, end="", flush=True)


class bcolors:
    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"


def filename_color(text: str) -> str:
    return f"{bcolors.OKBLUE}{text}{bcolors.ENDC}"


def done_color(text: str) -> str:
    return f"{bcolors.OKGREEN}{text}{bcolors.ENDC}"


def failed_color(text: str) -> str:
    return f"{bcolors.FAIL}{text}{bcolors.ENDC}"
