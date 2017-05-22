import hy  # NOQA
import imp
import sys

# This just mocks the normalish behavior of the Python interp. Helpful to aid
# with shimming existing apps that don't really "work" with Hy.
#
# You could say this script helps Hyjack a file.
#


if len(sys.argv) > 1:
    sys.argv.pop(0)
    imp.load_source("__main__", sys.argv[0])
    sys.exit(0)  # right?
