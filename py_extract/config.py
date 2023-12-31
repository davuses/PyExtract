import dataclasses
from pathlib import Path

import tomllib

from .exceptions import (
    ConfigNotFound,
    InvalidConfig,
    InvalidPath,
)
from .utils import load_passwords


def is_list_of_str(list_to_test: list[str]):
    if not isinstance(list_to_test, list):
        return False
    if list_to_test and not all(
        map(lambda x: isinstance(x, str), list_to_test)
    ):
        return False
    return True


@dataclasses.dataclass
class PyExtractConfig:
    zip_metadata_encoding: list[str]
    exclude_suffix: list[str]
    exclude_filename: list[str]
    exclude_substrings: list[str]
    rename_substrings: list[str]
    target_directory: str
    passwords: list[str]
    password_path: str
    language: str
    auto_rename: bool
    logging_level: str
    config_path: str

    def __post_init__(self) -> None:
        assert is_list_of_str(self.zip_metadata_encoding)
        assert is_list_of_str(self.exclude_suffix)
        assert is_list_of_str(self.exclude_filename)
        assert is_list_of_str(self.exclude_substrings)
        assert is_list_of_str(self.rename_substrings)
        assert isinstance(self.target_directory, str)
        assert isinstance(self.language, str)
        assert isinstance(self.auto_rename, bool)
        assert isinstance(self.logging_level, str)
        if not Path(self.target_directory).exists():
            raise InvalidPath(
                f"target directory {self.target_directory} doesn't exist"
            )
        assert is_list_of_str(self.passwords)

        self.rename_substrings = sorted(self.rename_substrings, reverse=True)


POSSIBLE_CONFIG_PATHS = [
    "./config/py_extract_config.toml",
    "./py_extract_config.toml",
]
CONFIG_NOT_FOUND_ERROR_MSG = f"""\
config file should be found in one of these paths: {POSSIBLE_CONFIG_PATHS},\
 or you can specify the path with --config option"""


def load_config(config_path: str | None = None) -> PyExtractConfig:
    if not config_path:
        for p in POSSIBLE_CONFIG_PATHS:
            if Path(p).is_file():
                config_path = p
                break
        else:
            raise ConfigNotFound(CONFIG_NOT_FOUND_ERROR_MSG)
    else:
        if not Path(config_path).is_file():
            raise ConfigNotFound(f"cannot find the config file: {config_path}")
    config_path = str(Path(config_path).resolve())
    with open(config_path, mode="rb") as fp:
        toml_config = tomllib.load(fp)
        match toml_config:
            case {
                "zip_metadata_encoding": list() as zip_metadata_encoding,
                "language": str() as language,
                "auto_rename": bool() as auto_rename,
                "logging_level": str() as logging_level,
                "path": {
                    "target_directory": str() as target_directory,
                    "password_path": str() as password_path,
                },
                "exclude": {
                    "suffixes": list() as suffixes,
                    "filenames": list() as filenames,
                    "substrings": list() as substrings,
                },
                "rename": {"substrings": list() as rename_substrings},
            }:
                if not Path(password_path).exists():
                    raise InvalidPath(
                        f"password file  {password_path} doesn't exist"
                    )
                with open(password_path, "r", encoding="utf-8") as pwd_file:
                    passwords = load_passwords(pwd_file)
                extract_config = PyExtractConfig(
                    zip_metadata_encoding=zip_metadata_encoding,
                    exclude_suffix=suffixes,
                    exclude_filename=filenames,
                    exclude_substrings=substrings,
                    rename_substrings=rename_substrings,
                    target_directory=target_directory,
                    passwords=passwords,
                    password_path=password_path,
                    language=language,
                    auto_rename=auto_rename,
                    logging_level=logging_level,
                    config_path=config_path,
                )
            case _:
                raise InvalidConfig(
                    "invalid configuration, please check"
                    " ./config/example_config.toml for a valid configuration"
                )
        return extract_config
