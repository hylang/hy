============================
Versioning and compatibility
============================

Starting with Hy 1.0.0, Hy is `semantically versioned <https://semver.org>`_. Refer to `the NEWS file <https://github.com/hylang/hy/blob/master/NEWS.rst>`_ for a summary of user-visible changes brought on by each version, and how to update your code in case of breaking changes. Be sure you're reading the version of this manual (shown at the top of each page) that matches the version of Hy you're running.

Hy is tested on `all released and currently maintained versions of CPython <https://devguide.python.org/versions>`_ (on Linux, Windows, and Mac OS), and on recent versions of `PyPy <https://pypy.org>`_ and `Pyodide <https://pyodide.org>`_. We usually find that for Hy, unlike most Python packages, we need to change things to fully support each new 3.x release of Python. We may drop compatibility with a version of Python after the CPython guys cease maintaining it. Note that we construe such a change as non-breaking, so we won't bump Hy's major version for it. But we will at least bump the minor version, and ``python_requires`` in Hy's ``setup.py`` should prevent you from installing a Hy version that won't work with your Python version.

Starting with Hy 1.0.0, each version of Hy also has a nickname, such as "Afternoon Review". Nicknames are used in alphabetical order, with a nickname starting with "Z" then wrapping around to "A". Nicknames are provided mostly for the amusement of the maintainer, but can be useful as a conspicuous sign that you're not using the version you expected. In code, you can get the current nickname as a string (or ``None``, for unreleased commits of Hy) with ``hy.nickname``.
