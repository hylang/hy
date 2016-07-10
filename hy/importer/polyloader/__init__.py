# -*- coding: utf-8 -*-
import sys

__author__ = 'Kenneth M. "Elf" Sternberg'
__email__ = 'elf.sternberg@gmail.com'
__version__ = '0.1.0'

if sys.version_info[0:2] >= (2, 6):
    from ._python2 import install, reset

if sys.version_info[0] >= 3:
    from ._python3 import install, reset

__all__ = ['install', 'reset']
