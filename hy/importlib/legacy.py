# Copyright 2018 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.

from io import open
import imp
import importlib
import os
import sys

from .common import HyLoaderBase


class HyLoader(HyLoaderBase):
    def __init__(self, fullname, path):
        self.name = fullname
        self.path = path

    def is_package(self, fullname):
        filename = os.path.split(self.path)[1]
        filename_base = filename.rsplit('.', 1)[0]
        tail_name = fullname.rpartition('.')[2]
        return filename_base == '__init__' and tail_name != '__init__'

    def get_filename(self, fullname):
        return self.path

    def get_data(self, path):
        with open(path, 'rb') as f:
            return f.read()

    def load_module(self, fullname):
        if fullname in sys.modules:
            return sys.modules[fullname]

        module = sys.modules[fullname] = imp.new_module(fullname)
        name = module.__name__
        try:
            code_object = self.get_code(name)
        except Exception:
            del sys.modules[fullname]
            raise

        module.__file__ = self.path
        module.__package__ = name
        if self.is_package(name):
            module_path = os.path.split(module.__file__)[0]
            module.__path__ = [module_path]
            sys.path_importer_cache[module_path] = HyPathFinder
        else:
            module.__package__ = module.__package__.rpartition('.')[0]
        module.__loader__ = self

        exec(code_object, module.__dict__)
        return module


class HyPathFinder(object):
    @classmethod
    def find_module(cls, fullname, path=None):
        root_module, _, tail_module = fullname.rpartition('.')

        if root_module:
            module = importlib.import_module(root_module)
            path = module.__path__
        else:
            path = sys.path

        for pth in path:
            base_path = os.path.join(pth, tail_module)

            if os.path.isdir(base_path):
                full_path = os.path.join(base_path, '__init__.hy')
                if os.path.isfile(full_path):
                    return HyLoader(fullname, full_path)
            else:
                full_path = os.path.join(pth, tail_module + '.hy')
                if os.path.isfile(full_path):
                    return HyLoader(fullname, full_path)


def _install():
    sys.meta_path.append(HyPathFinder)
