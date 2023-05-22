import os
import types

import pytest

import hy.completer
from hy import mangle, unmangle

hy.completer.init_readline()


@pytest.mark.skipif(
    not hy.completer.readline, reason="Module 'readline' is not available."
)
def test_history_custom_location(tmp_path):
    import readline

    expected_entry = '(print "Hy, custom history file!")'

    history_location = tmp_path / ".hy-custom-history"
    os.environ["HY_HISTORY"] = str(history_location)

    with hy.completer.completion():
        readline.clear_history()
        readline.add_history(expected_entry)

    actual_entry = history_location.read_text()

    # yes, this is recommended way to check GNU readline vs libedit
    # see https://docs.python.org/3.11/library/readline.html
    if "libedit" in readline.__doc__:
        # libedit saves spaces as octal escapes, so convert them back
        actual_entry = actual_entry.replace("\\040", " ")

    assert expected_entry in actual_entry


def test_completion():
    completer = hy.completer.Completer(
        {
            "hy": None,
            "simple_pythonic_var_name": None,
            mangle("complicated->@#%!name"): types.SimpleNamespace(
                **{mangle("another$^@#$name"): None}
            ),
            "hyx_XaXaXaX": types.SimpleNamespace(**{"hyx_XbXbX": None}),
        }
    )
    assert completer.complete("hy.", 0) is not None
    for test in [
        ("simple_pyth", "simple-pythonic-var-name"),
        ("compli", "complicated->@#%!name"),
        ("complicated->@#", "complicated->@#%!name"),
        ("complicated->@#%!name", "complicated->@#%!name"),
        ("complicated->@#%!name.ano", "complicated->@#%!name.another$^@#$name"),
        ("complicated->@#%!name.another$^@", "complicated->@#%!name.another$^@#$name"),
        ("hyx_XaX", "hyx_XaXaXaX"),
        ("hyx_XaXaXaX.hyx_Xb", "hyx_XaXaXaX.hyx_XbXbX"),
    ]:
        assert completer.complete(test[0], 0) == test[1]
