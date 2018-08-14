import sys

from . import ast_compile, hy_parse
from ..compiler import hy_compile
from .._compat import PY35

from importlib.util import cache_from_source
from importlib.machinery import SourceFileLoader
from importlib._bootstrap import _verbose_message

if PY35:
    from importlib._bootstrap_external import (_compile_bytecode,
                                               _code_to_bytecode,
                                               _validate_bytecode_header)
else:
    from importlib._bootstrap import (_compile_bytecode,
                                      _code_to_bytecode,
                                      _validate_bytecode_header)


class HyLoader(SourceFileLoader):
    def source_to_code(self, data, path='<string>'):
        ast = hy_compile(hy_parse(data.decode("utf-8")), self.name)
        return ast_compile(ast, path, "exec")

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
            except IOError as e:
                pass
            else:
                source_mtime = int(st['mtime'])
                try:
                    data = self.get_data(bytecode_path)
                except (IOError, OSError):
                    pass
                else:
                    try:
                        bytes_data = _validate_bytecode_header(
                            data, source_stats=st, name=fullname,
                            path=bytecode_path)
                    except (ImportError, EOFError) as err:
                        pass
                    else:
                        _verbose_message('{} matches {}', bytecode_path,
                                         source_path)

                        return _compile_bytecode(bytes_data, name=fullname,
                                                 bytecode_path=bytecode_path,
                                                 source_path=source_path)

        source_bytes = self.get_data(source_path)
        code_object = self.source_to_code(source_bytes, source_path)
        _verbose_message('code object from {}', source_path)

        if (not sys.dont_write_bytecode and bytecode_path is not None and
                source_mtime is not None):
            data = _code_to_bytecode(code_object, source_mtime,
                                     len(source_bytes))
            self.set_data(bytecode_path, data)
            _verbose_message('wrote {!r}', bytecode_path)

        return code_object
