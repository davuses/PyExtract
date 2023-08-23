from logging import (
    FileHandler,
    Formatter,
)


class FormattedFileHandler(FileHandler):
    def __init__(self, filename) -> None:
        super().__init__(filename, encoding="utf-8")
        formatter = Formatter(
            (
                " %(asctime)s [%(levelname)s %(name)s:%(lineno)s"
                " %(funcName)s()] %(message)s"
            ),
            "%Y-%m-%d %H:%M:%S",
        )
        self.setFormatter(formatter)
