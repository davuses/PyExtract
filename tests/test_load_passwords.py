from io import StringIO
from py_extract.utils import load_passwords


def test_load_passwords():
    pwd_text = """\


    foo
    foo2


    ok
    ok2



    bar
    bar2

    """
    pwd_file = StringIO(pwd_text)

    results = load_passwords(pwd_file=pwd_file)
    assert results == ["bar", "bar2", "ok", "ok2", "foo", "foo2"]
