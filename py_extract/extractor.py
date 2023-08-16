"""Extract archives in target directory recursively """

from logging import Logger
import os
import re
import shutil
import stat
import subprocess
import sys
import time
import traceback
import zipfile
from enum import Enum, unique
from pathlib import Path
import builtins


import magic
from .file_renaming import (
    RenameFileHandler,
)
from .utils import (
    done_color,
    failed_color,
    filename_color,
    output_same_line,
)
from .config import PyExtractConfig

# from .config_parser import py_extract_config
from .zip_decrypter import _ZipDecrypter  # pylint: disable=E0611

setattr(zipfile, "_ZipDecrypter", _ZipDecrypter)


class UnsafeTarfile(Exception):
    ...


class SevenZipExtractFail(Exception):
    ...


class SevenZipCmdNotFound(Exception):
    ...


class ExtractStatusCode(Enum):
    SUCCESS = 0
    WRONG_PASSWORD = 1
    FAIL = 2
    WRONG_ENCODING = 3


@unique
class ArchiveType(Enum):
    TAR = "application/x-tar"
    ZIP = "application/zip"
    SEVENTH_ZIP = "application/x-7z-compressed"
    RAR = "application/x-rar"

    @classmethod
    def get_suffix(cls, archive_type: "ArchiveType") -> str:
        suffix_mapping = {
            cls.TAR: "tar",
            cls.ZIP: "zip",
            cls.SEVENTH_ZIP: "7z",
            cls.RAR: "rar",
        }
        return suffix_mapping[archive_type]


def remove_readonly(func, path, _) -> None:
    os.chmod(path, stat.S_IWRITE)
    func(path)


class PyExtractor:
    def __init__(self, config: PyExtractConfig, logger: Logger) -> None:
        self.config = config
        self.logger = logger
        self.file_rename = RenameFileHandler(
            unwanted_substrings=config.rename_substrings,
            auto_rename=config.auto_rename,
            logger=logger,
        )

    def run(
        self,
    ):
        target_dir = self.config.target_directory
        print(_("target directory"), ":", filename_color(target_dir), "\n")
        self.extract_archives_recursively(target_dir)

    def is_excluded_file(self, file: Path) -> bool:
        """test if file should be excluded"""
        return (
            file.suffix in self.config.exclude_suffix
            or file.name in self.config.exclude_filename
            or any((sub in file.name for sub in self.config.exclude_substrings))
            or bool(
                re.search(
                    r"part(?:[2-9]|[1-9][0-9]|100|0[2-9])\.rar", str(file)
                )
            )
        )

    def extract_zip(
        self,
        archive_name: Path,
        out_path: Path,
        pwd: str | None = None,
        default_encoding="utf-8",
    ):
        # https://docs.python.org/3/library/zipfile.html#zipfile.ZipFile
        # Monkey patch the decryption of zipfile with C for better performance, it
        # is about 10% slower than the 7z program in testing.
        additional_encodings = self.config.zip_metadata_encoding
        additional_encodings.append(default_encoding)
        for encoding in additional_encodings:
            self.logger.info("try encoding: %s", encoding)
            password: bytes | None = pwd.encode(encoding) if pwd else None
            try:
                with zipfile.ZipFile(
                    archive_name, "r", metadata_encoding=encoding
                ) as zip_file:
                    zip_file.extractall(out_path, pwd=password)
                    return ExtractStatusCode.SUCCESS
            except Exception as exc:
                if out_path.exists():
                    shutil.rmtree(out_path, onerror=remove_readonly)
                if isinstance(exc, NotImplementedError):
                    # some algorithms are not supported by zipfile
                    return self.extract_7z(archive_name, out_path, pwd=pwd)
                if isinstance(exc, UnicodeDecodeError):
                    self.logger.info(
                        "%s cannot decode %s", encoding, archive_name
                    )
                    continue
                if "Bad password" in repr(exc):
                    self.logger.info("%s wrong password", archive_name)
                    return ExtractStatusCode.WRONG_PASSWORD
                traceback_info = traceback.format_exc()
                self.logger.error("%s\n%s", archive_name, traceback_info)
                return ExtractStatusCode.FAIL
        self.logger.error(
            "None of encodings %s can decode %s",
            additional_encodings,
            archive_name,
        )
        return ExtractStatusCode.WRONG_ENCODING

    def extract_tar(self, archive_name: Path, out_path: Path):
        return self.extract_7z(archive_name, out_path)

    def extract_rar(self, archive_name: Path, out_path: Path, pwd=None):
        # didn't find a usable python library for rar, switch to 7z program
        # 7z reduces absolute paths to relative paths by default
        return self.extract_7z(archive_name, out_path, pwd)

    def extract_7z(self, archive_name: Path, out_path: Path, pwd=None):
        try:
            assert shutil.which("7z")
            cmd = [
                "7z",
                "x",
                f"-p{pwd if pwd else ''}",
                archive_name.as_posix(),
                f"-o{out_path.as_posix()}",
            ]
            proc = subprocess.Popen(
                cmd,
                shell=False,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
            _stdout, errs = proc.communicate()
            rc = proc.returncode
            if rc != 0:
                raise SevenZipExtractFail(f"Extract fails, {errs}")
        except Exception as exc:
            if out_path.exists():
                shutil.rmtree(out_path, onerror=remove_readonly)
            if isinstance(exc, AssertionError):
                self.logger.error("7z command not found")
                raise SevenZipCmdNotFound from exc
            if "Wrong password" in str(exc):
                self.logger.info(
                    "%s , Wrong password: %s", archive_name, pwd
                )
                return ExtractStatusCode.WRONG_PASSWORD
            self.logger.error("%s\n%s", archive_name, traceback.format_exc())
            return ExtractStatusCode.FAIL
        return ExtractStatusCode.SUCCESS

    def extract_archive(
        self, file: Path, archive_type: ArchiveType, dir_level
    ) -> Path | None:
        """return out_path if done is True, else return None

        Args:
            file (Path):
            archive_type (ArchiveFileType)
        Returns:
            out_path (Path) | None
        """
        target_out_dir = f"{file}_out"
        out_path = Path(target_out_dir)
        if out_path.exists():
            print(
                f"{'  ' * dir_level}▷ {_('Skipping')}"
                f" {filename_color(str(file))} , {_('type')}:"
                f" {ArchiveType.get_suffix(archive_type)}"
            )
            return out_path
        indent = "".join(["  " * dir_level, "└──"])
        print(
            f"{'  ' * dir_level}▶ {_('Extracting')}"
            f" {filename_color(str(file))} , {_('type')}:"
            f" {ArchiveType.get_suffix(archive_type)}"
        )
        pwd = ""
        start = time.time()
        passwords_list = self.config.passwords
        failed_msg = ""
        status_code = ExtractStatusCode.FAIL
        if not passwords_list:
            passwords_list = [None]
        for pwd in passwords_list:
            output_same_line(f"{indent} {_('try passwd')} {pwd}")
            try:
                match archive_type:
                    case ArchiveType.ZIP:
                        status_code = self.extract_zip(file, out_path, pwd)
                    case ArchiveType.TAR:
                        status_code = self.extract_tar(file, out_path)
                    case ArchiveType.SEVENTH_ZIP:
                        status_code = self.extract_7z(file, out_path, pwd)
                    case ArchiveType.RAR:
                        status_code = self.extract_rar(file, out_path, pwd)
                    case _:
                        raise AssertionError("Not going to happen")
                match status_code:
                    case ExtractStatusCode.WRONG_PASSWORD:
                        continue
                    case _:
                        break

            except SevenZipCmdNotFound:
                failed_msg = _(
                    "Din't find 7z command, please make sure 7z is"
                    " installed and available in PATH env"
                )
                break
        else:
            failed_msg = _("None of the passwords can decrypt the archive")
        if status_code == ExtractStatusCode.SUCCESS:
            end = time.time()
            time_cost = round(end - start)
            output_same_line(f"{indent} {_('passwd')} {pwd} {_('matches')}\n")
            print(
                f"{indent} {done_color(_('Done'))}"
                f" {filename_color(str(file))} {_('extracted to')}"
                f" {filename_color(str(out_path))}"
                f" , {_('time cost')}: {time_cost}s"
            )
            self.logger.info("%s is extracted to %s", file, out_path)
            return out_path
        if status_code == ExtractStatusCode.WRONG_ENCODING:
            failed_msg = _("None of the encodings can decode the archive")
        if not failed_msg:
            failed_msg = _("Invalid archive")
        output_same_line(
            f"{indent} {failed_color(_('Failed'))}"
            f" {filename_color(str(file))} {failed_color(failed_msg)}\n"
        )
        return None

    def extract_archives_recursively(
        self, target_dir: str | Path, dir_level=0
    ) -> None:
        # don't match files in subdirs if in root directory
        dirs_to_rename_files: set[Path] = set()
        files_generator = (
            Path(target_dir).iterdir()
            if dir_level == 0
            else Path(target_dir).glob("**/*")
        )

        for file in files_generator:
            if (not file.is_file()) or self.is_excluded_file(file):
                continue
            file_type = magic.from_buffer(
                open(file, "rb").read(2048), mime=True
            )
            try:
                archive_type = ArchiveType(file_type)
            except ValueError:
                pass
            else:
                out_dir = self.extract_archive(file, archive_type, dir_level)
                if out_dir:
                    self.extract_archives_recursively(
                        out_dir.as_posix(), dir_level=dir_level + 1
                    )
                else:
                    if self.file_rename.has_unwanted_substrings_in_filenames(
                        file.parent
                    ):
                        dirs_to_rename_files.add(file.parent)
        if dirs_to_rename_files:
            self.file_rename.rename_files_in_dirs(dirs_to_rename_files)
            if self.file_rename.auto_rename:
                choice = "y"
                print(f"\n{_('retry extracting')}")
            else:
                sys.stdout.write(
                    f"\n{_('Do you want to retry extracting')}? [y/n]"
                )
                choice = input().lower()
            if choice in ["y", "Y"]:
                for d in dirs_to_rename_files:
                    self.extract_archives_recursively(d, dir_level=0)


if __name__ == "__main__":
    _ = builtins.__dict__["_"]
