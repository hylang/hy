import os
import sys
import marshal
import pkgutil
import types
import _imp

if sys.version_info[0:2] in [(3, 3), (3, 4)]:
    from importlib._bootstrap import (cache_from_source, SourceFileLoader,
                                      FileFinder, _verbose_message, 
                                      _get_supported_file_loaders, _relax_case,
                                      _w_long, _code_type)


if sys.version_info[0:2] in [(3, 3)]:
    from importlib._bootstrap import _MAGIC_BYTES as MAGIC_NUMBER

if sys.version_info[0:2] == (3, 4):
    from importlib._bootstrap import _validate_bytecode_header, MAGIC_NUMBER

if sys.version_info[0:2] >= (3, 5):
    from importlib.machinery import SourceFileLoader, FileFinder
    from importlib._bootstrap import _verbose_message
    from importlib._bootstrap_external import (_w_long, _code_type, cache_from_source,
                                               _validate_bytecode_header,
                                               MAGIC_NUMBER, _relax_case,
                                               _get_supported_file_loaders)
    
SEP = os.sep
EXS = os.extsep
FLS = [('%s' + SEP + '__init__' + EXS + '%s', True), 
       ('%s' + EXS + '%s', False)]


def _suffixer(loaders):
    return [(suffix, loader) 
            for (loader, suffixes) in loaders
            for suffix in suffixes]


class _PolySourceFileLoader(SourceFileLoader):
    _compiler = None

    def _poly_bytes_from_bytecode(self, fullname, data, path, st):
        if hasattr(self, '_bytes_from_bytecode'):
            return self._bytes_from_bytecode(fullname, data,
                                             path, st)
        self_module = sys.modules[__name__]
        if hasattr(self_module, '_validate_bytecode_header'):
            return _validate_bytecode_header(data, source_stats = st,
                                             name = fullname, path = path)
        raise ImportError("No bytecode handler found loading.")

    # All this just to change one line.
    def get_code(self, fullname):
        source_path = self.get_filename(fullname)
        source_mtime = None
        try:
            bytecode_path = cache_from_source(source_path)
        except NotImplementedError:
            bytecode_path = None
        else:
            try:
                st = self.path_stats(source_path)
            except NotImplementedError:
                pass
            else:
                source_mtime = int(st['mtime'])
                try:
                    data = self.get_data(bytecode_path)
                except IOError:
                    pass
                else:
                    try:
                        bytes_data = self._poly_bytes_from_bytecode(fullname, data,
                                                                    bytecode_path,
                                                                    st)
                    except (ImportError, EOFError):
                        pass
                    else:
                        _verbose_message('{} matches {}', bytecode_path,
                                        source_path)
                        found = marshal.loads(bytes_data)
                        if isinstance(found, _code_type):
                            _imp._fix_co_filename(found, source_path)
                            _verbose_message('code object from {}',
                                            bytecode_path)
                            return found
                        else:
                            msg = "Non-code object in {}"
                            raise ImportError(msg.format(bytecode_path),
                                              name=fullname, path=bytecode_path)
        source_bytes = self.get_data(source_path)
        code_object = self._compiler(source_bytes, source_path, fullname)
        _verbose_message('code object from {}', source_path)
        if (not sys.dont_write_bytecode and bytecode_path is not None and
            source_mtime is not None):
            data = bytearray(MAGIC_NUMBER)
            data.extend(_w_long(source_mtime))
            data.extend(_w_long(len(source_bytes)))
            data.extend(marshal.dumps(code_object))
            try:
                self._cache_bytecode(source_path, bytecode_path, data)
                _verbose_message('wrote {!r}', bytecode_path)
            except NotImplementedError:
                pass
        return code_object
        

class PolyFileFinder(FileFinder):
    '''The poly version of FileFinder supports the addition of loaders
       after initialization.  That's pretty much the whole point of the 
       PolyLoader mechanism.'''

    _native_loaders = []
    _custom_loaders = []
    
    def __init__(self, path):
        # Base (directory) path
        self.path = path or '.'
        self._path_mtime = -1
        self._path_cache = set()
        self._relaxed_path_cache = set()

    @property
    def _loaders(self):
        return self._custom_loaders + list(self._native_loaders)
        
    @classmethod
    def _install(cls, compiler, suffixes):
        if not suffixes:
            return
        if isinstance(suffixes, str):
            suffixes = [suffixes]
        suffixset = set(suffixes)
        overlap = suffixset.intersection(set([suf[0] for suf in cls._native_loaders]))
        if overlap:
            raise RuntimeError("Override of native Python extensions is not permitted.")
        overlap = suffixset.intersection(
            set([loader[0] for loader in cls._custom_loaders]))
        if overlap:
            # Fail silently
            return

        newloaderclassname = (suffixes[0].lower().capitalize() + 
                              str(_PolySourceFileLoader).rpartition('.')[2][1:])
        if isinstance(compiler, types.FunctionType):
            newloader = type(newloaderclassname, (_PolySourceFileLoader,), 
                             dict(_compiler = staticmethod(compiler)))
        else:
            newloader = type(newloaderclassname, (_PolySourceFileLoader,), 
                             dict(_compiler = compiler))
        cls._custom_loaders += [(EXS + suffix, newloader) for suffix in suffixset]

    @classmethod
    def getmodulename(cls, path):
        filename = os.path.basename(path)
        suffixes = ([(-len(suf[0]), suf[0]) for suf in cls._native_loaders] +
                    [(-len(suf[0]), suf[0]) for suf in cls._custom_loaders])
        suffixes.sort()
        for neglen, suffix in suffixes:
            if filename[neglen:] == suffix:
                return filename[:neglen]
        return None

    def find_loader(self, fullname):
        """Try to find a loader for the specified module, or the namespace
        package portions. Returns (loader, list-of-portions)."""
        is_namespace = False
        tail_module = fullname.rpartition('.')[2]
        try:
            mtime = os.stat(self.path).st_mtime
        except OSError:
            mtime = -1
        if mtime != self._path_mtime:
            self._fill_cache()
            self._path_mtime = mtime
        # tail_module keeps the original casing, for __file__ and friends
        if _relax_case():
            cache = self._relaxed_path_cache
            cache_module = tail_module.lower()
        else:
            cache = self._path_cache
            cache_module = tail_module
        # Check if the module is the name of a directory (and thus a package).
        if cache_module in cache:
            base_path = os.path.join(self.path, tail_module)
            if os.path.isdir(base_path):
                for suffix, loader in self._loaders:
                    init_filename = '__init__' + suffix
                    full_path = os.path.join(base_path, init_filename)
                    if os.path.isfile(full_path):
                        return (loader(fullname, full_path), [base_path])
                else:
                    # A namespace package, return the path if we don't also
                    #  find a module in the next section.
                    is_namespace = True
        # Check for a file w/ a proper suffix exists.
        for suffix, loader in self._loaders:
            full_path = os.path.join(self.path, tail_module + suffix)
            _verbose_message('trying {}'.format(full_path), verbosity=2)
            if cache_module + suffix in cache:
                if os.path.isfile(full_path):
                    return (loader(fullname, full_path), [])
        if is_namespace:
            _verbose_message('possible namespace for {}'.format(base_path))
            return (None, [base_path])
        return (None, [])

    @classmethod
    def path_hook(cls, *loader_details):
        cls._native_loaders = loader_details
        def path_hook_for_PolyFileFinder(path):
            if not os.path.isdir(path):
                raise ImportError("only directories are supported", path=path)
            return PolyFileFinder(path)
        return path_hook_for_PolyFileFinder


def _poly_file_finder_modules(importer, prefix=''):
    print("RUNNING!")
    if importer.path is None or not os.path.isdir(importer.path):
        return

    yielded = {}

    try:
        filenames = os.listdir(importer.path)
    except OSError:
        # ignore unreadable directories like import does
        filenames = []
    filenames.sort()
    for fn in filenames:
        modname = importer.getmodulename(fn)
        if modname == '__init__' or modname in yielded:
            continue

        path = os.path.join(importer.path, fn)
        ispkg = False

        if not modname and os.path.isdir(path) and '.' not in fn:
            modname = fn
            try:
                dircontents = os.listdir(path)
            except OSError:
                # ignore unreadable directories like import does
                dircontents = []
            for fn in dircontents:
                subname = importer.getmodulename(fn)
                if subname == '__init__':
                    ispkg = True
                    break
            else:
                continue    # not a package

        if modname and '.' not in modname:
            yielded[modname] = 1
            yield prefix + modname, ispkg
 

def install(compiler, suffixes):
    filefinder = [(f, i) for i, f in enumerate(sys.path_hooks)
                  if repr(f).find('.path_hook_for_FileFinder') != -1]
    if filefinder:
        filefinder, fpos = filefinder[0]
        sys.path_hooks[fpos] = PolyFileFinder.path_hook(*(_suffixer(_get_supported_file_loaders())))
        sys.path_importer_cache = {}
        pkgutil.iter_importer_modules.register(PolyFileFinder, _poly_file_finder_modules)

    PolyFileFinder._install(compiler, suffixes)


def reset():
    PolyFileFinder._custom_loaders = []
