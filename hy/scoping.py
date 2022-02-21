"Scope and variable tracking for Hy/Python scopes."

from __future__ import annotations

import ast
import itertools
from abc import ABC, abstractmethod
from typing import List as ListT
from typing import Optional, Protocol
from typing import Set as SetT
from typing import Type, TypeVar, Union

import hy._compat
from hy.errors import HyInternalError
from hy.lex import mangle
from hy.models import Expression, List, Symbol


class _CompilerT(Protocol):
    scope: ScopeBase


def is_function_scope(scope):
    return isinstance(scope, ScopeFn) and scope.is_fn


def is_inside_function_scope(scope):
    "True if any enclosing scope (including this one) is a function scope."
    cur = scope
    while not isinstance(cur, ScopeGlobal):
        if is_function_scope(cur):
            return True
        cur = cur.parent
    return False


def nearest_python_scope(scope):
    "Return the closest enclosing scope that corresponds to a Python scope."
    cur = scope
    while isinstance(cur, (ScopeLet, ScopeGen)):
        cur = cur.parent
    return cur


_NodeT = Union[ast.Name, ast.Global, ast.Nonlocal]
if hy._compat.PY3_10:
    _NodeT = Union[_NodeT, ast.MatchAs, ast.MatchStar, ast.MatchMapping]


class NodeRef:
    """
    Wrapper for AST nodes that have symbol names, so that we can rename them if
    necessary. Each `NodeRef` corresponds to one Python identifier. `ast` nodes
    that accept multiple identifier names (`global`, `nonlocal`, etc) have
    their specific identifier referenced by their `index` in the list of
    `names` provided by the `ast` node.
    """

    node: _NodeT
    index: Optional[int]
    _accessor: str

    ACCESSOR = {
        ast.Name: "id",
        ast.Global: "names",
        ast.Nonlocal: "names",
    }
    if hy._compat.PY3_10:
        ACCESSOR.update(
            {
                ast.MatchAs: "name",
                ast.MatchStar: "name",
                ast.MatchMapping: "rest",
            }
        )

    def __init__(self, node: _NodeT, index: Optional[int] = None):
        self.node = node
        self.index = index
        self._accessor = NodeRef.ACCESSOR[type(self.node)]

    @property
    def name(self) -> str:
        res = getattr(self.node, self._accessor)
        if self.index is not None:
            return res[self.index]
        return res

    @name.setter
    def name(self, new_name: str) -> None:
        "Used to rename `ast` identifiers"
        if self.index is not None:
            getattr(self.node, self._accessor)[self.index] = new_name
        else:
            setattr(self.node, self._accessor, new_name)

    @staticmethod
    def wrap(f):
        "Decorator to convert AST node parameter to NodeRef."

        def _wrapper(self, node: _NodeT, index: Optional[int] = None):
            if not isinstance(node, NodeRef):
                node = NodeRef(node, index)
            return f(self, node)

        return _wrapper

    def __repr__(self):
        return (
            f"NodeRef(name={self.name}, node={type(self.node).__name__},"
            f" index={self.index})"
        )


_ScopeBaseT = TypeVar("_ScopeBaseT", bound="ScopeBase")


class ScopeBase(ABC):
    parent: Optional[ScopeBase]
    compiler: _CompilerT

    def __init__(self, compiler: _CompilerT):
        self.parent = None
        self.compiler = compiler

    def create(self, scope_type: Type[_ScopeBaseT], *args) -> _ScopeBaseT:
        "Create new scope from this one."
        return scope_type(self.compiler, *args)

    def __enter__(self):
        self.parent = self.compiler.scope
        self.compiler.scope = self
        return self

    def __exit__(self, *args):
        assert self.parent is not None
        self.compiler.scope = self.parent
        self.parent = None
        return False

    # Scope interface
    @abstractmethod
    def access(self, node, index=None):
        "Called when a symbol is accessed."
        ...

    @abstractmethod
    def assign(self, node: _NodeT, index=None):
        "Called when a symbol is assigned to."
        ...

    @abstractmethod
    def define(self, name):
        """
        Called when a symbol is defined.
        (e.g., function names, class names, imports)
        """
        ...

    @abstractmethod
    def define_nonlocal(self, node, root):
        "Called when a symbol is declared nonlocal or global."
        ...


class ScopeGlobal(ScopeBase):
    """Global scope."""

    defined: SetT
    """All symbols created or assigned in this scope."""

    nonlocal_vars: ListT
    """List of all `nonlocal`s defined in this scope.

    Deliberately not a `set` so we can maintain the order they were defined in.
    """

    def __init__(self, compiler: _CompilerT):
        super().__init__(compiler)
        self.defined = set()
        self.nonlocal_vars = []

    def __exit__(self, *args):
        nonlocal_vars = self.nonlocal_vars
        self.nonlocal_vars = []
        if not self.defined.issuperset(nonlocal_vars):
            raise SyntaxError(f"no binding for nonlocal '{nonlocal_vars[0]}'")
        return super().__exit__(*args)

    @NodeRef.wrap
    def access(self, node: NodeRef, index: int = 0):
        return node.node

    @NodeRef.wrap
    def assign(self, node: NodeRef):
        self.define(node.name)
        return node.node

    def define(self, name):
        self.defined.add(name)

    def define_nonlocal(self, node, root):
        if root == "nonlocal":
            self.nonlocal_vars.extend(node.names)
        else:
            self.defined.update(node.names)


class ScopeLet(ScopeBase):
    """
    Scope that supports let-binding by renaming bound symbols as they are
    accessed/assigned. Defined symbols are never renamed.
    """

    def __init__(self, compiler):
        super().__init__(compiler)
        self.bindings = {}

    def _rename_if_bound(self, node):
        if node.name in self.bindings:
            node.name = self.bindings[node.name]
            return True
        return False

    @NodeRef.wrap
    def access(self, node):
        assert self.parent is not None
        self._rename_if_bound(node) or self.parent.access(node)
        return node.node

    @NodeRef.wrap
    def assign(self, node):
        assert self.parent is not None
        self._rename_if_bound(node) or self.parent.assign(node)
        return node.node

    def define(self, name):
        self.bindings.pop(name, None)
        self.parent.define(name)

    def define_nonlocal(self, node, root):
        # remove nonlocal defs of any let scopes in this Python scope
        cur = self
        while isinstance(cur, ScopeLet):
            for name in node.names:
                if root == "nonlocal":
                    if name in cur.bindings and cur is not self:
                        node.names.remove(name)
                else:
                    cur.bindings[name] = name
            cur = cur.parent
        cur.define_nonlocal(node, root)

    def add(self, target, new_name=None):
        """Add a new let-binding target, mapped to a new, unique name."""
        if isinstance(target, (str, Symbol)):
            if "." in target:
                raise ValueError("binding target may not contain a dot")
            name = mangle(target)
            if new_name is None:
                new_name = self.compiler.get_anon_var(f"_hy_let_{name}")
            self.bindings[name] = new_name
            if isinstance(target, Symbol):
                return Symbol(new_name).replace(target)
            return new_name
        if new_name is not None:
            raise ValueError("cannot specify name for compound targets")
        if isinstance(target, List):
            return List(map(self.add, target)).replace(target)
        if (
            isinstance(target, Expression)
            and target
            and target[0] in (Symbol(","), Symbol("unpack-iterable"))
        ):
            return Expression([target[0], *map(self.add, target[1:])]).replace(target)
        raise ValueError(f"invalid binding target: {type(target)}")


class ScopeFn(ScopeBase):
    """Scope that corresponds to Python's own function or class scopes."""

    defined: SetT
    """All vars defined in this scope."""

    seen: ListT
    """All vars accessed in this scope."""

    nonlocal_vars: SetT
    """All `nonlocal`s defined in this scope."""

    is_fn: bool
    """Whether this scope is used to track a Python function.

    `True` if this scope _is_ being used to track a Python function.
    `False` if tracking a class.
    """

    def __init__(self, compiler: _CompilerT, args: Optional[ast.arguments] = None):
        super().__init__(compiler)

        self.defined = set()
        self.seen = []
        self.nonlocal_vars = set()
        self.is_fn = args is not None

        if args:
            for arg in itertools.chain(
                args.args, args.posonlyargs, args.kwonlyargs, [args.vararg, args.kwarg]
            ):
                if arg:
                    self.define(arg.arg)

    def __exit__(self, *args):
        for node in self.seen:
            if node.name not in self.defined or node.name in self.nonlocal_vars:
                # pass unbound/nonlocal names up to parent scope
                assert self.parent is not None
                self.parent.access(node)
        return super().__exit__(*args)

    @NodeRef.wrap
    def access(self, node):
        self.seen.append(node)
        return node.node

    @NodeRef.wrap
    def assign(self, node):
        self.access(node)
        self.define(node.name)
        return node.node

    def define(self, name):
        self.defined.add(name)

    def define_nonlocal(self, node: NodeRef, root: str):
        (
            (self.nonlocal_vars if root == "nonlocal" else self.defined).update(
                node.names
            )
        )
        for n in self.seen:
            if n.name in node.names:
                raise SyntaxError(
                    f"name '{n.name}' is declared {root} after being used"
                )
        if root == "nonlocal":
            # toss all nonlocal names up to parent scope
            assert self.parent is not None
            for i in range(len(node.names)):
                self.parent.access(node, i)


class ScopeGen(ScopeFn):
    """
    Scope that supports generator forms (`lfor`, `gfor`, ...). If this scope is
    contained within a function scope or the global scope, then any variable
    assignments are "leaked out" to the parent scope, mimicking Python's inline
    generator semantics.

    .. note::
       see :pep:`572#why-not-use-a-sublocal-scope-and-prevent-namespace-pollution`
       for more details on how and when variables are leaked into enclosing scopes.
    """

    def __init__(self, compiler):
        super().__init__(compiler)
        self.iterators = set()
        self.assignments = []
        self.nonlocals = set()
        self.exposing_assignments = False

    def __enter__(self):
        super().__enter__()
        enclosing = nearest_python_scope(self.parent)
        if isinstance(enclosing, ScopeGlobal) or is_function_scope(enclosing):
            # only "leak out" assignments if we're contained in a function
            # (or global) scope
            self.exposing_assignments = True
        return self

    def finalize(self):
        """
        Access and return all the identifiers created and potentially leaked
        out by this generator. This should be called once and only once we've
        processed all of the iterators in this generators so as not to leak out
        any unwanted identifiers
        """
        res = set()
        for node in self.assignments:
            if node.name not in self.nonlocal_vars:
                assert self.parent is not None
                self.parent.access(node)
                res.add(node.name)
        return sorted(res)

    @NodeRef.wrap
    def assign(self, node):
        self.access(node)
        if node.name not in self.defined:
            self.assignments.append(node)
        return node.node

    def iterator(self, target):
        """
        Declare an iteration variable name for this scope; as in Python, the
        iteration variable(s) cannot be reassigned.
        """
        self.iterators.update(
            name.id for name in ast.walk(target) if isinstance(name, ast.Name)
        )
        # remove potentially leakable identifiers that were actually iteration
        # variables found in `target`
        self.assignments = [
            node for node in self.assignments if node.name not in self.iterators
        ]
        self.seen = [node for node in self.seen if node.name not in self.iterators]
