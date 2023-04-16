import dataclasses
import itertools
import os

import yaml


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


class InvalidConfig(Exception):
    ...


class InvalidPath(Exception):
    ...


@dataclasses.dataclass
class ExtractConfig:
    zip_codecs: list[str]
    exclude_suffix: list[str]
    exclude_filename: list[str]
    exclude_substrings: list[str]
    rename_substrings: list[str]
    target_directory: str
    password_filepath: str

    def __post_init__(self) -> None:
        assert isinstance(self.zip_codecs, list), "Invalid config file"
        assert isinstance(self.exclude_suffix, list), "Invalid config file"
        assert isinstance(self.exclude_filename, list), "Invalid config file"
        assert isinstance(self.exclude_substrings, list), "Invalid config file"
        assert isinstance(self.rename_substrings, list), "Invalid config file"
        assert isinstance(self.target_directory, str), "Invalid config file"
        if not os.path.exists(self.target_directory):
            raise InvalidPath("target directory doesn't exist")
        assert isinstance(self.password_filepath, str), "Invalid config file"
        if not os.path.exists(self.password_filepath):
            raise InvalidPath("password file doesn't exist")

        self.rename_substrings = sorted(self.rename_substrings, reverse=True)


def load_config() -> ExtractConfig:
    with open("config.yaml", "r", encoding="utf-8") as file:
        yaml_config = yaml.safe_load(file)
        try:
            extract_config = ExtractConfig(**yaml_config)
        except (TypeError, AssertionError) as exc:
            raise InvalidConfig("config file is invalid") from exc

        return extract_config


config = load_config()


def load_pwd_list(path: str) -> list[str]:
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


password_list = load_pwd_list(config.password_filepath)
