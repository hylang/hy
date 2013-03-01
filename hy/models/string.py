from hy.models import HyObject
import sys


if sys.version_info[0] >= 3:
    _str_type = str
else:
    _str_type = unicode


class HyString(HyObject, _str_type):
    def __new__(cls, value):
        obj = _str_type.__new__(cls, value)
        return obj
