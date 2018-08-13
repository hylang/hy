import sys

from hy.compiler import hy_compile
from hy._compat import PY3

from . import ast_compile, bytecode, hy_parse
from .util import _verbose_message


try:
    from importlib.machinery import SourceFileLoader
except ImportError:
    SourceFileLoader = object


class HyLoader(SourceFileLoader):
    def source_to_code(self, data, path, _optimize=-1):
        ast = hy_compile(hy_parse(data.decode("utf-8")), self.name)
        return ast_compile(ast, path, "exec")

    def get_code(self, fullname):
        source_path = self.get_filename(fullname)
        source_mtime = None
        try:
            bytecode_path = bytecode.get_path(source_path)
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
                        bytes_data = bytecode.validate_header(
                            data, source_stats=st, name=fullname,
                            path=bytecode_path)
                    except (ImportError, EOFError) as err:
                        pass
                    else:
                        _verbose_message('{} matches {}', bytecode_path,
                                         source_path)

                        # In Python 2, __file__ reflects what's
                        # loaded. By fixing this up, we'll set the
                        # bytecode path instead.
                        #
                        # Easier to live with the conditional here
                        # than having two maintain two copies of this
                        # function...
                        if not PY3:
                            self.path = bytecode_path

                        return bytecode.load(bytes_data, name=fullname,
                                             bytecode_path=bytecode_path,
                                             source_path=source_path)

        source_bytes = self.get_data(source_path)
        code_object = self.source_to_code(source_bytes, source_path)
        _verbose_message('code object from {}', source_path)

        if (not sys.dont_write_bytecode and bytecode_path is not None and
                source_mtime is not None):
            data = bytecode.dump(code_object, source_mtime, len(source_bytes))
            self.set_data(bytecode_path, data)
            _verbose_message('wrote {!r}', bytecode_path)

        return code_object
