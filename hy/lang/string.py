from hy.lang.hyobj import HYObject
import sys


if sys.version_info[0] >= 3:
    _str_type = str
else:
    _str_type = unicode


class HYString(HYObject, _str_type):
    def __new__(cls, value):
        obj = _str_type.__new__(cls, value)
        return obj

    def eval(self, ln, *args, **kwargs):
        return str(self)
