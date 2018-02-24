# Copyright 2018 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.

import sys
import os

from importlib.abc import FileLoader, SourceLoader
from importlib.machinery import FileFinder, PathFinder

from . import bytecode
from .common import HyLoaderBase


SOURCE_SUFFIXES = [".hy"]


path_importer_cache = {}
path_hooks = []


class HyLoader(HyLoaderBase, FileLoader, SourceLoader):
    pass


class HyPathFinder(PathFinder):
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
        else:
            return None

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
            # Need to be rewritten for __cached__ module attribute to
            # be written correctly.
            spec.cached = bytecode.get_path(spec.origin)
            return spec


def _install():
    path_hooks.append(FileFinder.path_hook((HyLoader, SOURCE_SUFFIXES)))
    sys.meta_path.append(HyPathFinder)
