import os

import sys
from hy.compiler import hy_compile
from hy.models import HyExpression, HySymbol
from hy.lex import tokenize

from hy._compat import PY3
from . import ast_compile, bytecode
from .util import write_atomic, _verbose_message


def source_to_code(data, fullname, path, optimize=-1):
    ast = hy_compile(HyExpression([HySymbol("do")]
                                  + tokenize(data.decode("utf-8") + "\n")),
                     fullname)
    return ast_compile(ast, path, "exec")


class HyLoaderBase(object):
    def path_stats(self, path):
        """Return the metadata for the path."""
        st = os.stat(path)
        return {'mtime': st.st_mtime, 'size': st.st_size}

    def source_to_code(self, data, path, _optimize=-1):
        return source_to_code(data, self.name, path, optimize=_optimize)

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
                            path=bytecode_path
                        )
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

    def set_data(self, path, data, mode=0o666):
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
            write_atomic(path, data, mode)
            _verbose_message('created {!r}', path)
        except OSError as exc:
            _verbose_message('could not create {!r}: {!r}', path, exc)
