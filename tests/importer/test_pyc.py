import os
import imp
import tempfile
from hy.importer import write_hy_as_pyc


def test_pyc():
    """Test pyc compilation."""
    f = tempfile.NamedTemporaryFile(suffix='.hy', delete=False)
    f.write(b'(defn pyctest [s] s)')
    f.close()

    write_hy_as_pyc(f.name)
    os.unlink(f.name)

    cfile = "%s.pyc" % f.name[:-len(".hy")]
    mod = imp.load_compiled('pyc', cfile)
    os.unlink(cfile)

    assert mod.pyctest('Foo') == 'Foo'
