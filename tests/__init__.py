
import hy  # noqa
from hy._compat import PY3
from .native_tests.cons import *  # noqa
from .native_tests.defclass import *  # noqa
from .native_tests.math import *  # noqa
from .native_tests.native_macros import *  # noqa
from .native_tests.quote import *  # noqa
from .native_tests.language import *  # noqa
from .native_tests.unless import *  # noqa
from .native_tests.when import *  # noqa
from .native_tests.with_decorator import *  # noqa
from .native_tests.core import *  # noqa
from .native_tests.reader_macros import *  # noqa
from .native_tests.shadow import *  # noqa
from .native_tests.with_test import *  # noqa
from .native_tests.contrib.anaphoric import *  # noqa
from .native_tests.contrib.loop import *  # noqa
from .native_tests.contrib.meth import *  # noqa
from .native_tests.contrib.walk import *  # noqa
from .native_tests.contrib.multi import *  # noqa
from .native_tests.contrib.curry import *  # noqa

if PY3:
    from .native_tests.py3_only_tests import *  # noqa
