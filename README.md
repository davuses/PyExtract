# PyExtract

![Python](https://img.shields.io/badge/python-3.11-blue.svg)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
![GitHub](https://img.shields.io/github/license/davuses/PyExtract?style=flat-square)

PyExtract is a utility that recursively finds and extracts archives in the target folder.

It can decrypt and decompress zip archives with Non-UTF-8 encoded password. For more details, refer to the related [superuser question](https://superuser.com/questions/1676282).

PyExtract uses Cython to speed up the `zipfile` library

## Screenshots

<img width="1033" alt="image" src="https://github.com/davuses/PyExtract/assets/54793121/12049df2-d789-4525-8666-079eeaa81e2c">

## Installation and Usage

### Prerequisites

- Python >= 3.11
- 7-Zip program (`7z` binary) added to your machine's PATH environment variable.

### Installation

Install the required packages using pip:

```sh
pip install -r requirements.txt
```

Make sure you have Cython installed, and then compile the Cython extension:

```sh
python setup.py build_ext  --inplace
```

Compile translation files:

```sh
python setup.py compile_catalog -D py_extract -d locales/
```

### Configuration and Running

Create a configuration file `py_extract_config.toml` by copying and modifying the `./config/example_config.toml`:

Then run:

```sh
$ python run.py --help

usage: run.py [-h] [-c CONFIG] [-t TARGET_DIR] [-a] [-d]

PyExtract

options:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        config file path
  -t TARGET_DIR, --target-dir TARGET_DIR
                        target directory
  -a, --auto-rename     auto rename archives with bad names
  -d, --debug           debug mode
```

### Example Configuration

Here's an example of a configuration file:

```toml
# addtional encodings of zip archives, the defualt is utf-8
# see https://en.wikipedia.org/wiki/Windows_code_page
# cp936 is used for Chinese encoding
zip_metadata_encoding = ["cp936"]

# language: en, cn
language = "en"

# automatically rename archives with bad filenames
auto_rename = false

# logging level: "warning", "debug"
logging_level = "warning"


[path]
target_directory = "D:/download"
password_path = "D:/passwords.txt"

[exclude]
# exclude filenames, you can leave them empty: suffixes=[]
suffixes = [".apk", ".exe"]
filenames = ["do_not_extract_me.zip"]
substrings = ["not_an_archive"]

[rename]
# rename files whose filenames contain these substrings:
substrings = ["删除", "删除我", "delete_this"]

```

### Windows Users

For Windows users, you can download the compiled binary file from the [releases](https://github.com/davuses/PyExtract/releases) section. Or you can run `build_win.bat` to build the binary by yourself.

### Password File

An example of password file:

```py
# passwords.txt
password_one_in_second_group
password_two_in_second_group

password_one_in_first_group
password_two_in_first_group
```
