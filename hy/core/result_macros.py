# Copyright 2021 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.

"""This file contains Hy's core macros that are written in Python and
return compiler Result objects (or Python AST objects) rather than Hy
model trees. These macros serve the role of special forms in other
Lisps: all ordinary macros should eventually compile down to one of
these, or to one of the model builders in hy.compiler."""

# ------------------------------------------------
# * Imports
# ------------------------------------------------

import ast, keyword, textwrap
from itertools import dropwhile

from funcparserlib.parser import (some, many, oneplus, maybe,
    forward_decl)

from hy.models import (Expression, Keyword, Integer, Complex, String,
    FComponent, FString, Bytes, Symbol, Float, List, Dict, Sequence,
    is_unpack)
from hy.model_patterns import (FORM, SYM, KEYWORD, STR, LITERAL, sym,
    brackets, notpexpr, dolike, pexpr, times, Tag, tag, unpack, braces)
from hy.lex import mangle, unmangle
from hy.macros import pattern_macro, require
from hy.errors import (HyTypeError, HyEvalError, HyInternalError)
from hy.compiler import Result, asty, mkexpr, hy_eval

# ------------------------------------------------
# * Helpers
# ------------------------------------------------

Inf = float('inf')

def pvalue(root, wanted):
    return pexpr(sym(root) + wanted) >> (lambda x: x[0])

# Parse an annotation setting.
OPTIONAL_ANNOTATION = maybe(pvalue("annotate", FORM))

# ------------------------------------------------
# * Fundamentals
# ------------------------------------------------

@pattern_macro("do", [many(FORM)])
def compile_do(self, expr, root, body):
    return self._compile_branch(body)

@pattern_macro(["eval-and-compile", "eval-when-compile"], [many(FORM)])
def compile_eval_and_compile(compiler, expr, root, body):
    new_expr = Expression([Symbol("do").replace(expr[0])]).replace(expr)

    try:
        hy_eval(new_expr + body,
                compiler.module.__dict__,
                compiler.module,
                filename=compiler.filename,
                source=compiler.source,
                import_stdlib=False)
    except HyInternalError:
        # Unexpected "meta" compilation errors need to be treated
        # like normal (unexpected) compilation errors at this level
        # (or the compilation level preceding this one).
        raise
    except Exception as e:
        # These could be expected Hy language errors (e.g. syntax errors)
        # or regular Python runtime errors that do not signify errors in
        # the compilation *process* (although compilation did technically
        # fail).
        # We wrap these exceptions and pass them through.
        raise HyEvalError(str(e), compiler.filename, body, compiler.source)

    return (compiler._compile_branch(body)
            if mangle(root) == "eval_and_compile"
            else Result())

@pattern_macro(["py", "pys"], [STR])
def compile_inline_python(compiler, expr, root, code):
    exec_mode = root == "pys"

    try:
        o = ast.parse(
            textwrap.dedent(code) if exec_mode else code,
            compiler.filename,
            'exec' if exec_mode else 'eval').body
    except (SyntaxError, ValueError) as e:
        raise compiler._syntax_error(
            expr,
            "Python parse error in '{}': {}".format(root, e))

    return Result(stmts=o) if exec_mode else o

# ------------------------------------------------
# * Quoting
# ------------------------------------------------

@pattern_macro(["quote", "quasiquote"], [FORM])
def compile_quote(compiler, expr, root, arg):
    level = Inf if root == "quote" else 0   # Only quasiquotes can unquote
    stmts, _ = render_quoted_form(compiler, arg, level)
    ret = compiler.compile(stmts)
    return ret

def render_quoted_form(compiler, form, level):
    """
    Render a quoted form as a new hy Expression.

    `level` is the level of quasiquoting of the current form. We can
    unquote if level is 0.

    Returns a two-tuple (`expression`, `splice`).

    The `splice` return value is used to mark `unquote-splice`d forms.
    We need to distinguish them as want to concatenate them instead of
    just nesting them.
    """

    op = None
    if isinstance(form, Expression) and form and isinstance(form[0], Symbol):
        op = unmangle(mangle(form[0]))
    if level == 0 and op in ("unquote", "unquote-splice"):
        if len(form) != 2:
            raise HyTypeError("`%s' needs 1 argument, got %s" % op, len(form) - 1,
                              compiler.filename, form, compiler.source)
        return form[1], op == "unquote-splice"
    elif op == "quasiquote":
        level += 1
    elif op in ("unquote", "unquote-splice"):
        level -= 1

    hytype = form.__class__
    name = ".".join((hytype.__module__, hytype.__name__))
    body = [form]

    if isinstance(form, Sequence):
        contents = []
        for x in form:
            f_contents, splice = render_quoted_form(compiler, x, level)
            if splice:
                contents.append(Expression([
                    Symbol("list"),
                    Expression([Symbol("or"), f_contents, List()])]))
            else:
                contents.append(List([f_contents]))
        if form:
            # If there are arguments, they can be spliced
            # so we build a sum...
            body = [Expression([Symbol("+"), List()] + contents)]
        else:
            body = [List()]

        if isinstance(form, FString) and form.brackets is not None:
            body.extend([Keyword("brackets"), form.brackets])
        elif isinstance(form, FComponent) and form.conversion is not None:
            body.extend([Keyword("conversion"), String(form.conversion)])

    elif isinstance(form, Symbol):
        body = [String(form)]

    elif isinstance(form, Keyword):
        body = [String(form.name)]

    elif isinstance(form, String):
        if form.brackets is not None:
            body.extend([Keyword("brackets"), form.brackets])

    ret = Expression([Symbol(name)] + body).replace(form)
    return ret, False

# ------------------------------------------------
# * Python operators
# ------------------------------------------------

@pattern_macro(["not", "~"], [FORM], shadow = True)
def compile_unary_operator(compiler, expr, root, arg):
    ops = {"not": ast.Not,
           "~": ast.Invert}
    operand = compiler.compile(arg)
    return operand + asty.UnaryOp(
        expr, op=ops[root](), operand=operand.force_expr)

@pattern_macro(["and", "or"], [many(FORM)], shadow = True)
def compile_logical_or_and_and_operator(compiler, expr, operator, args):
    ops = {"and": (ast.And, True),
           "or": (ast.Or, None)}
    opnode, default = ops[operator]
    osym = expr[0]
    if len(args) == 0:
        return asty.Constant(osym, value=default)
    elif len(args) == 1:
        return compiler.compile(args[0])
    ret = Result()
    values = list(map(compiler.compile, args))
    if any(value.stmts for value in values):
        # Compile it to an if...else sequence
        var = compiler.get_anon_var()
        name = asty.Name(osym, id=var, ctx=ast.Store())
        expr_name = asty.Name(osym, id=var, ctx=ast.Load())
        temp_variables = [name, expr_name]

        def make_assign(value, node=None):
            positioned_name = asty.Name(
                node or osym, id=var, ctx=ast.Store())
            temp_variables.append(positioned_name)
            return asty.Assign(
                node or osym, targets=[positioned_name], value=value)

        current = root = []
        for i, value in enumerate(values):
            if value.stmts:
                node = value.stmts[0]
                current.extend(value.stmts)
            else:
                node = value.expr
            current.append(make_assign(value.force_expr, value.force_expr))
            if i == len(values)-1:
                # Skip a redundant 'if'.
                break
            if operator == "and":
                cond = expr_name
            elif operator == "or":
                cond = asty.UnaryOp(node, op=ast.Not(), operand=expr_name)
            current.append(asty.If(node, test=cond, body=[], orelse=[]))
            current = current[-1].body
        ret = sum(root, ret)
        ret += Result(expr=expr_name, temp_variables=temp_variables)
    else:
        ret += asty.BoolOp(osym,
                           op=opnode(),
                           values=[value.force_expr for value in values])
    return ret

c_ops = {"=": ast.Eq, "!=": ast.NotEq,
         "<": ast.Lt, "<=": ast.LtE,
         ">": ast.Gt, ">=": ast.GtE,
         "is": ast.Is, "is-not": ast.IsNot,
         "in": ast.In, "not-in": ast.NotIn}
c_ops = {mangle(k): v for k, v in c_ops.items()}

def get_c_op(compiler, sym):
    k = mangle(sym)
    if k not in c_ops:
        raise compiler._syntax_error(sym,
            "Illegal comparison operator: " + str(sym))
    return c_ops[k]()

@pattern_macro(["=", "is", "<", "<=", ">", ">="], [oneplus(FORM)],
    shadow = True)
@pattern_macro(["!=", "is-not", "in", "not-in"], [times(2, Inf, FORM)],
    shadow = True)
def compile_compare_op_expression(compiler, expr, root, args):
    if len(args) == 1:
        return (compiler.compile(args[0]) +
                asty.Constant(expr, value=True))

    ops = [get_c_op(compiler, root) for _ in args[1:]]
    exprs, ret, _ = compiler._compile_collect(args)
    return ret + asty.Compare(
        expr, left=exprs[0], ops=ops, comparators=exprs[1:])

@pattern_macro("chainc", [FORM, many(SYM + FORM)])
def compile_chained_comparison(compiler, expr, root, arg1, args):
    ret = compiler.compile(arg1)
    arg1 = ret.force_expr

    ops = [get_c_op(compiler, op) for op, _ in args]
    args, ret2, _ = compiler._compile_collect(
        [x for _, x in args])

    return ret + ret2 + asty.Compare(expr,
        left=arg1, ops=ops, comparators=args)

# The second element of each tuple below is an aggregation operator
# that's used for augmented assignment with three or more arguments.
m_ops = {"+": (ast.Add, "+"),
         "/": (ast.Div, "*"),
         "//": (ast.FloorDiv, "*"),
         "*": (ast.Mult, "*"),
         "-": (ast.Sub, "+"),
         "%": (ast.Mod, None),
         "**": (ast.Pow, "**"),
         "<<": (ast.LShift, "+"),
         ">>": (ast.RShift, "+"),
         "|": (ast.BitOr, "|"),
         "^": (ast.BitXor, None),
         "&": (ast.BitAnd, "&"),
         "@": (ast.MatMult, "@")}

@pattern_macro(["+", "*", "|"], [many(FORM)], shadow = True)
@pattern_macro(["-", "/", "&", "@"], [oneplus(FORM)], shadow = True)
@pattern_macro(["**", "//", "<<", ">>"], [times(2, Inf, FORM)], shadow = True)
@pattern_macro(["%", "^"], [times(2, 2, FORM)], shadow = True)
def compile_maths_expression(compiler, expr, root, args):
    if len(args) == 0:
        # Return the identity element for this operator.
        return asty.Num(expr, n=(
            {"+": 0, "|": 0, "*": 1}[root]))

    if len(args) == 1:
        if root == "/":
            # Compute the reciprocal of the argument.
            args = [Integer(1).replace(expr), args[0]]
        elif root in ("+", "-"):
            # Apply unary plus or unary minus to the argument.
            op = {"+": ast.UAdd, "-": ast.USub}[root]()
            ret = compiler.compile(args[0])
            return ret + asty.UnaryOp(expr, op=op, operand=ret.force_expr)
        else:
            # Return the argument unchanged.
            return compiler.compile(args[0])

    op = m_ops[root][0]
    right_associative = root == "**"
    ret = compiler.compile(args[-1 if right_associative else 0])
    for child in args[-2 if right_associative else 1 ::
                      -1 if right_associative else 1]:
        left_expr = ret.force_expr
        ret += compiler.compile(child)
        right_expr = ret.force_expr
        if right_associative:
            left_expr, right_expr = right_expr, left_expr
        ret += asty.BinOp(expr, left=left_expr, op=op(), right=right_expr)

    return ret

a_ops = {x + "=": v for x, v in m_ops.items()}

@pattern_macro([x for x, (_, v) in a_ops.items() if v is not None], [FORM, oneplus(FORM)])
@pattern_macro([x for x, (_, v) in a_ops.items() if v is None], [FORM, times(1, 1, FORM)])
def compile_augassign_expression(compiler, expr, root, target, values):
    if len(values) > 1:
        return compiler.compile(mkexpr(root, [target],
            mkexpr(a_ops[root][1], rest=values)).replace(expr))

    op = a_ops[root][0]
    target = compiler._storeize(target, compiler.compile(target))
    ret = compiler.compile(values[0])
    return ret + asty.AugAssign(
        expr, target=target, value=ret.force_expr, op=op())

# ------------------------------------------------
# * Assignment, mutation, and annotation
# ------------------------------------------------

@pattern_macro("setv", [many(OPTIONAL_ANNOTATION + FORM + FORM)])
@pattern_macro(((3, 8), "setx"), [times(1, 1, SYM + FORM)])
def compile_def_expression(compiler, expr, root, decls):
    if not decls:
        return asty.Constant(expr, value=None)

    result = Result()
    is_assignment_expr = root == "setx"
    for decl in decls:
        if is_assignment_expr:
            ann = None
            name, value = decl
        else:
            ann, name, value = decl

        result += compile_assign(compiler, ann, name, value,
            is_assignment_expr=is_assignment_expr)
    return result

@pattern_macro(["annotate"], [FORM, FORM])
def compile_basic_annotation(compiler, expr, root, ann, target):
    return compile_assign(compiler, ann, target, None)

def compile_assign(compiler, ann, name, value, *, is_assignment_expr = False):
    # Ensure that assignment expressions have a result and no annotation.
    assert not is_assignment_expr or (value is not None and ann is None)

    ld_name = compiler.compile(name)

    annotate_only = value is None
    if annotate_only:
        result = Result()
    else:
        result = compiler.compile(value)

    if (result.temp_variables
            and isinstance(name, Symbol)
            and '.' not in name):
        result.rename(compiler._nonconst(name))
        if not is_assignment_expr:
            # Throw away .expr to ensure that (setv ...) returns None.
            result.expr = None
    else:
        st_name = compiler._storeize(name, ld_name)

        if ann is not None:
            ann_result = compiler.compile(ann)
            result = ann_result + result

        if is_assignment_expr:
            node = asty.NamedExpr
        elif ann is not None:
            node = lambda x, **kw: asty.AnnAssign(x, annotation=ann_result.force_expr,
                                                  simple=int(isinstance(name, Symbol)),
                                                  **kw)
        else:
            node = asty.Assign

        result += node(
            name if hasattr(name, "start_line") else result,
            value=result.force_expr if not annotate_only else None,
            target=st_name, targets=[st_name])

    return result

@pattern_macro(["global", "nonlocal"], [oneplus(SYM)])
def compile_global_or_nonlocal(compiler, expr, root, syms):
    node = asty.Global if root == "global" else asty.Nonlocal
    return node(expr, names=list(map(mangle, syms)))

@pattern_macro("del", [many(FORM)])
def compile_del_expression(compiler, expr, name, args):
    if not args:
        return asty.Pass(expr)

    del_targets = []
    ret = Result()
    for target in args:
        compiled_target = compiler.compile(target)
        ret += compiled_target
        del_targets.append(compiler._storeize(target, compiled_target,
                                          ast.Del))

    return ret + asty.Delete(expr, targets=del_targets)

# ------------------------------------------------
# * Subsetting
# ------------------------------------------------

@pattern_macro("get", [FORM, oneplus(FORM)], shadow = True)
def compile_index_expression(compiler, expr, name, obj, indices):
    indices, ret, _ = compiler._compile_collect(indices)
    ret += compiler.compile(obj)

    for ix in indices:
        ret += asty.Subscript(
            expr,
            value=ret.force_expr,
            slice=ast.Index(value=ix),
            ctx=ast.Load())

    return ret

@pattern_macro(".", [FORM, many(SYM | brackets(FORM))])
def compile_attribute_access(compiler, expr, name, invocant, keys):
    ret = compiler.compile(invocant)

    for attr in keys:
        if isinstance(attr, Symbol):
            ret += asty.Attribute(attr,
                                  value=ret.force_expr,
                                  attr=mangle(attr),
                                  ctx=ast.Load())
        else: # attr is a hy List
            compiled_attr = compiler.compile(attr[0])
            ret = compiled_attr + ret + asty.Subscript(
                attr,
                value=ret.force_expr,
                slice=ast.Index(value=compiled_attr.force_expr),
                ctx=ast.Load())

    return ret

@pattern_macro("cut", [FORM, maybe(FORM), maybe(FORM), maybe(FORM)])
def compile_cut_expression(compiler, expr, name, obj, lower, upper, step):
    ret = [Result()]
    def c(e):
        ret[0] += compiler.compile(e)
        return ret[0].force_expr

    if upper is None:
        # cut with single index is an upper bound,
        # this is consistent with slice and islice
        upper = lower
        lower = Symbol('None')

    s = asty.Subscript(
        expr,
        value=c(obj),
        slice=asty.Slice(expr,
            lower=c(lower), upper=c(upper), step=c(step)),
        ctx=ast.Load())
    return ret[0] + s

@pattern_macro("unpack-iterable", [FORM])
def compile_unpack_iterable(compiler, expr, root, arg):
    ret = compiler.compile(arg)
    ret += asty.Starred(expr, value=ret.force_expr, ctx=ast.Load())
    return ret

# ------------------------------------------------
# * `if`
# ------------------------------------------------

@pattern_macro("if", [FORM, FORM, maybe(FORM)])
def compile_if(compiler, expr, _, cond, body, orel_expr):
    cond = compiler.compile(cond)
    body = compiler.compile(body)

    nested = root = False
    orel = Result()
    if orel_expr is not None:
        if isinstance(orel_expr, Expression) and isinstance(orel_expr[0],
           Symbol) and orel_expr[0] == Symbol('if*'):
            # Nested ifs: don't waste temporaries
            root = compiler.temp_if is None
            nested = True
            compiler.temp_if = compiler.temp_if or compiler.get_anon_var()
        orel = compiler.compile(orel_expr)

    if not cond.stmts and isinstance(cond.force_expr, ast.Name):
        name = cond.force_expr.id
        branch = None
        if name == 'True':
            branch = body
        elif name in ('False', 'None'):
            branch = orel
        if branch is not None:
            if compiler.temp_if and branch.stmts:
                name = asty.Name(expr,
                                 id=mangle(compiler.temp_if),
                                 ctx=ast.Store())

                branch += asty.Assign(expr,
                                      targets=[name],
                                      value=body.force_expr)

            return branch

    # We want to hoist the statements from the condition
    ret = cond

    if body.stmts or orel.stmts:
        # We have statements in our bodies
        # Get a temporary variable for the result storage
        var = compiler.temp_if or compiler.get_anon_var()
        name = asty.Name(expr,
                         id=mangle(var),
                         ctx=ast.Store())

        # Store the result of the body
        body += asty.Assign(expr,
                            targets=[name],
                            value=body.force_expr)

        # and of the else clause
        if not nested or not orel.stmts or (not root and
           var != compiler.temp_if):
            orel += asty.Assign(expr,
                                targets=[name],
                                value=orel.force_expr)

        # Then build the if
        ret += asty.If(expr,
                       test=ret.force_expr,
                       body=body.stmts,
                       orelse=orel.stmts)

        # And make our expression context our temp variable
        expr_name = asty.Name(expr, id=mangle(var), ctx=ast.Load())

        ret += Result(expr=expr_name, temp_variables=[expr_name, name])
    else:
        # Just make that an if expression
        ret += asty.IfExp(expr,
                          test=ret.force_expr,
                          body=body.force_expr,
                          orelse=orel.force_expr)

    if root:
        compiler.temp_if = None

    return ret

# ------------------------------------------------
# * The `for` family
# ------------------------------------------------

loopers = many(
    tag('setv', sym(":setv") + FORM + FORM) |
    tag('if', sym(":if") + FORM) |
    tag('do', sym(":do") + FORM) |
    tag('afor', sym(":async") + FORM + FORM) |
    tag('for', FORM + FORM))

@pattern_macro(["for"], [brackets(loopers),
    many(notpexpr("else")) + maybe(dolike("else"))])
@pattern_macro(["lfor", "sfor", "gfor"], [loopers, FORM])
@pattern_macro(["dfor"], [loopers, brackets(FORM, FORM)])
def compile_comprehension(compiler, expr, root, parts, final):
    node_class = {
        "for":  asty.For,
        "lfor": asty.ListComp,
        "dfor": asty.DictComp,
        "sfor": asty.SetComp,
        "gfor": asty.GeneratorExp}[root]
    is_for = root == "for"

    orel = []
    if is_for:
        # Get the `else`.
        body, else_expr = final
        if else_expr is not None:
            orel.append(compiler._compile_branch(else_expr))
            orel[0] += orel[0].expr_as_stmt()
    else:
        # Get the final value (and for dictionary
        # comprehensions, the final key).
        if node_class is asty.DictComp:
            key, elt = map(compiler.compile, final)
        else:
            key = None
            elt = compiler.compile(final)

    # Compile the parts.
    if is_for:
        parts = parts[0]
    if not parts:
        return Result(expr=ast.parse({
            asty.For: "None",
            asty.ListComp: "[]",
            asty.DictComp: "{}",
            asty.SetComp: "{1}.__class__()",
            asty.GeneratorExp: "(_ for _ in [])"}[node_class]).body[0].value)
    parts = [
        Tag(p.tag, compiler.compile(p.value) if p.tag in ["if", "do"] else [
            compiler._storeize(p.value[0], compiler.compile(p.value[0])),
            compiler.compile(p.value[1])])
        for p in parts]

    # Produce a result.
    if (is_for or elt.stmts or (key is not None and key.stmts) or
        any(p.tag == 'do' or (p.value[1].stmts if p.tag in ("for", "afor", "setv") else p.value.stmts)
            for p in parts)):
        # The desired comprehension can't be expressed as a
        # real Python comprehension. We'll write it as a nested
        # loop in a function instead.
        def f(parts):
            # This function is called recursively to construct
            # the nested loop.
            if not parts:
                if is_for:
                    if body:
                        bd = compiler._compile_branch(body)
                        return bd + bd.expr_as_stmt()
                    return Result(stmts=[asty.Pass(expr)])
                if node_class is asty.DictComp:
                    ret = key + elt
                    val = asty.Tuple(
                        key, ctx=ast.Load(),
                        elts=[key.force_expr, elt.force_expr])
                else:
                    ret = elt
                    val = elt.force_expr
                return ret + asty.Expr(
                    elt, value=asty.Yield(elt, value=val))
            (tagname, v), parts = parts[0], parts[1:]
            if tagname in ("for", "afor"):
                orelse = orel and orel.pop().stmts
                node = asty.AsyncFor if tagname == "afor" else asty.For
                return v[1] + node(
                    v[1], target=v[0], iter=v[1].force_expr, body=f(parts).stmts,
                    orelse=orelse)
            elif tagname == "setv":
                return v[1] + asty.Assign(
                    v[1], targets=[v[0]], value=v[1].force_expr) + f(parts)
            elif tagname == "if":
                return v + asty.If(
                    v, test=v.force_expr, body=f(parts).stmts, orelse=[])
            elif tagname == "do":
                return v + v.expr_as_stmt() + f(parts)
            else:
                raise ValueError("can't happen")
        if is_for:
            return f(parts)
        fname = compiler.get_anon_var()
        # Define the generator function.
        ret = Result() + asty.FunctionDef(
            expr,
            name=fname,
            args=ast.arguments(
                args=[], vararg=None, kwarg=None, posonlyargs=[],
                kwonlyargs=[], kw_defaults=[], defaults=[]),
            body=f(parts).stmts,
            decorator_list=[])
        # Immediately call the new function. Unless the user asked
        # for a generator, wrap the call in `[].__class__(...)` or
        # `{}.__class__(...)` or `{1}.__class__(...)` to get the
        # right type. We don't want to just use e.g. `list(...)`
        # because the name `list` might be rebound.
        return ret + Result(expr=ast.parse(
            "{}({}())".format(
                {asty.ListComp: "[].__class__",
                 asty.DictComp: "{}.__class__",
                 asty.SetComp: "{1}.__class__",
                 asty.GeneratorExp: ""}[node_class],
                fname)).body[0].value)

    # We can produce a real comprehension.
    generators = []
    for tagname, v in parts:
        if tagname in ("for", "afor"):
            generators.append(ast.comprehension(
                target=v[0], iter=v[1].expr, ifs=[],
                is_async=int(tagname == "afor")))
        elif tagname == "setv":
            generators.append(ast.comprehension(
                target=v[0],
                iter=asty.Tuple(v[1], elts=[v[1].expr], ctx=ast.Load()),
                ifs=[], is_async=0))
        elif tagname == "if":
            generators[-1].ifs.append(v.expr)
        else:
            raise ValueError("can't happen")
    if node_class is asty.DictComp:
        return asty.DictComp(expr, key=key.expr, value=elt.expr, generators=generators)
    return node_class(expr, elt=elt.expr, generators=generators)

# ------------------------------------------------
# * More looping
# ------------------------------------------------

@pattern_macro(["while"], [FORM, many(notpexpr("else")), maybe(dolike("else"))])
def compile_while_expression(compiler, expr, root, cond, body, else_expr):
    cond_compiled = compiler.compile(cond)

    body = compiler._compile_branch(body)
    body += body.expr_as_stmt()
    body_stmts = body.stmts or [asty.Pass(expr)]

    if cond_compiled.stmts:
        # We need to ensure the statements for the condition are
        # executed on every iteration. Rewrite the loop to use a
        # single anonymous variable as the condition, i.e.:
        #  anon_var = True
        #  while anon_var:
        #    condition stmts...
        #    anon_var = condition expr
        #    if anon_var:
        #      while loop body
        cond_var = asty.Name(cond, id=compiler.get_anon_var(), ctx=ast.Load())
        def make_not(operand):
            return asty.UnaryOp(cond, op=ast.Not(), operand=operand)

        body_stmts = cond_compiled.stmts + [
            asty.Assign(cond, targets=[compiler._storeize(cond, cond_var)],
                        # Cast the condition to a bool in case it's mutable and
                        # changes its truth value, but use (not (not ...)) instead of
                        # `bool` in case `bool` has been redefined.
                        value=make_not(make_not(cond_compiled.force_expr))),
            asty.If(cond, test=cond_var, body=body_stmts, orelse=[]),
        ]

        cond_compiled = (Result()
            + asty.Assign(cond, targets=[compiler._storeize(cond, cond_var)],
                          value=asty.Constant(cond, value=True))
            + cond_var)

    orel = Result()
    if else_expr is not None:
        orel = compiler._compile_branch(else_expr)
        orel += orel.expr_as_stmt()

    ret = cond_compiled + asty.While(
        expr, test=cond_compiled.force_expr,
        body=body_stmts,
        orelse=orel.stmts)

    return ret

@pattern_macro(["break", "continue"], [])
def compile_break_or_continue_expression(compiler, expr, root):
    return (asty.Break if root == "break" else asty.Continue)(expr)

# ------------------------------------------------
# * `with`
# ------------------------------------------------

@pattern_macro(["with", "with/a"], [
    brackets(times(1, Inf, FORM + FORM)) |
        brackets((FORM >> (lambda x: [(Symbol('_'), x)]))),
    many(FORM)])
def compile_with_expression(compiler, expr, root, args, body):
    body = compiler._compile_branch(body)

    # Store the result of the body in a tempvar
    temp_var = compiler.get_anon_var()
    name = asty.Name(expr, id=mangle(temp_var), ctx=ast.Store())
    body += asty.Assign(expr, targets=[name], value=body.force_expr)
    # Initialize the tempvar to None in case the `with` exits
    # early with an exception.
    initial_assign = asty.Assign(
        expr, targets=[name], value=asty.Constant(expr, value=None))

    ret = Result(stmts=[initial_assign])
    items = []
    for variable, ctx in args[0]:
        ctx = compiler.compile(ctx)
        ret += ctx
        variable = (None
            if variable == Symbol('_')
            else compiler._storeize(variable, compiler.compile(variable)))
        items.append(asty.withitem(expr,
                                   context_expr=ctx.force_expr,
                                   optional_vars=variable))

    node = asty.With if root == "with" else asty.AsyncWith
    ret += node(expr, body=body.stmts, items=items)

    # And make our expression context our temp variable
    expr_name = asty.Name(expr, id=mangle(temp_var), ctx=ast.Load())

    ret += Result(expr=expr_name)
    # We don't give the Result any temp_vars because we don't want
    # Result.rename to touch `name`. Otherwise, initial_assign will
    # clobber any preexisting value of the renamed-to variable.

    return ret

# ------------------------------------------------
# * `switch`
# ------------------------------------------------

notsym = lambda *dissallowed: some(
    lambda x: isinstance(x, Symbol) and str(x) not in dissallowed
)
keepsym = lambda wanted: some(lambda x: x == Symbol(wanted))
_pattern = forward_decl()
_pattern.define(
    (
        SYM
        | LITERAL
        | brackets(many(_pattern | unpack("iterable")))
        | pexpr(keepsym("."), many(SYM))
        | pexpr(keepsym("|"), many(_pattern))
        | pexpr(keepsym(","), many(_pattern))
        | braces(
            many(LITERAL + _pattern), maybe(pvalue("unpack-mapping", SYM))
        )
        | pexpr(
            notsym(".", "|", ",", "unpack-mapping", "unpack-iterable"),
            many(_pattern),
            many(KEYWORD + _pattern),
        )
    )
    + maybe(sym(":as") + SYM)
)
match_clause = _pattern + maybe(sym(":if") + FORM)

@pattern_macro(
    ((3, 10), "match"), [FORM, many(match_clause + FORM)]
)
def compile_match_expression(compiler, expr, root, subject, clauses):
    subject = compiler.compile(subject)
    return_var = asty.Name(expr, id=mangle(compiler.get_anon_var()), ctx=ast.Store())

    lifted_if_defs = []
    match_cases = []
    for *pattern, guard, body in clauses:
        if guard and body == Keyword("as"):
            raise compiler._syntax_error(body, ":as clause cannot come after :if guard")

        body = compiler._compile_branch([body])
        body += asty.Assign(pattern[0], targets=[return_var], value=body.force_expr)
        body += body.expr_as_stmt()
        body = body.stmts

        pattern = compile_pattern(compiler, pattern)

        if guard:
            guard = compiler.compile(guard)
            if guard.stmts:
                fname = compiler.get_anon_var()
                guardret = Result() + asty.FunctionDef(
                    guard,
                    name=fname,
                    args=ast.arguments(
                        args=[],
                        varargs=None,
                        kwarg=None,
                        posonlyargs=[],
                        kwonlyargs=[],
                        kw_defaults=[],
                        defaults=[],
                    ),
                    body=guard.stmts + [asty.Return(guard.expr, value=guard.expr)],
                    decorator_list=[],
                )
                lifted_if_defs.append(guardret)
                guard = Result(expr=ast.parse(f"{fname}()").body[0].value)

        match_cases.append(
            ast.match_case(
                pattern=pattern,
                guard=guard.force_expr if guard else None,
                body=body,
            )
        )

    returnable = Result(
        expr=asty.Name(expr, id=return_var.id, ctx=ast.Load()),
        temp_variables=[return_var],
    )
    ret = Result() + subject
    ret += subject.expr_as_stmt()
    ret += asty.Assign(expr, targets=[return_var], value=asty.Constant(expr, value=None))
    if not match_cases:
        return ret + returnable

    for lifted_if in lifted_if_defs:
        ret += lifted_if
    ret += asty.Match(expr, subject=subject.force_expr, cases=match_cases)
    return ret + returnable

def compile_pattern(compiler, pattern):
    value, assignment = pattern
    if assignment is not None:
        return asty.MatchAs(
            value,
            pattern=compile_pattern(compiler, (value, None)),
            name=mangle(compiler._nonconst(assignment)),
        )

    if str(value) in ("None", "True", "False"):
        return asty.MatchSingleton(
            value,
            value=compiler.compile(value).force_expr.value,
        )
    elif (
        isinstance(value, (String, Integer, Float, Complex, Bytes))
        or isinstance(value, Symbol)
        and "." in value
    ):
        return asty.MatchValue(
            value,
            value=compiler.compile(value).expr,
        )
    elif value == Symbol("_"):
        return asty.MatchAs(value)
    elif isinstance(value, Symbol):
        return asty.MatchAs(value, name=mangle(value))
    elif isinstance(value, Expression) and value[0] == Symbol("|"):
        return asty.MatchOr(
            value,
            patterns=[compile_pattern(compiler, v) for v in value[1]],
        )
    elif isinstance(value, Expression) and value[0] == Symbol("."):
        root, syms = value
        dotform = mkexpr(root, *syms).replace(value)
        return asty.MatchValue(
            value,
            value=compiler.compile(dotform).expr,
        )
    elif (
        isinstance(value, List)
        or isinstance(value, Expression)
        and value[0] == Symbol(",")
    ):
        patterns = value[0] if isinstance(value, List) else value[1:][0]
        patterns = [
            compile_pattern(compiler, (v, None) if is_unpack("iterable", v) else v)
            for v in patterns
        ]
        return asty.MatchSequence(value, patterns=patterns)
    elif is_unpack("iterable", value):
        return asty.MatchStar(value, name=mangle(value[1]))

    elif isinstance(value, Dict):
        kvs, rest = value
        keys, values = zip(*kvs) if kvs else ([], [])
        return asty.MatchMapping(
            value,
            keys=[compiler.compile(key).expr for key in keys],
            patterns=[compile_pattern(compiler, v) for v in values],
            rest=mangle(rest) if rest else None,
        )
    elif isinstance(value, Expression):
        root, args, kwargs = value
        keywords, values = zip(*kwargs) if kwargs else ([], [])
        return asty.MatchClass(
            value,
            cls=asty.Name(root, id=mangle(root), ctx=ast.Load()),
            patterns=[compile_pattern(compiler, v) for v in args],
            kwd_attrs=[kwd.name for kwd in keywords],
            kwd_patterns=[compile_pattern(compiler, value) for value in values],
        )
    else:
        raise compiler._syntax_error(value, "unsuported")

# ------------------------------------------------
# * `raise` and `try`
# ------------------------------------------------

@pattern_macro("raise", [maybe(FORM), maybe(sym(":from") + FORM)])
def compile_raise_expression(compiler, expr, root, exc, cause):
    ret = Result()

    if exc is not None:
        exc = compiler.compile(exc)
        ret += exc
        exc = exc.force_expr

    if cause is not None:
        cause = compiler.compile(cause)
        ret += cause
        cause = cause.force_expr

    return ret + asty.Raise(
        expr, type=ret.expr, exc=exc,
        inst=None, tback=None, cause=cause)

@pattern_macro("try",
   [many(notpexpr("except", "else", "finally")),
    many(pexpr(sym("except"),
        brackets() | brackets(FORM) | brackets(SYM, FORM),
        many(FORM))),
    maybe(dolike("else")),
    maybe(dolike("finally"))])
def compile_try_expression(compiler, expr, root, body, catchers, orelse, finalbody):
    body = compiler._compile_branch(body)

    return_var = asty.Name(
        expr, id=mangle(compiler.get_anon_var()), ctx=ast.Store())

    handler_results = Result()
    handlers = []
    for catcher in catchers:
        handler_results += compile_catch_expression(
            compiler, catcher, return_var, *catcher)
        handlers.append(handler_results.stmts.pop())

    if orelse is None:
        orelse = []
    else:
        orelse = compiler._compile_branch(orelse)
        orelse += asty.Assign(expr, targets=[return_var],
                              value=orelse.force_expr)
        orelse += orelse.expr_as_stmt()
        orelse = orelse.stmts

    if finalbody is None:
        finalbody = []
    else:
        finalbody = compiler._compile_branch(finalbody)
        finalbody += finalbody.expr_as_stmt()
        finalbody = finalbody.stmts

    # Using (else) without (except) is verboten!
    if orelse and not handlers:
        raise compiler._syntax_error(expr,
            "`try' cannot have `else' without `except'")
    # Likewise a bare (try) or (try BODY).
    if not (handlers or finalbody):
        raise compiler._syntax_error(expr,
            "`try' must have an `except' or `finally' clause")

    returnable = Result(
        expr=asty.Name(expr, id=return_var.id, ctx=ast.Load()),
        temp_variables=[return_var])
    body += body.expr_as_stmt() if orelse else asty.Assign(
        expr, targets=[return_var], value=body.force_expr)
    body = body.stmts or [asty.Pass(expr)]

    x = asty.Try(
        expr,
        body=body,
        handlers=handlers,
        orelse=orelse,
        finalbody=finalbody)
    return handler_results + x + returnable

def compile_catch_expression(compiler, expr, var, exceptions, body):
    # exceptions catch should be either:
    # [[list of exceptions]]
    # or
    # [variable [list of exceptions]]
    # or
    # [variable exception]
    # or
    # [exception]
    # or
    # []

    name = None
    if len(exceptions) == 2:
        name = mangle(compiler._nonconst(exceptions[0]))

    exceptions_list = exceptions[-1] if exceptions else List()
    if isinstance(exceptions_list, List):
        if len(exceptions_list):
            # [FooBar BarFoo] → catch Foobar and BarFoo exceptions
            elts, types, _ = compiler._compile_collect(exceptions_list)
            types += asty.Tuple(exceptions_list, elts=elts, ctx=ast.Load())
        else:
            # [] → all exceptions caught
            types = Result()
    else:
        types = compiler.compile(exceptions_list)

    body = compiler._compile_branch(body)
    body += asty.Assign(expr, targets=[var], value=body.force_expr)
    body += body.expr_as_stmt()

    return types + asty.ExceptHandler(
        expr, type=types.expr, name=name,
        body=body.stmts or [asty.Pass(expr)])

# ------------------------------------------------
# * Functions and macros
# ------------------------------------------------

NASYM = some(lambda x: isinstance(x, Symbol) and x not in (Symbol("/"), Symbol("*")))
argument = OPTIONAL_ANNOTATION + (NASYM | brackets(NASYM, FORM))
varargs = lambda unpack_type, wanted: OPTIONAL_ANNOTATION + pvalue(unpack_type, wanted)
kwonly_delim = some(lambda x: x == Symbol("*"))
lambda_list = brackets(
        maybe(many(argument) + sym("/")),
        many(argument),
        maybe(kwonly_delim | varargs("unpack-iterable", NASYM)),
        many(argument),
        maybe(varargs("unpack-mapping", NASYM)))

@pattern_macro(["fn", "fn/a"], [OPTIONAL_ANNOTATION, lambda_list, many(FORM)])
def compile_function_lambda(compiler, expr, root, returns, params, body):
    posonly, args, rest, kwonly, kwargs = params
    has_annotations = returns is not None or any(
        isinstance(param, tuple) and param[0] is not None
        for param in (posonly or []) + args + kwonly + [rest, kwargs]
    )
    body = compiler._compile_branch(body)

    # Compile to lambda if we can
    if not has_annotations and not body.stmts and root != "fn/a":
        args, ret = compile_lambda_list(compiler, params, Result())
        return ret + asty.Lambda(expr, args=args, body=body.force_expr)

    # Otherwise create a standard function
    node = asty.AsyncFunctionDef if root == "fn/a" else asty.FunctionDef
    name = compiler.get_anon_var()
    ret = compile_function_node(compiler, expr, node, name, params, returns, body)

    # return its name as the final expr
    return ret + Result(expr=ret.temp_variables[0])

@pattern_macro(["defn", "defn/a"], [OPTIONAL_ANNOTATION, SYM, lambda_list, many(FORM)])
def compile_function_def(compiler, expr, root, returns, name, params, body):
    node = asty.FunctionDef if root == "defn" else asty.AsyncFunctionDef
    body = compiler._compile_branch(body)

    return compile_function_node(
        compiler, expr, node,
        mangle(compiler._nonconst(name)), params, returns, body
    )

def compile_function_node(compiler, expr, node, name, params, returns, body):
    ret = Result()
    args, ret = compile_lambda_list(compiler, params, ret)

    if body.expr:
        body += asty.Return(body.expr, value=body.expr)

    ret += node(
        expr,
        name=name,
        args=args,
        body=body.stmts or [asty.Pass(expr)],
        decorator_list=[],
        returns=compiler.compile(returns).force_expr if returns is not None else None,
    )

    ast_name = asty.Name(expr, id=name, ctx=ast.Load())
    return ret + Result(temp_variables=[ast_name, ret.stmts[-1]])

@pattern_macro("defmacro", [SYM | STR, lambda_list, many(FORM)])
def compile_macro_def(compiler, expr, root, name, params, body):
    _, _, rest, _, kwargs = params

    if "." in name:
        raise compiler._syntax_error(name, "periods are not allowed in macro names")
    if rest == Symbol("*"):
        raise compiler._syntax_error(rest, "macros cannot use '*'")
    if kwargs is not None:
        raise compiler._syntax_error(kwargs, "macros cannot use '#**'")

    ret = Result() + compiler.compile(Expression([
        Symbol("eval-and-compile"),
        Expression([
            Expression([
                Symbol("hy.macros.macro"),
                str(name),
            ]),
            Expression([
                Symbol("fn"),
                List([Symbol("&compiler")] + list(expr[2])),
                *body
            ])
        ])
    ]).replace(expr))

    return ret + ret.expr_as_stmt()

def compile_lambda_list(compiler, params, ret):
    posonly_parms, args_parms, rest_parms, kwonly_parms, kwargs_parms = params

    py_reserved_param = next(
        (
            sym
            for param in (
                (posonly_parms or [])
                + args_parms
                + kwonly_parms
                + [rest_parms, kwargs_parms]
            )
            if isinstance(param, tuple)
            for sym in [param[1][0] if isinstance(param[1], List) else param[1]]
            if keyword.iskeyword(str(sym))
        ),
        None,
    )
    if py_reserved_param:
        raise compiler._syntax_error(
            py_reserved_param, "parameter name cannot be Python reserved word"
        )

    if not (posonly_parms or posonly_parms is None):
        raise compiler._syntax_error(
            params, "positional only delimiter '/' must have an argument"
        )

    posonly_parms = posonly_parms or []

    is_positional_arg = lambda x: isinstance(x[1], Symbol)
    invalid_non_default = next(
        (arg
         for arg in dropwhile(is_positional_arg, posonly_parms + args_parms)
         if is_positional_arg(arg)),
        None
    )
    if invalid_non_default:
        raise compiler._syntax_error(
            invalid_non_default[1], "non-default argument follows default argument"
        )

    posonly_ast, posonly_defaults, ret = compile_arguments_set(compiler, posonly_parms, ret)
    args_ast, args_defaults, ret = compile_arguments_set(compiler, args_parms, ret)
    kwonly_ast, kwonly_defaults, ret = compile_arguments_set(compiler, kwonly_parms, ret, True)
    rest_ast = kwargs_ast = None

    if rest_parms == Symbol("*"): # rest is a positional only marker
        if not kwonly_parms:
            raise compiler._syntax_error(rest_parms, "named arguments must follow bare *")
        rest_ast = None
    elif rest_parms: # rest is capturing varargs
        [rest_ast], _, ret = compile_arguments_set(compiler, [rest_parms], ret)
    if kwargs_parms:
        [kwargs_ast], _, ret = compile_arguments_set(compiler, [kwargs_parms], ret)

    return ast.arguments(
        args=args_ast,
        defaults=[*posonly_defaults, *args_defaults],
        vararg=rest_ast,
        posonlyargs=posonly_ast,
        kwonlyargs=kwonly_ast,
        kw_defaults=kwonly_defaults,
        kwarg=kwargs_ast), ret

def compile_arguments_set(compiler, decls, ret, is_kwonly=False):
    args_ast = []
    args_defaults = []

    for ann, decl in decls:
        default = None

        # funcparserlib will check to make sure that the only times we
        # ever have a hy List here are due to a default value.
        if isinstance(decl, List):
            sym, default = decl
        else:
            sym = decl

        if ann is not None:
            ret += compiler.compile(ann)
            ann_ast = ret.force_expr
        else:
            ann_ast = None

        if default is not None:
            ret += compiler.compile(default)
            args_defaults.append(ret.force_expr)
        # Kwonly args without defaults are considered required
        elif not isinstance(decl, List) and is_kwonly:
            args_defaults.append(None)
        elif isinstance(decl, List):
            # Note that the only time any None should ever appear here
            # is in kwargs, since the order of those with defaults vs
            # those without isn't significant in the same way as
            # positional args.
            args_defaults.append(None)

        args_ast.append(asty.arg(
            sym, arg=mangle(compiler._nonconst(sym)), annotation=ann_ast))

    return args_ast, args_defaults, ret

_decoratables = (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)

@pattern_macro("with-decorator", [oneplus(FORM)])
def compile_decorate_expression(compiler, expr, name, args):
    decs, fn = args[:-1], compiler.compile(args[-1])
    if not fn.stmts or not isinstance(fn.stmts[-1], _decoratables):
        raise compiler._syntax_error(args[-1],
            "Decorated a non-function")
    decs, ret, _ = compiler._compile_collect(decs)
    fn.stmts[-1].decorator_list = decs + fn.stmts[-1].decorator_list
    return ret + fn

@pattern_macro("return", [maybe(FORM)])
def compile_return(compiler, expr, root, arg):
    ret = Result()
    if arg is None:
        return asty.Return(expr, value=None)
    ret += compiler.compile(arg)
    return ret + asty.Return(expr, value=ret.force_expr)

@pattern_macro("yield", [maybe(FORM)])
def compile_yield_expression(compiler, expr, root, arg):
    ret = Result()
    if arg is not None:
        ret += compiler.compile(arg)
    return ret + asty.Yield(expr, value=ret.force_expr)

@pattern_macro(["yield-from", "await"], [FORM])
def compile_yield_from_or_await_expression(compiler, expr, root, arg):
    ret = Result() + compiler.compile(arg)
    node = asty.YieldFrom if root == "yield-from" else asty.Await
    return ret + node(expr, value=ret.force_expr)

# ------------------------------------------------
# * `defclass`
# ------------------------------------------------

@pattern_macro("defclass", [
    SYM,
    maybe(brackets(many(FORM)) + maybe(STR) + many(FORM))])
def compile_class_expression(compiler, expr, root, name, rest):
    base_list, docstring, body = rest or ([[]], None, [])

    bases_expr, bases, keywords = (
        compiler._compile_collect(base_list[0], with_kwargs=True))

    bodyr = Result()

    if docstring is not None:
        bodyr += compiler.compile(docstring).expr_as_stmt()

    e = compiler._compile_branch(body)
    bodyr += e + e.expr_as_stmt()

    return bases + asty.ClassDef(
        expr,
        decorator_list=[],
        name=mangle(compiler._nonconst(name)),
        keywords=keywords,
        starargs=None,
        kwargs=None,
        bases=bases_expr,
        body=bodyr.stmts or [asty.Pass(expr)])

# ------------------------------------------------
# * `import` and `require`
# ------------------------------------------------

def importlike(*name_types):
    name = some(lambda x: isinstance(x, name_types) and "." not in x)
    return [many(
        SYM |
        brackets(SYM, sym(":as"), name) |
        brackets(SYM, brackets(many(
            name + maybe(sym(":as") + name)))))]

@pattern_macro("import", importlike(Symbol))
@pattern_macro("require", importlike(Symbol, String))
def compile_import_or_require(compiler, expr, root, entries):
    ret = Result()

    for entry in entries:
        assignments = "ALL"
        prefix = ""

        if isinstance(entry, Symbol):
            # e.g., (import foo)
            module, prefix = entry, entry
        elif isinstance(entry, List) and isinstance(entry[1], Symbol):
            # e.g., (import [foo :as bar])
            module, prefix = entry
        else:
            # e.g., (import [foo [bar baz :as MyBaz bing]])
            # or (import [foo [*]])
            module, kids = entry
            kids = kids[0]
            if (Symbol('*'), None) in kids:
                if len(kids) != 1:
                    star = kids[kids.index((Symbol('*'), None))][0]
                    raise compiler._syntax_error(star,
                        "* in an import name list must be on its own")
            else:
                assignments = [(k, v or k) for k, v in kids]

        ast_module = mangle(module)

        if root == "import":
            module = ast_module.lstrip(".")
            level = len(ast_module) - len(module)
            if assignments == "ALL" and prefix == "":
                node = asty.ImportFrom
                names = [asty.alias(entry, name="*", asname=None)]
            elif assignments == "ALL":
                node = asty.Import
                prefix = mangle(prefix)
                names = [asty.alias(
                    entry,
                    name=ast_module,
                    asname=prefix if prefix != module else None)]
            else:
                node = asty.ImportFrom
                names = [
                    asty.alias(
                        entry,
                        name=mangle(k),
                        asname=None if v == k else mangle(v))
                    for k, v in assignments]
            ret += node(
                expr, module=module or None, names=names, level=level)

        elif require(ast_module, compiler.module, assignments=assignments,
                     prefix=prefix):
            # Actually calling `require` is necessary for macro expansions
            # occurring during compilation.
            # The `require` we're creating in AST is the same as above, but used at
            # run-time (e.g. when modules are loaded via bytecode).
            ret += compiler.compile(Expression([
                Symbol('hy.macros.require'),
                String(ast_module),
                Symbol('None'),
                Keyword('assignments'),
                (String("ALL") if assignments == "ALL" else
                    [[String(k), String(v)] for k, v in assignments]),
                Keyword('prefix'),
                String(prefix)]).replace(expr))
            ret += ret.expr_as_stmt()

    return ret

# ------------------------------------------------
# * Miscellany
# ------------------------------------------------

@pattern_macro(",", [many(FORM)])
def compile_tuple(compiler, expr, root, args):
    elts, ret, _ = compiler._compile_collect(args)
    return ret + asty.Tuple(expr, elts=elts, ctx=ast.Load())

@pattern_macro("assert", [FORM, maybe(FORM)])
def compile_assert_expression(compiler, expr, root, test, msg):
    if msg is None or type(msg) is Symbol:
        ret = compiler.compile(test)
        return ret + asty.Assert(
            expr,
            test=ret.force_expr,
            msg=(None if msg is None else compiler.compile(msg).force_expr))

    # The `msg` part may involve statements, which we only
    # want to be executed if the assertion fails. Rewrite the
    # form to set `msg` to a variable.
    msg_var = compiler.get_anon_var()
    return compiler.compile(mkexpr(
        'if', mkexpr('and', '__debug__', mkexpr('not', [test])),
            mkexpr('do',
                mkexpr('setv', msg_var, [msg]),
                mkexpr('assert', 'False', msg_var))).replace(expr))
