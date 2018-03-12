from hy._compat import PY3, PY35, PY36


def pytest_ignore_collect(path, config):
    return (("py3_only" in path.basename and not PY3)
            or ("py35_only" in path.basename and not PY35)
            or ("py36_only" in path.basename and not PY36))
