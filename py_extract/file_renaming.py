import builtins
from logging import Logger
import sys
from pathlib import Path

from .utils import filename_color


class RenameFileHandler:
    def __init__(
        self,
        unwanted_substrings: list[str],
        auto_rename: bool,
        logger: Logger,
    ) -> None:
        self.unwanted_substrings = unwanted_substrings
        self.auto_rename = auto_rename
        self.logger = logger

    def has_unwanted_substrings_in_filenames(self, target_dir: Path) -> bool:
        for path in Path(target_dir).iterdir():
            if path.is_dir():
                continue
            filename = path.name
            if any((substr in filename for substr in self.unwanted_substrings)):
                return True
        return False

    def display_files_to_rename(self, target_dir: Path):
        print(filename_color(str(target_dir)))
        for path in Path(target_dir).iterdir():
            if path.is_dir():
                continue
            filename = path.name
            for substr in self.unwanted_substrings:
                if substr in filename:
                    print(filename_color("  " + filename))
                    break

    def rename_files_in_dir(self, target_dir: Path | str) -> None:
        _ = builtins.__dict__["_"]
        for path in Path(target_dir).iterdir():
            if path.is_dir():
                continue
            filename = path.name
            newname, oldname = "", filename
            for substr in self.unwanted_substrings:
                if substr in filename:
                    newname = filename.replace(substr, "")
                    break
            else:
                # substr not in filename, skip
                continue
            sys.stdout.write(
                f"{_('Do you want to rename')}"
                f" {filename_color(str(path.with_name(oldname)))} {_('to')}"
                f" {filename_color(str(path.with_name(newname)))} ? [y/n]"
            )
            if self.auto_rename:
                choice = "y"
                sys.stdout.write("\n")
            else:
                choice = input().lower()
            if choice in ["y", "Y"]:
                new_path = path.rename(path.with_name(newname))
                self.logger.info("rename %s to %s", path, new_path)
                print(_("rename done"))
            else:
                print(_("skip rename"))

    def rename_files_in_dirs(self, dirs: set[Path]) -> None:
        if self.auto_rename:
            choice = "y"
            print()
        else:
            print(
                f"\n{_('Some files probably need to be renamed in these directories')}:"
            )
            for d in dirs:
                self.display_files_to_rename(d)
            sys.stdout.write(f"\n{_('Take a look')}? [y/n]")
            choice = input().lower()
        if choice in ["y", "Y"]:
            for d in dirs:
                self.rename_files_in_dir(d)


if __name__ == "__main__":
    _ = builtins.__dict__["_"]
