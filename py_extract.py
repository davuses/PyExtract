"""Extract archives in target directory recursively """

import time
from typing import Callable
import zipfile
import tarfile
import os
from pathlib import Path
from enum import Enum, unique
import shutil
import logging
import subprocess
import traceback
import magic
from pwd_loader import load_pwd_list
from zip_decrypter import _ZipDecrypter
from logger import debug_logger

setattr(zipfile, "_ZipDecrypter", _ZipDecrypter)


class bcolors:
    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"


class UnsafeTarfile(Exception):
    ...


class ExtractFail(Exception):
    ...


@unique
class ArchiveFileType(str, Enum):
    suffix: str

    def __new__(cls, value, suffix):
        obj = str.__new__(cls, [value])
        obj._value_ = value
        obj.suffix = suffix
        return obj

    TAR = ("application/x-tar", "tar")
    ZIP = ("application/zip", "zip")
    SEVENTH_ZIP = ("application/x-7z-compressed", "7z")
    RAR = ("application/x-rar", "rar")


def reprint(text: str) -> None:
    """reprint/overwrite a line"""
    reprinted_text = "\x1b[2K\r" + text
    print(reprinted_text, end="", flush=True)


def retry_with_codecs(
    extract_func: Callable[[Path, Path, str | None, str], bool]
) -> Callable[[Path, Path, str | None], bool]:
    def wrapper(
        archive_name: Path, out_path: Path, pwd: str | None = None
    ) -> bool:
        done = False
        codecs_list: list[str] = [
            "cp936",
            "utf-8",
        ]
        for codec in codecs_list:
            # print(codec)
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
    # Monkey patch the decryction of zipfile with C for better performance, it
    # is about 10% slower than the 7z program in testing.
    done = False
    password: bytes | None = pwd.encode(codec) if pwd else None
    try:
        with zipfile.ZipFile(
            archive_name, "r", metadata_encoding=codec
        ) as myzip:
            myzip.extractall(out_path, pwd=password)
        done = True
    except RuntimeError as e:
        if "Bad password" not in repr(e):
            debug_logger.info("%s %s", archive_name, e)
            debug_logger.debug("%s %s", archive_name, traceback.format_exc())
        if out_path.exists():
            shutil.rmtree(out_path)
    except Exception as e:
        if out_path.exists():
            shutil.rmtree(out_path)
        debug_logger.info("%s %s", archive_name, e)
        debug_logger.debug("%s %s", archive_name, traceback.format_exc())
    return done


def extract_tar(archive_name: Path, out_path: Path, encoding="gbk") -> bool:
    # https://docs.python.org/3/library/tarfile.html
    done = False
    try:
        with tarfile.open(archive_name, "r", encoding=encoding) as tar:
            tar.getnames()
            for file in tar:
                if not is_tar_safe(file):
                    print("Warning: unsafe tarfile! extrating exits")
                    raise UnsafeTarfile("unsafe tarfile")
            tar.extractall(out_path)
        done = True
    except Exception as e:
        if out_path.exists():
            shutil.rmtree(out_path)
        debug_logger.info("%s %s", archive_name, e)
        debug_logger.debug("%s %s", archive_name, traceback.format_exc())
    return done


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
            shutil.rmtree(out_path)
        if "Wrong password" in str(e):
            debug_logger.debug("%s Wrong password? pwd: %s", archive_name, pwd)
        else:
            debug_logger.debug("%s %s", archive_name, traceback.format_exc())
    return done


def is_tar_safe(tarinfo: tarfile.TarInfo) -> bool:
    # https://github.com/beatsbears/tarsafe/blob/master/tarsafe/tarsafe.py
    safe = (
        (not tarinfo.islnk())
        and (not tarinfo.issym())
        and (not tarinfo.name.startswith(os.sep))
        and not (".." in tarinfo.name)
    )
    return safe


def is_excluded_file(file: Path) -> bool:
    return (
        file.suffix
        in (
            ".apk",
            ".exe",
        )
        or file.name in ("上老王论坛当老王.zip",)
        or any(
            (sub in file.name for sub in ["地址发布器", "baiduyun.p.downloading"])
        )
    )


def extract_archive(
    file: Path, archive_type: ArchiveFileType, dir_level
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
            f" {bcolors.OKBLUE}{file}{bcolors.ENDC} , type:"
            f" {archive_type.suffix}"
        )
        return out_path
    indent = "".join(["  " * dir_level, "└──"])
    print(
        f"{'  ' * dir_level}▶ Extracting"
        f" {bcolors.OKBLUE}{file}{bcolors.ENDC} , type:"
        f" {archive_type.suffix}"
    )
    pwd = ""
    done = False
    start = time.time()
    for pwd in load_pwd_list():
        reprint(f"{indent} try passwd {pwd}")
        try:
            match archive_type:
                case ArchiveFileType.ZIP:
                    done = extract_zip(file, out_path, pwd)
                case ArchiveFileType.TAR:
                    done = extract_tar(file, out_path)
                case ArchiveFileType.SEVENTH_ZIP:
                    done = extract_7z(file, out_path, pwd)
                case ArchiveFileType.RAR:
                    done = extract_rar(file, out_path, pwd)
                case _:
                    raise RuntimeError("Impossible!")
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
            f"{indent} {bcolors.OKGREEN}Done{bcolors.ENDC}"
            f" {bcolors.OKBLUE}{file}{bcolors.ENDC} extracted"
            f" to {bcolors.OKBLUE}{out_path}{bcolors.ENDC}"
            f" , time cost: {time_cost}s"
        )
        return out_path
    reprint(
        f"{indent} {bcolors.FAIL}Failed{bcolors.ENDC},"
        f" {bcolors.OKBLUE}{file}{bcolors.ENDC} maybe no password match\n"
    )
    return None


def extract_archives_recursively(path: str, dir_level=0) -> None:
    # don't match files in subdirs if in root directory
    files_generator = (
        Path(path).iterdir() if dir_level == 0 else Path(path).glob("**/*")
    )

    for file in files_generator:
        if (not file.is_file()) or is_excluded_file(file):
            continue
        file_type = magic.from_buffer(open(file, "rb").read(2048), mime=True)
        try:
            archive_type = ArchiveFileType(file_type)  # type: ignore
        except ValueError:
            pass
        else:
            out_dir = extract_archive(file, archive_type, dir_level)
            if out_dir:
                extract_archives_recursively(
                    out_dir.as_posix(), dir_level=dir_level + 1
                )


if __name__ == "__main__":
    debug_logger.setLevel(logging.DEBUG)
    # extract_archive(Path("新建文件夹 (3).rar"), ArchiveFileType.RAR, dir_level=0)
    target_dir = "G:/BaiduNet/"
    extract_archives_recursively(target_dir)
