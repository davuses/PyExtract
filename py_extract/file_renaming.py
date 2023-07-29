import logging
import sys
from pathlib import Path

from .logging_utils import my_logger
from .utils import config, filename_color

UNWANTED_SUBSTRINGS = config.rename_substrings


def has_unwanted_substrings_in_filenames(target_dir: Path) -> bool:
    for path in Path(target_dir).iterdir():
        if path.is_dir():
            continue
        filename = path.name
        if any((substr in filename for substr in UNWANTED_SUBSTRINGS)):
            return True
    return False


def rename_archives_in_dir(target_dir: Path | str) -> None:
    for path in Path(target_dir).iterdir():
        if path.is_dir():
            continue
        filename = path.name
        newname, oldname = "", filename
        for substr in UNWANTED_SUBSTRINGS:
            # print("substr", substr)
            if substr in filename:
                newname = filename.replace(substr, "")
                break
                # print("newname", newname)
        else:
            # substr not in filename, skip
            continue
        sys.stdout.write(
            "Do you want to rename"
            f" {filename_color(str(path.with_name(oldname)))} to"
            f" {filename_color(str(path.with_name(newname)))} ? [y/n]"
        )
        choice = input().lower()
        if choice in ["y", "Y"]:
            new_path = path.rename(path.with_name(newname))
            my_logger.info("rename %s to %s", path, new_path)
            print("rename done")
        else:
            print("skip rename")


def main() -> None:
    target_dir = sys.argv[1]
    my_logger.setLevel(logging.DEBUG)
    rename_archives_in_dir(target_dir=target_dir)


if __name__ == "__main__":
    main()
