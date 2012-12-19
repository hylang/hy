from hy.lang.hyobj import HYObject
import sys


if sys.version_info[0] >= 3:
    _str_type = str
else:
    _str_type = unicode


class HYString(HYObject, _str_type):
    def __init__(self, string):
        self += string

    def eval(self, ln, *args, **kwargs):
        return str(self)
