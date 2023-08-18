class InvalidConfig(Exception):
    pass


class InvalidPath(Exception):
    pass


class BadFormat(Exception):
    pass


class ConfigNotFound(Exception):
    pass


class UnsafeTarfile(Exception):
    ...


class SevenZipExtractFail(Exception):
    ...


class SevenZipCmdNotFound(Exception):
    ...
