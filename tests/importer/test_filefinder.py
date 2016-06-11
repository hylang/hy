# Test various import styles

from hy.core.language import map
from hy import importer
import hy.importer
from hy.importer import import_buffer_to_ast

import os
import os.path
import pkgutil
import inspect


# Test that the iter_modules mechanism now works and
# Python gives us both py and hy files found in a
# module
def test_finder():
    path = os.path.join(
        os.path.dirname(
            os.path.abspath(
                inspect.getfile(
                    inspect.currentframe()))), 'test_module')

    def _hy_anon_fn_1(pkg):
        return pkg[1]
    modules = list(map(lambda pkg: pkg[1], pkgutil.iter_modules([path])))
    assert ('hytest' in modules)
    assert ('pytest' in modules)
