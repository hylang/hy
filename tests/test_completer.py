import os
import sys
from hy.completer import completion
import pytest


@pytest.mark.skipif(
    "readline" not in sys.modules,
    reason="Module 'readline' is not available.")
def test_history_custom_location(tmp_path):
    import readline

    expected_entry = '(print "Hy, custom history file!")'

    history_location = tmp_path / ".hy-custom-history"
    os.environ["HY_HISTORY"] = str(history_location)

    with completion():
        readline.clear_history()
        readline.add_history(expected_entry)

    actual_entry = history_location.read_text()
    assert expected_entry in actual_entry
