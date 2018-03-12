import pytest
import hy  # noqa


def pytest_addoption(parser):
    parser.addini("hy_files", type="args",
                  default=['test_*.hy', '*_test.hy'],
                  help="glob-style file patterns for Hy test module discovery")


def pytest_collect_file(parent, path):
    ext = path.ext
    if ext == ".hy":
        if not parent.session.isinitpath(path):
            for pat in parent.config.getini('hy_files'):
                if path.fnmatch(pat):
                    break
            else:
                return
        ihook = parent.session.gethookproxy(path)
        return ihook.pytest_pycollect_makemodule(path=path, parent=parent)
