import os
import shutil
import subprocess
import sys
from pathlib import Path

import toml

from py_extract import create_py_extractor


def test_py_extract():
    temp_dir_path = Path("./temp")
    try:
        shutil.rmtree(temp_dir_path)
    except FileNotFoundError:
        pass
    temp_dir_path.mkdir(exist_ok=True)

    test_filenames = ["file1.txt", "file2.txt", "file3.txt"]

    test_filepaths = [
        temp_dir_path.joinpath(filename) for filename in test_filenames
    ]

    for _p in test_filepaths:
        with open(_p, mode="wb") as f:
            f.truncate(1024 * 1024 * 10)

    archive_name = "archive.7z"
    archive_path = temp_dir_path.joinpath(archive_name)
    test_password = "password"
    cmd = [
        "7z",
        "a",
        f"-p{test_password}",
        "-v2k",
        "-mx9",
        "-mhe=on",
        str(archive_path),
    ]
    cmd.extend([str(p) for p in test_filepaths])

    print(cmd)
    with subprocess.Popen(
        cmd,
        shell=False,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ) as proc:
        # print()
        stdout, stderr = proc.communicate()
        print(stdout, stderr)

    first_volume_path = temp_dir_path.joinpath("archive.7z.001")
    first_volume_path.rename(first_volume_path.with_name("archive.7z.删除001"))

    test_password2 = "password2"
    nested_test_filenames = [
        "archive.7z.删除001",
        "archive.7z.002",
        "archive.7z.003",
    ]
    nested_test_filepaths = [
        str(temp_dir_path.joinpath(filename))
        for filename in nested_test_filenames
    ]

    with subprocess.Popen(
        [
            "7z",
            "a",
            f"-p{test_password2}",
            "-v2k",
            "-mx9",
            "-mhe=on",
            str(temp_dir_path.joinpath("nested_archive.7z")),
        ]
        + nested_test_filepaths,
        shell=False,
        encoding="utf-8",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ) as proc:
        # print()
        stdout, stderr = proc.communicate()
        print(stdout, stderr)

    nested_archive_1 = temp_dir_path.joinpath("nested_archive.7z.001")
    nested_archive_1.rename(
        nested_archive_1.with_name("nested_archive.7z.删001")
    )
    nested_archive_2 = temp_dir_path.joinpath("nested_archive.7z.002")
    nested_archive_2.rename(
        nested_archive_2.with_name("nested_archive.7z.删我002")
    )
    for _p in test_filepaths + nested_test_filepaths:
        os.remove(_p)

    test_password_text = """\
    filler
    other_filler
    ------
    password
    password2
    """
    test_password_path = "./temp/test_password.txt"
    with open(test_password_path, "w", encoding="utf-8") as test_pwd_file:
        test_pwd_file.write(test_password_text)

    with open(
        "./config/example_config.toml", "r", encoding="utf-8"
    ) as example_config_file:
        test_config = toml.load(example_config_file)
        test_config["path"]["target_directory"] = str(temp_dir_path)
        test_config["path"]["password_path"] = test_password_path
        test_config["rename"]["substrings"] = ["删除", "删", "删我"]
        test_config["auto_rename"] = True

    test_config_path = "./temp/test_config.toml"
    with open(test_config_path, "w", encoding="utf-8") as test_config_file:
        toml.dump(test_config, test_config_file)

    sys.argv[1:] = ["--config", test_config_path]
    print("sys.argv", sys.argv)

    py_extractor = create_py_extractor()
    py_extractor.run()

    for filename in test_filenames:
        assert os.path.isfile(
            f"./temp/nested_archive.7z.001_out/temp/archive.7z.001_out/temp/{filename}"
        )
