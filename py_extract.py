import time
import zipfile
import tarfile
import os
from pathlib import Path
import magic
from enum import Enum, unique
import shutil
import logging
from zip_decrypter import _ZipDecrypter
import subprocess
import traceback
from logger import debug_logger

setattr(zipfile, "_ZipDecrypter", _ZipDecrypter)


class bcolors:
    OKBLUE = "\033[94m"
    OKGREEN = "\033[92m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"


class UnsafeTarfile(Exception):
    ...


@unique
class ArchiveFileType(Enum):
    TAR = "application/x-tar", "tar"
    ZIP = "application/zip", "zip"
    SEVENTH_ZIP = "application/x-7z-compressed", "7z"
    RAR = "application/x-rar", "rar"

    def __new__(cls, *args, **kwds):
        obj = object.__new__(cls)
        obj._value_ = args[0]
        return obj

    # ignore the first param since it's already set by __new__
    def __init__(self, _: str, suffix: str):
        self._suffix_ = suffix

    @property
    def suffix(self):
        return self._suffix_

    @classmethod
    def dict(cls):
        return {c.value: c for c in cls}


ARCHIVE_FILETYPE_MAP = ArchiveFileType.dict()


def load_pwd_list(path):
    with open(path, "r", encoding="utf-8") as file:
        pwd_list = [line.strip() for line in file.readlines()]
        return pwd_list


PWD_FILEPATH = "E:/linux_windows/passwd.txt"


PWD_LIST = load_pwd_list(PWD_FILEPATH)


def reprint(text: str):
    reprinted_text = "\x1b[2K\r" + text
    print(reprinted_text, end="", flush=True)


def extract_zip_retry_codec(
    archive_name: Path, out_path: Path, pwd: str | None = None
):
    codecs_list = ["utf-8", "cp936"]
    done = False
    for codec in codecs_list:
        done = extract_zip(archive_name, out_path, pwd, codec=codec)
        if done:
            break
    return done


def extract_zip(
    archive_name: Path, out_path: Path, pwd: str | None = None, codec="cp936"
):
    # https://docs.python.org/3/library/zipfile.html#zipfile.ZipFile
    # Monkey patch the decryction of zipfile with C for better performance, it
    # is about 10% slower than the 7z program in testing.
    done = False
    password = pwd.encode(codec) if pwd else None
    try:
        with zipfile.ZipFile(
            archive_name, "r", metadata_encoding=codec
        ) as myzip:
            myzip.extractall(out_path, pwd=password)
        done = True
    except RuntimeError as e:
        if "Bad password" not in repr(e):
            debug_logger.info(f"{archive_name} {e}")
            debug_logger.debug(f"{archive_name} {traceback.format_exc()}")
        if out_path.exists():
            shutil.rmtree(out_path)
    except Exception as e:
        if out_path.exists():
            shutil.rmtree(out_path)
        debug_logger.info(f"{archive_name} {e}")
        debug_logger.debug(f"{archive_name} {traceback.format_exc()}")
    return done


def extract_tar(archive_name: Path, out_path: Path, encoding="gbk"):
    # https://docs.python.org/3/library/tarfile.html
    done = False
    try:
        with tarfile.open(archive_name, "r", encoding=encoding) as tar:
            tar.getnames()
            for file in tar:
                if not is_tar_safe(file):
                    print("Warning: unsafe tarfile! extrating exits")
                    raise Exception("unsafe tarfile")
            tar.extractall(out_path)
        done = True
    except Exception as e:
        if out_path.exists():
            shutil.rmtree(out_path)
        debug_logger.info(f"{archive_name} {e}")
        debug_logger.debug(f"{archive_name} {traceback.format_exc()}")
    return done


def extract_rar(archive_name: Path, out_path: Path, pwd=None):
    # didn't find a usable python library for rar, switch to 7z program
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
            raise Exception(f"Rar extract fails\n{errs.decode()}")
    except Exception as e:
        if out_path.exists():
            shutil.rmtree(out_path)
        debug_logger.info(f"{archive_name} {e}")
        debug_logger.debug(f"{archive_name} {traceback.format_exc()}")
    return done


def extract_7z(archive_name: Path, out_path: Path, pwd=None):
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
            raise Exception(f"7z extract fails\n{errs.decode()}")
    except Exception as e:
        if out_path.exists():
            shutil.rmtree(out_path)
        debug_logger.info(f"{archive_name} {e}")
        debug_logger.debug(f"{archive_name} {traceback.format_exc()}")
    return done


def is_tar_safe(tarinfo: tarfile.TarInfo):
    # https://github.com/beatsbears/tarsafe/blob/master/tarsafe/tarsafe.py
    safe = (
        (not tarinfo.islnk())
        and (not tarinfo.issym())
        and (not tarinfo.name.startswith(os.sep))
        and not (".." in tarinfo.name)
    )
    return safe


def is_excluded_file(file: Path):
    return (
        file.suffix
        in (
            ".apk",
            ".exe",
        )
        or file.name in ("上老王论坛当老王.zip",)
        or any(
            [sub in file.name for sub in ["地址发布器", "baiduyun.p.downloading"]]
        )
    )


def extract_archive(file: Path, archive_type: ArchiveFileType, dir_level):
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
    for pwd in PWD_LIST:
        reprint(f"{indent} try passwd {pwd}")
        try:
            match archive_type:
                case ArchiveFileType.ZIP:
                    done = extract_zip_retry_codec(file, out_path, pwd)
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
    else:
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
        if file_type in ARCHIVE_FILETYPE_MAP:
            archive_type = ARCHIVE_FILETYPE_MAP[file_type]
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
