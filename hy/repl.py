import ast
import builtins
import code
import codeop
import hashlib
import importlib
import linecache
import os
import platform
import sys
import time
import traceback
import types
from contextlib import contextmanager

import hy
from hy.compiler import HyASTCompiler, hy_compile
from hy.completer import Completer, completion
from hy.errors import (
    HyLanguageError,
    HyMacroExpansionError,
    HyRequireError,
    filtered_hy_exceptions,
)
from hy.importer import HyLoader
from hy.macros import enable_readers, require, require_reader
from hy.reader import mangle, read_many
from hy.reader.exceptions import PrematureEndOfInput
from hy.reader.hy_reader import HyReader


class HyQuitter:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "Use (%s) or Ctrl-D (i.e. EOF) to exit" % (self.name)

    __str__ = __repr__

    def __call__(self, code=None):
        try:
            sys.stdin.close()
        except:
            pass
        raise SystemExit(code)


class HyHelper:
    def __repr__(self):
        return (
            "Use (help) for interactive help, or (help object) for help "
            "about object."
        )

    def __call__(self, *args, **kwds):
        import pydoc

        return pydoc.help(*args, **kwds)


sys.last_type = None
sys.last_value = None
sys.last_traceback = None


@contextmanager
def extend_linecache(add_cmdline_cache):
    _linecache_checkcache = linecache.checkcache

    def _cmdline_checkcache(*args):
        _linecache_checkcache(*args)
        linecache.cache.update(add_cmdline_cache)

    linecache.checkcache = _cmdline_checkcache
    yield
    linecache.checkcache = _linecache_checkcache


_codeop_maybe_compile = codeop._maybe_compile
codeop._maybe_compile = (lambda compiler, source, filename, symbol, *args, **kwargs:
    # Python 3.14 adds a mandatory parameter `flags`, which is
    # sometimes specified by position and sometimes by name.
    compiler(source, filename, symbol)
    if isinstance(compiler, HyCompile) else
    _codeop_maybe_compile(compiler, source, filename, symbol, *args, **kwargs))


class HyCompile(codeop.Compile):
    """This compiler uses `linecache` like
    `IPython.core.compilerop.CachingCompiler`.
    """

    def __init__(
        self, module, locals, ast_callback=None, hy_compiler=None, cmdline_cache={}
    ):
        self.module = module
        self.locals = locals
        self.ast_callback = ast_callback
        self.hy_compiler = hy_compiler
        self.reader = HyReader()
        self.skip_next_shebang = False

        super().__init__()

        if hasattr(self.module, "_hy_reader_macros"):
            enable_readers(
                self.module, self.reader, self.module._hy_reader_macros.keys()
            )

        self.cmdline_cache = cmdline_cache

    def _cache(self, source, name):
        entry = (
            len(source),
            time.time(),
            [line + "\n" for line in source.splitlines()],
            name,
        )

        linecache.cache[name] = entry
        self.cmdline_cache[name] = entry

    def _update_exc_info(self):
        self.locals["_hy_last_type"] = sys.last_type
        self.locals["_hy_last_value"] = sys.last_value
        # Skip our frame.
        sys.last_traceback = getattr(sys.last_traceback, "tb_next", sys.last_traceback)
        self.locals["_hy_last_traceback"] = sys.last_traceback

    def __call__(self, source, filename="<input>", symbol=None):
        symbol = "exec"
          # This parameter is required by `codeop.Compile`, but we
          # ignore it in favor of always using "exec".

        hash_digest = hashlib.sha1(source.encode("utf-8").strip()).hexdigest()
        name = "{}-{}".format(filename.strip("<>"), hash_digest)

        self._cache(source, name)

        try:
            # Our compiler doesn't correspond to a real, fixed source file, so
            # we need to [re]set these.
            self.hy_compiler.filename = name
            self.hy_compiler.source = source
            hy_ast = read_many(
                source, filename=name, reader=self.reader,
                skip_shebang=self.skip_next_shebang,
            )
            self.skip_next_shebang = False
            exec_ast, eval_ast = hy_compile(
                hy_ast,
                self.module,
                root=ast.Module,
                get_expr=True,
                compiler=self.hy_compiler,
                filename=name,
                source=source,
                import_stdlib=False,
            )

            if self.ast_callback:
                self.ast_callback(exec_ast, eval_ast)

            exec_code = super().__call__(exec_ast, name, symbol)
            eval_code = super().__call__(eval_ast, name, "eval")

        except Exception as e:
            # Capture and save the error before we handle further

            sys.last_type, sys.last_value, sys.last_traceback = sys.exc_info()
            self._update_exc_info()

            if isinstance(e, (PrematureEndOfInput, SyntaxError)):
                raise
            else:
                # Hy will raise exceptions during compile-time that Python would
                # raise during run-time (e.g. import errors for `require`).  In
                # order to work gracefully with the Python world, we convert such
                # Hy errors to code that purposefully reraises those exceptions in
                # the places where Python code expects them.
                # Capture a traceback without the compiler/REPL frames.
                exec_code = super(HyCompile, self).__call__(
                    "raise _hy_last_value.with_traceback(_hy_last_traceback)",
                    name,
                    symbol,
                )
                eval_code = super(HyCompile, self).__call__("None", name, "eval")

        return exec_code, eval_code


class HyCommandCompiler(codeop.CommandCompiler):
    def __init__(self, *args, allow_incomplete = True, **kwargs):
        self.compiler = HyCompile(*args, **kwargs)
        self.allow_incomplete = allow_incomplete

    def __call__(self, *args, **kwargs):
        try:
            return super().__call__(*args, **kwargs)
        except PrematureEndOfInput:
            # We have to do this here, because `codeop._maybe_compile` won't
            # take `None` for a return value (at least not in Python 2.7) and
            # this exception type is also a `SyntaxError`, so it will be caught
            # by `code.InteractiveConsole` base methods before it reaches our
            # `runsource`.
            if not self.allow_incomplete:
                raise


class REPL(code.InteractiveConsole):
    """A subclass of :class:`code.InteractiveConsole` for Hy.

    A convenient way to use this class to interactively debug code is to insert the
    following in the code you want to debug::

        (.run (hy.REPL :locals {#** (globals) #** (locals)}))

    Or in Python:

    .. code-block:: python

       import hy; hy.REPL(locals = {**globals(), **locals()}).run()

    Note that as with :func:`code.interact`, changes to local variables inside the
    REPL are not propagated back to the original scope."""

    __module__ = 'hy'

    def __init__(self, spy=False, spy_delimiter=('-' * 30), output_fn=None, locals=None, filename="<stdin>", allow_incomplete=True):

        # Create a proper module for this REPL so that we can obtain it easily
        # (e.g. using `importlib.import_module`).
        # We let `InteractiveConsole` initialize `self.locals` when it's
        # `None`.
        super().__init__(locals=locals, filename=filename)

        module_name = self.locals.get("__name__", "__console__")
        # Make sure our newly created module is properly introduced to
        # `sys.modules`, and consistently use its namespace as `self.locals`
        # from here on.
        self.module = sys.modules.setdefault(module_name, types.ModuleType(module_name))
        self.module.__dict__.update(self.locals)
        self.locals = self.module.__dict__

        self.ps1 = "=> "
        self.ps2 = "... "

        if os.environ.get("HYSTARTUP"):
            try:
                loader = HyLoader("__hystartup__", os.environ.get("HYSTARTUP"))
                spec = importlib.util.spec_from_loader(loader.name, loader)
                mod = importlib.util.module_from_spec(spec)
                sys.modules.setdefault(mod.__name__, mod)
                loader.exec_module(mod)
                imports = mod.__dict__.get(
                    "__all__",
                    [name for name in mod.__dict__ if not name.startswith("_")],
                )
                imports = {name: mod.__dict__[name] for name in imports}
                spy = spy or imports.get("repl_spy")
                output_fn = output_fn or imports.get("repl_output_fn")
                self.ps1 = imports.get("repl_ps1", self.ps1)
                self.ps2 = imports.get("repl_ps2", self.ps2)

                # Load imports and defs
                self.locals.update(imports)

                # load module macros
                require(mod, self.module, assignments="ALL")
                require_reader(mod, self.module, assignments="ALL")
            except Exception as e:
                print(e)

        self.hy_compiler = HyASTCompiler(self.module, module_name)

        self.cmdline_cache = {}
        self.compile = HyCommandCompiler(
            self.module,
            self.locals,
            ast_callback=self.ast_callback,
            hy_compiler=self.hy_compiler,
            cmdline_cache=self.cmdline_cache,
            allow_incomplete=allow_incomplete,
        )

        self.spy = spy
        self.spy_delimiter = spy_delimiter
        self.last_value = None
        self.print_last_value = True

        if output_fn is None:
            self.output_fn = hy.repr
        elif callable(output_fn):
            self.output_fn = output_fn
        elif "." in output_fn:
            parts = [mangle(x) for x in output_fn.split(".")]
            module, f = ".".join(parts[:-1]), parts[-1]
            self.output_fn = getattr(importlib.import_module(module), f)
        else:
            self.output_fn = getattr(builtins, mangle(output_fn))

        # Pre-mangle symbols for repl recent results: *1, *2, *3
        self._repl_results_symbols = [mangle("*{}".format(i + 1)) for i in range(3)]
        self.locals.update({sym: None for sym in self._repl_results_symbols})

        # Allow access to the running REPL instance
        self.locals["_hy_repl"] = self

        # Compile an empty statement to load the standard prelude
        exec_ast = hy_compile(
            read_many(""), self.module, compiler=self.hy_compiler, import_stdlib=True
        )
        if self.ast_callback:
            self.ast_callback(exec_ast, None)

    def ast_callback(self, exec_ast, eval_ast):
        if self.spy:
            try:
                # Mush the two AST chunks into a single module for
                # conversion into Python.
                new_ast = ast.Module(
                    exec_ast.body
                    + ([] if eval_ast is None else [ast.Expr(eval_ast.body)]),
                    type_ignores=[],
                )
                print(ast.unparse(new_ast))
                print(self.spy_delimiter)
            except Exception:
                msg = "Exception in AST callback:\n{}\n".format(traceback.format_exc())
                self.write(msg)

    def _error_wrap(self, exc_info_override=False, *args, **kwargs):
        sys.last_type, sys.last_value, sys.last_traceback = sys.exc_info()

        if exc_info_override:
            # Use a traceback that doesn't have the REPL frames.
            sys.last_type = self.locals.get("_hy_last_type", sys.last_type)
            sys.last_value = self.locals.get("_hy_last_value", sys.last_value)
            sys.last_traceback = self.locals.get(
                "_hy_last_traceback", sys.last_traceback
            )

        sys.excepthook(sys.last_type, sys.last_value, sys.last_traceback)

        self.locals[mangle("*e")] = sys.last_value

    def showsyntaxerror(self, filename=None, source=None):
        if filename is None:
            filename = self.filename
        self.print_last_value = False

        self._error_wrap(exc_info_override=True, filename=filename)

    def showtraceback(self):
        self._error_wrap()

    def runcode(self, code):
        try:
            eval(code[0], self.locals)
            self.last_value = eval(code[1], self.locals)
            # Don't print `None` values.
            self.print_last_value = self.last_value is not None
        except SystemExit:
            raise
        except Exception as e:
            # Set this to avoid a print-out of the last value on errors.
            self.print_last_value = False
            self.showtraceback()

    def runsource(self, source, filename="<stdin>", symbol="exec"):
        try:
            res = super().runsource(source, filename, symbol)
        except (HyMacroExpansionError, HyRequireError):
            # We need to handle these exceptions ourselves, because the base
            # method only handles `OverflowError`, `SyntaxError` and
            # `ValueError`.
            self.showsyntaxerror(filename)
            return False
        except (HyLanguageError):
            # Our compiler will also raise `TypeError`s
            self.showtraceback()
            return False

        # Shift exisitng REPL results
        if not res:
            next_result = self.last_value
            for sym in self._repl_results_symbols:
                self.locals[sym], next_result = next_result, self.locals[sym]

            # Print the value.
            if self.print_last_value:
                try:
                    output = self.output_fn(self.last_value)
                except Exception:
                    self.showtraceback()
                    return False

                print(output)

        return res

    def run(self):
        "Start running the REPL. Return 0 when done."

        sentinel = []
        saved_values = (
            getattr(sys, "ps1", sentinel),
            getattr(sys, "ps2", sentinel),
            builtins.quit,
            builtins.exit,
            builtins.help,
        )
        try:
            sys.ps1 = self.ps1
            sys.ps2 = self.ps2
            builtins.quit = HyQuitter("quit")
            builtins.exit = HyQuitter("exit")
            builtins.help = HyHelper()

            namespace = self.locals
            with filtered_hy_exceptions(), extend_linecache(
                self.cmdline_cache
            ), completion(Completer(namespace)):
                self.interact(self.banner())

        finally:
            sys.ps1, sys.ps2, builtins.quit, builtins.exit, builtins.help = saved_values
            for a in "ps1", "ps2":
                if getattr(sys, a) is sentinel:
                    delattr(sys, a)

        return 0

    def banner(self):
        return "Hy {version}{nickname} using {py}({build}) {pyversion} on {os}".format(
            version=hy.__version__,
            nickname="" if hy.nickname is None else f' ({hy.nickname})',
            py=platform.python_implementation(),
            build=platform.python_build()[0],
            pyversion=platform.python_version(),
            os=platform.system(),
        )
