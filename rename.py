import logging
from pathlib import Path
from logger import debug_logger


def rename_archives(target_dir):
    for path in Path(target_dir).iterdir():
        if path.is_dir():
            continue
        filename = path.name
        unwanted_substrs = ["删除", "删"]
        newname, oldname = "", filename
        if any([substr in filename for substr in unwanted_substrs]):
            for substr in unwanted_substrs:
                # print("substr", substr)
                newname = filename.replace(substr, "")
                filename = newname
                # print("newname", newname)
            input(
                f"Do you want to rename {path.with_name(oldname)} to"
                f" {path.with_name(filename)} ?"
            )
            new_path = path.rename(path.with_name(filename))
            debug_logger.info(f"rename {path} to {new_path}")


if __name__ == "__main__":
    target_dir = r"G:\BaiduNet\奥yi.7z.001_out\2opreg\1\2\3\4\5"
    debug_logger.setLevel(logging.DEBUG)
    rename_archives(target_dir=target_dir)
