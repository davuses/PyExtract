import shutil
import subprocess
import sys
from pathlib import Path

import toml

from py_extract import create_py_extractor

FIRST_PASSWORD = "password1"

SECOND_PASSWORD = "password2"

PASSWORDS_FILE_CONTENT = f"""\
{FIRST_PASSWORD}

{SECOND_PASSWORD}
"""


def test_7z_command():
    assert bool(shutil.which("7z"))


def test_py_extract(tmp_path: Path):
    tmp_dir = tmp_path / "dir"
    tmp_dir.mkdir(exist_ok=True)

    test_files = ["file1.txt", "file2.txt", "file3.txt"]

    make_split_archives(tmp_dir, test_files)

    passwords_path = tmp_path / "passwords.txt"
    with open(passwords_path, "w", encoding="utf-8") as test_pwd_file:
        test_pwd_file.write(PASSWORDS_FILE_CONTENT)
    with open(
        "./config/example_config.toml", "r", encoding="utf-8"
    ) as example_config_file:
        test_config = toml.load(example_config_file)
        test_config["path"]["target_directory"] = str(tmp_dir)
        test_config["path"]["password_path"] = str(passwords_path)
        test_config["rename"]["substrings"] = ["删除", "删", "删我"]
        test_config["auto_rename"] = True

    test_config_path = tmp_path / "test_config.toml"
    with open(test_config_path, "w", encoding="utf-8") as test_config_file:
        toml.dump(test_config, test_config_file)

    sys.argv[1:] = ["--config", str(test_config_path)]

    py_extractor = create_py_extractor()
    py_extractor.run()

    for filename in test_files:
        assert (
            tmp_dir
            / f"./nested_archive.7z.001_out/archive.7z.001_out/{filename}"
        ).is_file()


def make_split_archives(tmp_dir, test_files):
    test_filepaths = [tmp_dir / filename for filename in test_files]

    for p in test_filepaths:
        with open(p, mode="wb") as f:
            f.truncate(1024 * 1024 * 10)

    archive_name = "archive.7z"

    with subprocess.Popen(
        [
            "7z",
            "a",
            f"-p{FIRST_PASSWORD}",
            "-v2k",
            "-mx9",
            "-mhe=on",
            archive_name,
            *test_files,
        ],
        shell=False,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=tmp_dir,
    ) as proc:
        stdout, _stderr = proc.communicate()
        assert "Everything is Ok" in stdout

    for p in test_filepaths:
        p.unlink()

    first_volume_path = tmp_dir / "archive.7z.001"
    first_volume_path.rename(first_volume_path.with_name("archive.7z.删除001"))

    archives_names = [
        "archive.7z.删除001",
        "archive.7z.002",
        "archive.7z.003",
    ]
    archive_paths = [tmp_dir / name for name in archives_names]

    with subprocess.Popen(
        [
            "7z",
            "a",
            f"-p{SECOND_PASSWORD}",
            "-v2k",
            "-mx9",
            "-mhe=on",
            "nested_archive.7z",
            *archives_names,
        ],
        shell=False,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=tmp_dir,
    ) as proc:
        stdout, _stderr = proc.communicate()
        assert "Everything is Ok" in stdout

    nested_archive_first_volume = tmp_dir / "nested_archive.7z.001"
    nested_archive_first_volume.rename(
        nested_archive_first_volume.with_name("nested_archive.7z.删001")
    )
    nested_archive_second_volume = tmp_dir / "nested_archive.7z.002"
    nested_archive_second_volume.rename(
        nested_archive_second_volume.with_name("nested_archive.7z.删我002")
    )
    for p in archive_paths:
        p.unlink()
