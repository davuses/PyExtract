import os
from logging import (
    FileHandler,
    Formatter,
    Handler,
    getLogger,
)


def setup_logger(name, handlers: list[Handler], level=None):
    logger = getLogger(name)
    if level:
        logger.setLevel(level=level)
    for handler in handlers:
        logger.addHandler(handler)

    return logger


class FormattedFileHandler(FileHandler):
    def __init__(self, filename) -> None:
        super().__init__(filename, encoding="utf-8")
        formatter = Formatter(
            (
                " %(asctime)s [%(levelname)s %(filename)s:%(lineno)s"
                " %(funcName)s()] %(message)s"
            ),
            "%Y-%m-%d %H:%M:%S",
        )
        self.setFormatter(formatter)


def init_debug_logger():
    log_path = os.path.join(os.path.dirname(__file__), "py_extract.log")
    open(log_path, "w", encoding="utf-8").close()
    logger = setup_logger("file", [FormattedFileHandler(log_path)])
    return logger


debug_logger = init_debug_logger()
