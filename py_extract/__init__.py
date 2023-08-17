import argparse
import gettext
import os
import sys

from .config import load_config
from .logging_utils import setup_logger
from .extractor import PyExtractor


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    base_path = getattr(sys, "_MEIPASS", "./")
    return os.path.join(base_path, relative_path)


def init_translation(lang):
    app_name = "py_extract"
    localedir = resource_path("locales")
    lang_dict = {"cn": "zh_Hans_CN", "en": "en"}
    locale_language = lang_dict.get(lang, "en")
    en_i18n = gettext.translation(
        app_name,
        localedir,
        languages=[locale_language],
    )
    en_i18n.install(names=["gettext", "ngettext"])


def create_py_extractor():
    parser = argparse.ArgumentParser(description="PyExtract")
    parser.add_argument("-c", "--config", help="config file path")
    parser.add_argument("-t", "--target-dir", help="target directory")
    parser.add_argument(
        "-a",
        "--auto-rename",
        action="store_const",
        const=True,
        help="auto rename archives with bad names",
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_const",
        const="debug",
        help="debug mode",
    )

    args = parser.parse_args()

    config_arg = args.config

    py_extract_config = load_config(config_arg)

    if arg_auto_rename := args.auto_rename:
        py_extract_config.auto_rename = arg_auto_rename
    if arg_debug := args.debug:
        py_extract_config.logging_level = arg_debug
    if arg_target_dir := args.target_dir:
        py_extract_config.target_directory = arg_target_dir
    logging_level = {"debug": "DEBUG"}.get(
        py_extract_config.logging_level, "WARNING"
    )
    logger = setup_logger(logging_level)

    language = py_extract_config.language
    init_translation(language)
    py_extractor = PyExtractor(config=py_extract_config, logger=logger)
    return py_extractor
