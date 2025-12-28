"""
Get useful information from live Hy or Python objects.

This module provides Hy compatibility with CPython's inspect module.
Within Hy, Hy macros are supported via Hy's `get_macro` macro,
for example `(inspect.getsource (get-macro get-macro))`.
The Hy-specific functionality is monkey-patched into `inspect` at run-time.

The class finder in `findsource` relies on python 3.13 or later.
"""

import inspect
import linecache
import sys
from contextlib import suppress

from hy.compat import PY3_13
from hy.errors import HySyntaxError
from hy.models import as_model, Expression, Lazy, Object
from hy.reader import HyReader, read
from hy.reader.exceptions import LexException, PrematureEndOfInput


class HySafeReader(HyReader):
    """A HyReader that skips over non-default reader macros.

    Skip over undefined reader macros so that no code is executed at read time.
    Do this by replacing the tag reader method to return None, as comments do.
    """

    @reader_for(")")
    @reader_for("]")
    @reader_for("}")
    def _skip(self, key):
        return None

    @reader_for("#")
    def _safe_tag_dispatch(self, key):
        """Skip over undefined reader macros so that no code is executed at read time."""
        with suppress(LexException):
            return super().tag_dispatch(key)


def isExpression(object):
    """Check if object is a Hy Expression instance."""
    return isinstance(object, Expression)


def isLazy(object):
    """Check if object is a Hy Lazy instance."""
    return isinstance(object, Lazy)


def getfile(object):
    """Work out which source or compiled file an object was defined in."""

    if isLazy(object) or isExpression(object):
        if getattr(object, "filename", None) and object.filename != "<string>":
            return object.filename
        else:
            # python's inspect.getfile raises OSError where there's no __file__
            raise OSError("source code not available")

    try:
        return py_getfile(object)
    except TypeError:
        # python's inspect.getfile raises TypeError for unhandled types
        raise TypeError(
            "module, class, method, function, traceback, frame, "
            "code, Expression or Lazy object was expected, got "
            "{}".format(type(object).__name__)
        )


def findsource(object):
    """Return the entire source file and starting line number for an object.

    First looks for Hy source, otherwise defers to the original
    `inspect.findsource`. The argument may be a module, class, method,
    function, traceback, frame, code, Lazy or Expression object. The source
    code is returned as a list of all the lines in the file and the line number
    indexes a line in that list. An OSError is raised if the source code cannot
    be retrieved.
    """
    if getfile(object) is None:
        raise OSError("source code not available")

    fname = inspect.getsourcefile(object)

    if isExpression(object) or isLazy(object):
        if getattr(object, "start_line", None) is None:
            raise OSError("source code not available")
        return (linecache.getlines(fname), object.start_line)
    elif getfile(object).endswith(".hy") and not inspect.isframe(object):
        # We identify other Hy objects from the file extension.
        module = inspect.getmodule(object, fname)
        # List of source code lines.
        lines = (
            linecache.getlines(fname, module.__dict__)
            if module
            else linecache.getlines(fname)
        )
        if inspect.ismodule(object):
            return (lines, 0)
        # Some objects already have the information we need.
        elif hasattr(object, "__code__") and hasattr(object.__code__, "co_firstlineno"):
            # This indexing offset is actually correct.
            return (lines, object.__code__.co_firstlineno - 1)
        elif inspect.iscode(object):
            return (lines, object.co_firstlineno - 1)
        elif inspect.isclass(object):
            # _ClassFinder exists and can be used prior to python 3.13,
            # but would require compiling the ast which may be unsafe,
            # so just decline to do it.
            if PY3_13:
                return py_findsource(object)
            else:
                raise OSError("finding Hy class source code requires Python 3.13")
        else:
            raise OSError("source code not available")
    else:
        # Non-Hy object
        return py_findsource(object)


def getcomments(object):
    """Get comments immediately preceding an object's source code.

    First checks for Hy source, otherwise defers to the original `inspect.getcomments`.
    Returns None when the source can't be found.
    """
    try:
        lines, lnum = findsource(object)
    except (OSError, TypeError):
        # Return None when the source can't be found.
        return None

    if getfile(object).endswith(".hy"):
        # Roughly follows the logic of inspect.getcomments, but for Hy comments
        if not lines:
            return None

        comments = []
        if inspect.ismodule(object) or isExpression(object) or isLazy(object):
            # Remove shebang.
            start = 1 if lines and lines[0][:2] == "#!" else 0
            # Remove preceding empty lines and textless comments.
            while start < len(lines) and set(lines[start].strip()) == {";"}:
                start += 1
            if start < len(lines) and lines[start].lstrip().startswith(";"):
                end = start
                while end < len(lines) and lines[end].lstrip().startswith(";"):
                    comments.append(lines[end].expandtabs())
                    end += 1
                return "".join(comments)
            else:
                return None
        # Look for a comment block preceding the object
        elif lnum > 0 and lnum < len(lines):
            # Look for comments above the object and work up.
            end = lnum - 1
            while end >= 0 and lines[end].lstrip().startswith(";"):
                comments = [lines[end].expandtabs().lstrip()] + comments
                end -= 1
            return "".join(comments) if comments else None
        else:
            return None

    else:
        # Non-Hy object
        return py_getcomments(object)


def getsource(object):
    """Return the text of the source code for an object.

    The argument may be a module, class, method, function, traceback, frame,
    or code object.  The source code is returned as a single string.  An
    OSError is raised if the source code cannot be retrieved."""
    return "".join(getsourcelines(object)[0])


def hy_getblock(lines):
    """Extract the lines of code corresponding to the first Hy form from the given list of lines.

    Built-in Hy reader macros are allowed as safe, since they do not execute code.
    User-defined reader macros could execute code, so we use `HySafeReader`.
    """
    # Read the first form and use its attributes
    try:
        form = read("".join(lines), reader=HySafeReader())
    except HySyntaxError as e:
        raise e from None
    return lines[: form.end_line]


def getsourcelines(object):
    """Return a list of source lines and starting line number for a Hy or python object.

    First checks for Hy source, otherwise defers to the original `inspect.getsourcelines`.

    The argument may be a module, class, method, function, traceback, frame,
    code, Lazy or Expression object. The source code is returned as a list of
    the lines corresponding to the object and the line number indicates where
    in the original source file the first line of code was found. An OSError is
    raised if the source code cannot be retrieved.
    """
    object = inspect.unwrap(object)
    lines, lnum = findsource(object)

    if inspect.istraceback(object):
        object = object.tb_frame

    # For module or frame that corresponds to module, return all source lines.
    if inspect.ismodule(object) or (
        inspect.isframe(object) and object.f_code.co_name == "<module>"
    ):
        return lines, 0

    # Almost everything already works with python's inspect.
    # The inspect.getblock function relies on inspect.BlockFinder which
    # assumes python tokenization.
    # So deal with this as a special case using hy_getblock.
    elif getfile(object).endswith(".hy"):
        return hy_getblock(lines[lnum:]), lnum + 1
    else:
        # Non-Hy object
        return py_getsourcelines(object)


if hasattr(inspect, "_hy_originals"):
    # Retrieve saved versions of `inspect`'s original functions.
    py_findsource, py_getcomments, py_getfile, py_getsource, py_getsourcelines = inspect._hy_originals
else:
    # Save the originals and then monkey-patch.
    inspect._hy_originals = \
        py_findsource,       py_getcomments,      py_getfile,      py_getsource,      py_getsourcelines = \
        inspect.findsource,  inspect.getcomments, inspect.getfile, inspect.getsource, inspect.getsourcelines
    inspect.findsource, inspect.getcomments, inspect.getfile, inspect.getsource, inspect.getsourcelines = \
            findsource,         getcomments,         getfile,         getsource,         getsourcelines
