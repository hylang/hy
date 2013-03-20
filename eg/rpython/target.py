import hy
import sys
import test


def entry_point(argv):
    return test.main(argv)


def target(driver, args):
    return entry_point, None


if __name__ == "__main__":
    entry_point(sys.argv)
