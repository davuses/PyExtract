from io import StringIO

from py_extract.utils import load_passwords

PASSWORDS_TEXT = """\


foo
foo2


ok
ok2



bar
bar2

"""


def test_load_passwords():
    pwd_file = StringIO(PASSWORDS_TEXT)

    results = load_passwords(pwd_file=pwd_file)
    assert results == ["bar", "bar2", "ok", "ok2", "foo", "foo2"]
