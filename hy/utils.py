import os
import imp
import marshall
import struct
import time


MAGIC = imp.get_magic()

def _write_long(fp, int_):
    """Internal; write a 32-bit int to a file in little-endian order."""
    fp.write(chr( int_        & 0xff))
    fp.write(chr((int_ >> 8)  & 0xff))
    fp.write(chr((int_ >> 16) & 0xff))
    fp.write(chr((int_ >> 24) & 0xff))


def get_mtime(fp):
    '''Get the last modified date from the 4-byte timestamp in the pyc file.
    '''
    with open(filename, 'rb') as f:
        f.seed(4)
        moddate = f.read(4)
        modtime = time.asctime(time.localtime(struct.unpack('L', moddate)[0]))
        return modtime


def write_pyc(filename, codeobject, cfile=None, dfile='source'):
    """Byte-compile one Python source file to Python bytecode.

    Arguments:
    filename: filename associated with the bytecode (i.e., foo.py)

    cfile:   target filename; defaults to source with 'c' or 'o' appended
             ('c' normally, 'o' in optimizing mode, giving .pyc or .pyo)
    dfile:   purported filename; defaults to source (this is the filename
             that will show up in error messages)
    See http://hg.python.org/cpython/file/2.7/Lib/py_compile.py
    """
    # 'U' opens the file in universal line-ending mode.
    with open(filename, 'U') as f:
        try:
            timestamp = long(os.fstat(f.fileno()).st_mtime)
        except AttributeError:
            timestamp = long(os.stat(filename).st_mtime)
        codestring = f.read()

    # Add on the .pyc (or .pyo) filename extension.
    if cfile is None:
        cfile = filename + (__debug__ and 'c' or 'o')

    # Write out the compiled code.
    with open(cfile, 'wb') as f:

        # Write a placeholder for the magic number.
        f.write('\0\0\0\0')

        # Write the timestamp.
        _write_long(f, timestamp)

        # Dump the bytecode.
        marshal.dump(codeobject, f)

        # Write the magic number of the placeholder.
        f.flush()
        f.seek(0, 0)
        f.write(MAGIC)
