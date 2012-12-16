from hy.lang.importer import _hy_import_file
import sys

mod = _hy_import_file('test', sys.argv[1])
