# Copyright 2018 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.

import sys
import os

from importlib.machinery import FileFinder, PathFinder

from . import bytecode
from .loader import HyLoader
from .util import _verbose_message


SOURCE_SUFFIXES = [".hy"]

path_importer_cache = {}
path_hooks = []


class HyFileFinder(FileFinder):
    def find_spec(self, fullname, target=None):
        tail_module = fullname.rpartition('.')[2]
        try:
            mtime = os.stat(self.path or os.getcwd()).st_mtime
        except OSError:
            mtime = -1
        if mtime != self._path_mtime:
            self._fill_cache()
            self._path_mtime = mtime

        if tail_module in self._path_cache:
            base_path = os.path.join(self.path, tail_module)
            for suffix, loader_class in self._loaders:
                init_filename = '__init__' + suffix
                full_path = os.path.join(base_path, init_filename)
                if os.path.isfile(full_path):
                    return self._get_spec(loader_class, fullname, full_path,
                                          [base_path], target)

        for suffix, loader_class in self._loaders:
            full_path = os.path.join(self.path, tail_module + suffix)
            _verbose_message('trying {}', full_path, verbosity=2)
            if tail_module + suffix in self._path_cache:
                if os.path.isfile(full_path):
                    return self._get_spec(loader_class, fullname, full_path,
                                          None, target)


class HyPathFinder(PathFinder):
    """Custom PathFinder that keeps a Hy-specific cache and path_hooks."""

    @classmethod
    def invalidate_caches(cls):
        for finder in path_importer_cache.values():
            if hasattr(finder, 'invalidate_caches'):
                finder.invalidate_caches()

    @classmethod
    def _path_hooks(cls, path):
        for hook in path_hooks:
            try:
                return hook(path)
            except ImportError:
                continue

    @classmethod
    def _path_importer_cache(cls, path):
        if path == '':
            try:
                path = os.getcwd()
            except FileNotFoundError:
                return None
        try:
            finder = path_importer_cache[path]
        except KeyError:
            finder = cls._path_hooks(path)
            path_importer_cache[path] = finder
        return finder

    @classmethod
    def find_spec(cls, fullname, path=None, target=None):
        spec = super().find_spec(fullname, path=path, target=target)
        if spec:
            spec.cached = bytecode.get_path(spec.origin)
            return spec


def _install():
    path_hooks.append(HyFileFinder.path_hook((HyLoader, SOURCE_SUFFIXES)))

    sys.meta_path.insert(0, HyPathFinder)
