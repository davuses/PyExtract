import argparse
import gettext
import sys
from logging import getLogger
from pathlib import Path

from .config import load_config
from .extractor import PyExtractor
from .logging_utils import FormattedFileHandler


def resource_path(relative_path: str):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    base_path = getattr(sys, "_MEIPASS", "./")
    return Path(base_path).joinpath(relative_path)


def init_translation(lang: str):
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
    logger = getLogger(__name__)
    logger.setLevel(level=logging_level)
    log_path = "py_extract.log"
    logger.addHandler(FormattedFileHandler(log_path))

    language = py_extract_config.language
    init_translation(language)
    py_extractor = PyExtractor(config=py_extract_config)
    return py_extractor
