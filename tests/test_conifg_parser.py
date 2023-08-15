import sys
from py_extract.config import load_config


def test_config_parser():
    test_config_path = "py_extract_config.toml"

    sys.argv[1:] = ["--config", test_config_path]

    config = load_config(test_config_path)

    print(config)
