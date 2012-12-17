from hy.lang.hyobj import HYObject
import sys


if sys.version_info[0] >= 3:
    _str_type = str
else:
    _str_type = unicode


class HYString(_str_type, HYObject):
    def __init__(self, string):
        self += string
