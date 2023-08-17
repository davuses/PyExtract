# PyExtract

PyExtract is a utility that recursively finds and extracts archives in the target folder.

It can decrypt and decompress zip archives with Non-UTF-8 encoded password. see related [superuser question](https://superuser.com/questions/1676282)

## Usage

PyExtract requires Python >= 3.11 and 7-Zip program to run, make sure the `7z` binary is added to your machine's PATH environment variable.

Install the required packages using pip:

```sh
pip install -r requirements.txt
```

Make sure you have Cython installed, and then compile the Cython extension:

```sh
python setup.py build_ext  --inplace
```

Compile translation files using Python babel:

```sh
pybabel compile -D py_extract -d locales/
```

Create a configuration file `py_extract_config.toml` from `./config/example_config.toml`:

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
language = "cn"

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

### Password File

An example of password file:

```py
# passwords.txt
password_one_in_second_group
password_two_in_second_group

password_one_in_first_group
password_two_in_first_group
```
