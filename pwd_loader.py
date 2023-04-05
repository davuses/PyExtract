import itertools


def load_pwd_list(path: str = "E:/linux_windows/passwd.txt"):
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


if __name__ == "__main__":
    load_pwd_list()
