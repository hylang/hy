# Copyright 2018 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.

import os
import imp
import tempfile
from hy.importer import write_hy_as_pyc, get_bytecode_path


def test_pyc():
    """Test pyc compilation."""
    f = tempfile.NamedTemporaryFile(suffix='.hy', delete=False)
    f.write(b'(defn pyctest [s] (+ "X" s "Y"))')
    f.close()

    write_hy_as_pyc(f.name)
    os.remove(f.name)

    cfile = get_bytecode_path(f.name)
    mod = imp.load_compiled('pyc', cfile)
    os.remove(cfile)

    assert mod.pyctest('Foo') == 'XFooY'
