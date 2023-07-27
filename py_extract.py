"""Extract archives in target directory recursively """

import logging
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
from typing import Callable

import magic
from zip_decrypter import _ZipDecrypter

from logger import debug_logger
from rename import (
    is_unwanted_substr_present_in_filenames,
    rename_archives_in_dir,
)
from utils import (
    config,
    done_color,
    failed_color,
    filename_color,
    passwords,
    reprint,
)

setattr(zipfile, "_ZipDecrypter", _ZipDecrypter)


class UnsafeTarfile(Exception):
    ...


class ExtractFail(Exception):
    ...


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


def is_excluded_file(file: Path) -> bool:
    """check if file should be excluded, we only want the fist part of a multi-volume"""
    return (
        file.suffix in config.exclude_suffix
        or file.name in config.exclude_filename
        or any((sub in file.name for sub in config.exclude_substrings))
        or bool(
            re.search(r"part(?:[2-9]|[1-9][0-9]|100|0[2-9])\.rar", str(file))
        )
    )


def retry_with_codecs(
    extract_func: Callable[[Path, Path, str | None, str], bool]
) -> Callable[[Path, Path, str | None], bool]:
    def wrapper(
        archive_name: Path, out_path: Path, pwd: str | None = None
    ) -> bool:
        done = False
        codecs_list = config.zip_codecs
        for codec in codecs_list:
            debug_logger.debug("retry with codec: %s", codec)
            done = extract_func(archive_name, out_path, pwd, codec)
            if done:
                break
        return done

    return wrapper


@retry_with_codecs
def extract_zip(
    archive_name: Path, out_path: Path, pwd: str | None = None, codec="cp936"
) -> bool:
    # https://docs.python.org/3/library/zipfile.html#zipfile.ZipFile
    # Monkey patch the decryption of zipfile with C for better performance, it
    # is about 10% slower than the 7z program in testing.
    done = False
    password: bytes | None = pwd.encode(codec) if pwd else None
    try:
        with zipfile.ZipFile(
            archive_name, "r", metadata_encoding=codec
        ) as zip_file:
            zip_file.extractall(out_path, pwd=password)
        done = True
    except Exception as e:
        if out_path.exists():
            shutil.rmtree(out_path, onerror=remove_readonly)
        if "Bad password" not in repr(e):
            debug_logger.info("%s %s", archive_name, e)
            debug_logger.debug("%s\n%s", archive_name, traceback.format_exc())
        else:
            debug_logger.info("%s wrong password", archive_name)
    return done


def extract_tar(archive_name: Path, out_path: Path) -> bool:
    return extract_7z(archive_name, out_path)


def extract_rar(archive_name: Path, out_path: Path, pwd=None) -> bool:
    # didn't find a usable python library for rar, switch to 7z program
    # 7z reduces absolute paths to relative paths by default
    return extract_7z(archive_name, out_path, pwd)


def extract_7z(archive_name: Path, out_path: Path, pwd=None) -> bool:
    # give up py7zr and switch to 7z program
    # 7z reduces absolute paths to relative paths by default
    done = False
    try:
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
        )
        _, errs = proc.communicate()
        rc = proc.returncode
        if rc == 0:
            done = True
        else:
            raise ExtractFail(f"Extract fails\n{errs.decode()}")
    except Exception as e:
        if out_path.exists():
            shutil.rmtree(out_path, onerror=remove_readonly)
        if "Wrong password" in str(e):
            debug_logger.debug("%s Wrong password? pwd: %s", archive_name, pwd)
        else:
            debug_logger.debug("%s\n%s", archive_name, traceback.format_exc())
    return done


def extract_archive(
    file: Path, archive_type: ArchiveType, dir_level
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
            f"{'  ' * dir_level}▷ Skipping"
            f" {filename_color(str(file))} , type:"
            f" {ArchiveType.get_suffix(archive_type)}"
        )
        return out_path
    indent = "".join(["  " * dir_level, "└──"])
    print(
        f"{'  ' * dir_level}▶ Extracting"
        f" {filename_color(str(file))} , type:"
        f" {ArchiveType.get_suffix(archive_type)}"
    )
    pwd = ""
    done = False
    start = time.time()
    for pwd in passwords:
        reprint(f"{indent} try passwd {pwd}")
        try:
            match archive_type:
                case ArchiveType.ZIP:
                    done = extract_zip(file, out_path, pwd)
                case ArchiveType.TAR:
                    done = extract_tar(file, out_path)
                case ArchiveType.SEVENTH_ZIP:
                    done = extract_7z(file, out_path, pwd)
                case ArchiveType.RAR:
                    done = extract_rar(file, out_path, pwd)
            if done:
                break
        except UnsafeTarfile:
            reprint(f"{indent} unsafe tarfile\n")
            return None
        except Exception:
            continue
            # raise
    if done:
        end = time.time()
        time_cost = round(end - start)
        reprint(f"{indent} passwd {pwd} matches\n")
        print(
            f"{indent} {done_color('Done')}"
            f" {filename_color(str(file))} extracted"
            f" to {filename_color(str(out_path))}"
            f" , time cost: {time_cost}s"
        )
        return out_path
    reprint(
        f"{indent} {failed_color('Failed')}"
        f" {filename_color(str(file))} Wrong password or invalid archive?\n"
    )
    return None


def extract_archives_recursively(path: str, dir_level=0) -> None:
    # don't match files in subdirs if in root directory
    unwanted_filenames_dirs: set[Path] = set()
    files_generator = (
        Path(path).iterdir() if dir_level == 0 else Path(path).glob("**/*")
    )

    for file in files_generator:
        if (not file.is_file()) or is_excluded_file(file):
            continue
        file_type = magic.from_buffer(open(file, "rb").read(2048), mime=True)
        try:
            archive_type = ArchiveType(file_type)
        except ValueError:
            pass
        else:
            out_dir = extract_archive(file, archive_type, dir_level)
            if out_dir:
                extract_archives_recursively(
                    out_dir.as_posix(), dir_level=dir_level + 1
                )
            else:
                if is_unwanted_substr_present_in_filenames(file.parent):
                    unwanted_filenames_dirs.add(file.parent)
    if unwanted_filenames_dirs:
        handle_unwanted_filenames(unwanted_filenames_dirs)


def handle_unwanted_filenames(unwanted_filenames_dirs: set[Path]) -> None:
    print(
        failed_color(
            "\nSome unwanted sub-strings are present in"
            " filenames within following dirs:"
        )
    )
    for d in unwanted_filenames_dirs:
        print(f"{filename_color(str(d))}")
    sys.stdout.write("\nDo you want to rename them? [y/n]")
    choice = input().lower()
    if choice in ["y", "Y"]:
        for d in unwanted_filenames_dirs:
            rename_archives_in_dir(str(d))
        sys.stdout.write("\nDo you want to retry extracting? [y/n]")
        choice = input().lower()
        if choice in ["y", "Y"]:
            for d in unwanted_filenames_dirs:
                extract_archives_recursively(str(d), dir_level=0)


def main() -> None:
    debug_logger.setLevel(logging.DEBUG)
    target_dir = config.target_directory
    extract_archives_recursively(target_dir)


if __name__ == "__main__":
    main()
