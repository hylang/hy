# Copyright 2018 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.

import os
import imp
import tempfile

import py_compile


def test_pyc():
    """Test pyc compilation."""
    with tempfile.NamedTemporaryFile(suffix='.hy') as f:
        f.write(b'(defn pyctest [s] (+ "X" s "Y"))')
        f.flush()

        cfile = py_compile.compile(f.name)

        assert os.path.exists(cfile)

        mod = imp.load_compiled('pyc', cfile)
        os.remove(cfile)

        assert mod.pyctest('Foo') == 'XFooY'
