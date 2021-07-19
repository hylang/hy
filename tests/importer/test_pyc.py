import os
import importlib.util
import py_compile
import tempfile

import hy.importer


def test_pyc():
    """Test pyc compilation."""
    with tempfile.NamedTemporaryFile(suffix='.hy') as f:
        f.write(b'(defn pyctest [s] (+ "X" s "Y"))')
        f.flush()

        cfile = py_compile.compile(f.name)
        assert os.path.exists(cfile)

        try:
            mod = hy.importer._import_from_path('pyc', cfile)
        finally:
            os.remove(cfile)

        assert mod.pyctest('Foo') == 'XFooY'
