# Copyright 2018 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.

from io import open
import imp
import os
import sys

from . import loader
from .util import write_atomic, calc_mode, _verbose_message


class HyLoader(loader.HyLoader):
    def path_stats(self, path):
        st = os.stat(path)
        return {'mtime': st.st_mtime, 'size': st.st_size}

    def is_package(self, fullname):
        filename = os.path.split(self.path)[1]
        filename_base = filename.rsplit('.', 1)[0]
        tail_name = fullname.rpartition('.')[2]
        return filename_base == '__init__' and tail_name != '__init__'

    def get_data(self, path):
        with open(path, 'rb') as f:
            return f.read()

    def set_data(self, path, data):
        parent, filename = os.path.split(path)
        path_parts = []
        while parent and not os.path.isdir(parent):
            parent, part = os.path.split(parent)
            path_parts.append(part)

        for part in reversed(path_parts):
            parent = os.path.join(parent, part)
            try:
                os.mkdir(parent)
            except FileExistsError:
                continue
            except OSError as exc:
                _verbose_message('could not create {!r}: {!r}', parent, exc)
                return
        try:
            mode = calc_mode(path)
            write_atomic(path, data, mode)
            _verbose_message('created {!r}', path)
        except OSError as exc:
            _verbose_message('could not create {!r}: {!r}', path, exc)

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

        if not path:
            if root_module:
                f, filename, description = imp.find_module(root_module)
                module = imp.load_module(root_module, f, filename, description)
                return imp.find_module(root_module, module.__path__)
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
