import hy
import imp
import sys


if len(sys.argv) > 1:
    sys.argv.pop(0)
    imp.load_source("__main__", sys.argv[0])
    sys.exit(0)  # right?
