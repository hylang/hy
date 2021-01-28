import os
import sys
from hy.completer import completion
import pytest
import tempfile


@pytest.mark.skipif(
    "readline" not in sys.modules,
    reason="Module 'readline' is not available.")
def test_history_custom_location():
    import readline

    expected_entry = '(print "Hy, custom history file!")'

    with tempfile.TemporaryDirectory() as tmp:
        history_location = tmp + os.sep + ".hy-custom-history"
        os.environ["HY_HISTORY"] = history_location

        with completion():
            readline.clear_history()
            readline.add_history(expected_entry)

        with open(history_location, "r") as hf:
            actual_entry = hf.readline()
            assert expected_entry in actual_entry
