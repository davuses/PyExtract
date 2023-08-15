from logging import (
    FileHandler,
    Formatter,
    getLogger,
)


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


def setup_logger(level="WARNING"):
    # log_path = os.path.join(os.path.dirname(__file__), "py_extract.log")
    log_path = "py_extract.log"
    # open(log_path, "w", encoding="utf-8").close()
    logger = getLogger("file")
    logger.setLevel(level=level)
    logger.addHandler(FormattedFileHandler(log_path))

    return logger
