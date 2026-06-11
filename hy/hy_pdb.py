"""Hy-aware debugger extension for pdb.

Provides Hy-specific commands in pdb for macro debugging.
Monkey-patches sys.breakpointhook to use HyPdb automatically.
"""

import pdb
import sys
import hy

__all__ = ['HyPdb', 'set_trace']


def _decode_local_macro_name(key):
    """Reverse hy.macros.local_macro_name encoding.

    _hy_local_macro__fooDDbar -> 'foo.bar' (original Hy name).
    """
    prefix = '_hy_local_macro__'
    assert key.startswith(prefix), f"Expected prefix {prefix}, got {key}"
    mangled = key[len(prefix):]
    # Encoding order in local_macro_name: mangle, then D->DN, then .->DD.
    # Reverse: DD->sentinel, DN->D, sentinel->.
    decoded = mangled.replace('DD', '\x00').replace('DN', 'D').replace('\x00', '.')
    return hy.unmangle(decoded)


class HyPdb(pdb.Pdb):
    """Pdb subclass with Hy-aware debugging commands."""

    def _hy_expand(self, arg, expand_fn):
        """Helper to expand a Hy form.

        Args:
            arg: The Hy form to expand as a string.
            expand_fn: Either hy.macroexpand or hy.macroexpand_1.

        Raises:
            Displays error via self.error() on failure.
        """
        if not arg.strip():
            self.error("Usage: <command> (form ...)")
            return

        try:
            # Use <pdb> as filename to avoid confusing error messages
            form = hy.read(arg, filename="<pdb>")
        except hy.PrematureEndOfInput as e:
            self.error(f"Incomplete form: {e}")
            return
        except hy.HySyntaxError as e:
            self.error(f"Syntax error: {e}")
            return

        module_name = self.curframe.f_globals.get('__name__')
        if module_name is None:
            self.error("Cannot determine module name")
            return

        try:
            expanded = expand_fn(form, module_name)
            self.message(f"{hy.repr(expanded)}")
        except Exception as e:
            self.error(f"Expansion failed: {e}")

    def do_macroexpand(self, arg):
        """Expand a Hy form fully: macroexpand (my-macro 1 2)"""
        self._hy_expand(arg, hy.macroexpand)

    def do_macroexpand_1(self, arg):
        """Single-step macro expansion: macroexpand_1 (my-macro 1 2)"""
        self._hy_expand(arg, hy.macroexpand_1)

    def do_macros(self, arg):
        """List macros defined in the current module and local scope."""
        module_name = self.curframe.f_globals.get('__name__')

        # Module-level macros
        macros = []
        if module_name is not None and module_name in sys.modules:
            module = sys.modules[module_name]
            if hasattr(module, '_hy_macros'):
                for name in module._hy_macros:
                    macros.append(hy.unmangle(name))

        # Local macros (defmacro or require in function body)
        local = []
        for k in self.curframe.f_locals:
            if k.startswith('_hy_local_macro__'):
                try:
                    original = _decode_local_macro_name(k)
                    local.append(original)
                except Exception:
                    pass

        if not macros and not local:
            self.message("No macros found.")
            return

        if macros:
            self.message(f"Macros ({len(macros)}):")
            for name in sorted(macros):
                self.message(f"  {name}")
        if local:
            self.message(f"Local macros ({len(local)}):")
            for name in sorted(local):
                self.message(f"  {name}")

    def do_hy_repr(self, arg):
        """Show Hy representation: hy_repr <python_expression>"""
        if not arg.strip():
            self.error("Usage: hy_repr <expression>")
            return

        try:
            result = eval(arg, self.curframe.f_globals, self.curframe_locals)
        except NameError as e:
            self.error(f"Name not found: {e}")
            return
        except Exception as e:
            self.error(f"Error evaluating expression: {e}")
            return

        try:
            self.message(f"{hy.repr(result)}")
        except Exception as e:
            self.error(f"Cannot represent as Hy: {e}")

    # Aliases
    do_me = do_macroexpand
    do_me1 = do_macroexpand_1
    do_m = do_macros
    do_hy = do_hy_repr


def set_trace(*, header=None):
    """Enter the debugger using HyPdb.

    This function is installed as sys.breakpointhook to make
    breakpoint() use Hy-aware debugging automatically (PEP 553).
    """
    debugger = HyPdb()
    if header is not None:
        debugger.message(header)
    debugger.set_trace(sys._getframe().f_back)


# Install as breakpoint hook (PEP 553)
sys.breakpointhook = set_trace
