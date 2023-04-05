from logging import (
    FileHandler,
    Formatter,
    Handler,
    getLogger,
)
import os


def setup_logger(name, handlers: list[Handler], level=None):
    logger = getLogger(name)
    if level:
        logger.setLevel(level=level)
    for handler in handlers:
        logger.addHandler(handler)

    return logger


class FormarttedFileHandler(FileHandler):
    def __init__(self, filename):
        super().__init__(filename, encoding="utf-8")
        formatter = Formatter(
            (
                " %(asctime)s [%(levelname)s %(filename)s:%(lineno)s"
                " %(funcName)s()] %(message)s"
            ),
            "%Y-%m-%d %H:%M:%S",
        )
        self.setFormatter(formatter)


log_path = os.path.join(os.path.dirname(__file__), "extract.log")
open(log_path, "w").close()
debug_logger = setup_logger("file", [FormarttedFileHandler(log_path)])
