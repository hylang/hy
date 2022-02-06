import os
import runpy
import subprocess

# Try to get and update the version.

os.chdir(os.path.split(os.path.abspath(__file__))[0])
VERSIONFILE = os.path.join("hy", "version.py")

try:
    if "HY_VERSION" in os.environ:
        __version__ = os.environ["HY_VERSION"]
    else:
        __version__ = (
            subprocess.check_output(["git", "describe", "--tags", "--dirty"])
            .decode("ASCII")
            .strip()
            .replace("-", "+", 1)
            .replace("-", ".")
        )

    with open(VERSIONFILE, "wt") as o:
        o.write("__version__ = {!r}\n".format(__version__))

except (subprocess.CalledProcessError, OSError):
    if os.path.exists(VERSIONFILE):
        __version__ = runpy.run_path(VERSIONFILE)["__version__"]
    else:
        __version__ = "unknown"
