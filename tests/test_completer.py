import os
import sys
import pytest
import hy.completer

hy.completer.init_readline()

@pytest.mark.skipif(
    not hy.completer.readline,
    reason="Module 'readline' is not available.")
def test_history_custom_location(tmp_path):
    import readline

    expected_entry = '(print "Hy, custom history file!")'

    history_location = tmp_path / ".hy-custom-history"
    os.environ["HY_HISTORY"] = str(history_location)

    with hy.completer.completion():
        readline.clear_history()
        readline.add_history(expected_entry)

    actual_entry = history_location.read_text()
    assert expected_entry in actual_entry
