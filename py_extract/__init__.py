import argparse
import gettext

from .config import load_config
from .logging_utils import setup_logger
from .extractor import PyExtractor


def init_translation(lang):
    app_name = "py_extract"
    localedir = "./locales"
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
    args = parser.parse_args()

    config_arg = args.config

    py_extract_config = load_config(config_arg)

    logging_level = {"debug": "DEBUG"}.get(
        py_extract_config.logging_level, "WARNING"
    )
    logger = setup_logger(logging_level)

    language = py_extract_config.language
    init_translation(language)
    py_extractor = PyExtractor(config=py_extract_config, logger=logger)
    return py_extractor
