# PyExtract

A tool that finds and extracts archives recursively in target folder.

## Compile

Make sure Cython is installed, compile the Cython extension:

```sh
python setup.py build_ext  --inplace
```

Compile translation:
```sh
pybabel compile -D py_extract -d locales/
``` 

run:

```sh
python run.py
```

```sh
$ python run.py --help
usage: run.py [-h] [-c CONFIG]

PyExtract

options:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        config file path
```


passwords file should be like:
```py
# passwords.txt
password_one_in_second_group
password_two_in_second_group

password_one_in_first_group
password_two_in_first_group
```
