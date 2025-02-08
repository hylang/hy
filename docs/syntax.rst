.. _syntax:

==============
Syntax
==============

This chapter describes how Hy source code is understood at the level of text,
as well as the abstract syntax objects that the reader (a.k.a. the parser)
turns text into, as when invoked with :hy:func:`hy.read`. The basic units of
syntax at the textual level are called **forms**, and the basic objects
representing forms are called **models**.

Following Python, Hy is in general case-sensitive. For example, ``foo`` and
``FOO`` are different symbols, and the Python-level variables they refer to are
also different.

.. contents:: Contents
   :local:

.. _models:

An introduction to models
-------------------------

Reading a Hy program produces a nested structure of model objects. Models can
be very similar to the kind of value they represent (such as :class:`Integer
<hy.models.Integer>`, which is a subclass of :class:`int`) or they can be
somewhat different (such as :class:`Set <hy.models.Set>`, which is ordered,
unlike actual :class:`set`\s). All models inherit from :class:`Object
<hy.models.Object>`, which stores textual position information, so tracebacks
can point to the right place in the code. The compiler takes whatever models
are left over after parsing and macro-expansion and translates them into Python
:mod:`ast` nodes (e.g., :class:`Integer <hy.models.Integer>` becomes
:class:`ast.Constant`), which can then be evaluated or rendered as Python code.
Macros (that is, regular macros, as opposed to reader macros) operate on the
model level, taking some models as arguments and returning more models for
compilation or further macro-expansion; they're free to do quite different
things with a given model than the compiler does, if it pleases them to, like
using an :class:`Integer <hy.models.Integer>` to construct a :class:`Symbol
<hy.models.Symbol>`.

In general, a model doesn't count as equal to the value it represents. For
example, ``(= (hy.models.String "foo") "foo")`` returns :data:`False`. But you
can promote a value to its corresponding model with :hy:func:`hy.as-model`, or
you can demote a model with the usual Python constructors like :py:class:`str`
or :py:class:`int`, or you can evaluate a model as Hy code with
:hy:func:`hy.eval`.

Models can be created with the constructors, with the :hy:func:`quote` or
:hy:func:`quasiquote` macros, or with :hy:func:`hy.as-model`. Explicit creation
is often not necessary, because the compiler will automatically promote (via
:hy:func:`hy.as-model`) any object it's trying to evaluate.

Note that when you want plain old data structures and don't intend to produce
runnable Hy source code, you'll usually be better off using Python's basic data
structures (:class:`tuple`, :class:`list`, :class:`dict`, etc.) than models.
Yes, "homoiconicity" is a fun word, but a Hy :class:`List <hy.models.List>`
won't provide any advantage over a Python :class:`list` when you're managing a
list of email addresses or something.

The default representation of models (via :hy:func:`hy.repr`) uses quoting for
readability, so ``(hy.models.Integer 5)`` is represented as ``'5``. Python
representations (via :func:`repr`) use the constructors, and by default are
pretty-printed; you can disable this globally by setting ``hy.models.PRETTY``
to ``False``, or temporarily with the context manager ``hy.models.pretty``.

.. _hyobject:

.. autoclass:: hy.models.Object
.. autoclass:: hy.models.Lazy

Non-form syntactic elements
---------------------------

.. _shebang:

Shebang
~~~~~~~

If a Hy program begins with ``#!``, Hy assumes the first line is a `shebang
line <https://en.wikipedia.org/wiki/Shebang_(Unix)>`_ and ignores it. It's up
to your OS to do something more interesting with it.

Shebangs aren't real Hy syntax, so :hy:func:`hy.read-many` only allows them
if its option ``skip_shebang`` is enabled.

Whitespace
~~~~~~~~~~

Hy has lax whitespace rules less similar to Python's than to those of most
other programming languages. Whitespace can separate forms (e.g., ``a b`` is
two forms whereas ``ab`` is one) and it can occur inside some forms (like
string literals), but it's otherwise ignored by the reader, producing no
models.

The reader only grants this special treatment to the ASCII whitespace
characters, namely U+0009 (horizontal tab), U+000A (line feed), U+000B
(vertical tab), U+000C (form feed), U+000D (carriage return), and U+0020
(space). Non-ASCII whitespace characters, such as U+2009 (THIN SPACE), are
treated as any other character. So yes, you can have exotic whitespace
characters in variable names, although this is only especially useful for
obfuscated code contests.

Comments
~~~~~~~~

Comments begin with a semicolon (``;``) and continue through the end of the
line.

There are no multi-line comments in the style of C's ``/* … */``, but you can
use the :ref:`discard prefix <discard-prefix>` or :ref:`string literals
<string-literals>` for similar purposes.

.. _discard-prefix:

Discard prefix
~~~~~~~~~~~~~~

Like Clojure, Hy supports the Extensible Data Notation discard prefix ``#_``,
which is kind of like a structure-aware comment. When the reader encounters
``#_``, it reads and then discards the following form. Thus ``#_`` is like
``;`` except that reader macros still get executed, and normal parsing resumes
after the next form ends rather than at the start of the next line: ``[dilly #_
and krunk]`` is equivalent to ``[dilly krunk]``, whereas ``[dilly ; and
krunk]`` is equivalent to just ``[dilly``. Comments indicated by ``;`` can be
nested within forms discarded by ``#_``, but ``#_`` has no special meaning
within a comment indicated by ``;``.

Identifiers
-----------

Identifiers are a broad class of syntax in Hy, comprising not only variable
names, but any nonempty sequence of characters that aren't ASCII whitespace nor
one of the following: ``()[]{};"'`~``. The reader will attempt to read an
identifier as each of the following types, in the given order:

1. a :ref:`numeric literal <numeric-literals>`
2. a :ref:`keyword <keywords>`
3. a :ref:`dotted identifier <dotted-identifiers>`
4. a :ref:`symbol <symbols>`

.. _numeric-literals:

Numeric literals
~~~~~~~~~~~~~~~~

All of :ref:`Python's syntax for numeric literals <py:numbers>` is supported in
Hy, resulting in an :class:`Integer <hy.models.Integer>`, :class:`Float
<hy.models.Float>`, or :class:`Complex <hy.models.Complex>`. Hy also provides a
few extensions:

- Commas (``,``) can be used like underscores (``_``) to separate digits
  without changing the result. Thus, ``10_000_000_000`` may also be written
  ``10,000,000,000``. Hy is also more permissive about the placement of
  separators than Python: several may be in a row, and they may be after all
  digits, after ``.``, ``e``, or ``j``, or even inside a radix prefix. Separators
  before the first digit are still forbidden because e.g. ``_1`` is a legal
  Python variable name, so it's a symbol in Hy rather than an integer.
- Integers can begin with leading zeroes, even without a radix prefix like
  ``0x``. Leading zeroes don't automatically cause the literal to be
  interpreted in octal like they do in C. For octal, use the prefix ``0o``, as
  in Python.
- ``NaN``, ``Inf``, and ``-Inf`` are understood as literals. Each produces a
  :class:`Float <hy.models.Float>`. These are case-sensitive, unlike other uses
  of letters in numeric literals (``1E2``, ``0XFF``, ``5J``, etc.).
- Hy allows complex literals as understood by the constructor for
  :class:`complex`, such as ``5+4j``. (This is also legal Python, but Hy reads
  it as a single :class:`Complex <hy.models.Complex>`, and doesn't otherwise
  support infix addition or subtraction, whereas Python parses it as an
  addition expression.)

.. autoclass:: hy.models.Integer
.. autoclass:: hy.models.Float
.. autoclass:: hy.models.Complex

.. _keywords:

Keywords
~~~~~~~~

An identifier starting with a colon (``:``), such as ``:foo``, is a
:class:`Keyword <hy.models.Keyword>`.

Literal keywords are most often used for their special treatment in
:ref:`expressions <expressions>` that aren't macro calls: they set
:std:term:`keyword arguments <keyword argument>`, rather than being passed in
as values. For example, ``(f :foo 3)`` calls the function ``f`` with the
parameter ``foo`` set to ``3``. The keyword is also :ref:`mangled <mangling>`
at compile-time. To prevent a literal keyword from being treated specially in
an expression, you can :hy:func:`quote` the keyword, or you can use it as the
value for another keyword argument, as in ``(f :foo :bar)``.

Otherwise, keywords are simple model objects that evaluate to themselves. Users
of other Lisps should note that it's often a better idea to use a string than a
keyword, because the rest of Python uses strings for cases in which other Lisps
would use keywords. In particular, strings are typically more appropriate than
keywords as the keys of a dictionary. Notice that ``(dict :a 1 :b 2)`` is
equivalent to ``{"a" 1 "b" 2}``, which is different from ``{:a 1 :b 2}`` (see
:ref:`dict-literals`).

The empty keyword ``:`` is syntactically legal, but you can't compile a
function call with an empty keyword argument because of Python limitations.
Thus ``(foo : 3)`` must be rewritten to use runtime unpacking, as in ``(foo #**
{"" 3})``.

.. autoclass:: hy.models.Keyword
   :members:  __bool__, __lt__, __call__

.. _dotted-identifiers:

Dotted identifiers
~~~~~~~~~~~~~~~~~~

Dotted identifiers are named for their use of the dot character ``.``, also
known as a period or full stop. They don't have their own model type because
they're actually syntactic sugar for :ref:`expressions <expressions>`. Syntax
like ``foo.bar.baz`` is equivalent to ``(. foo bar baz)``. The general rule is
that a dotted identifier looks like two or more :ref:`symbols <symbols>`
(themselves not containing any dots) separated by single dots. The result is an
expression with the symbol ``.`` as its first element and the constituent
symbols as the remaining elements.

A dotted identifier may also begin with one or more dots, as in ``.foo.bar`` or
``..foo.bar``, in which case the resulting expression has the appropriate head
(``.`` or ``..`` or whatever) and the symbol ``None`` as the following element.
Thus, ``..foo.bar`` is equivalent to ``(.. None foo bar)``. In the leading-dot
case, you may also use only one constitutent symbol. Thus, ``.foo`` is a legal
dotted identifier, and equivalent to ``(. None foo)``.

See :ref:`the dot macro <dot>` for what these expressions typically compile to.
See also the special behavior for :ref:`expressions <expressions>` that begin
with a dotted identifier that itself begins with a dot. Note that Hy provides
definitions of ``.`` and ``...`` by default, but not ``..``, ``....``,
``.....``, etc., so ``..foo.bar`` won't do anything useful by default outside
of macros that treat it specially, like :hy:func:`import`.

.. _symbols:

Symbols
~~~~~~~

Symbols are the catch-all category of identifiers. In most contexts, symbols
are compiled to Python variable names, after being :ref:`mangled <mangling>`.
You can create symbol objects with the :hy:func:`quote` operator or by calling
the :class:`Symbol <hy.models.Symbol>` constructor (thus, :class:`Symbol
<hy.models.Symbol>` plays a role similar to the ``intern`` function in other
Lisps). Some example symbols are ``hello``, ``+++``, ``3fiddy``, ``$40``,
``just✈wrong``, and ``🦑``.

Dots are only allowed in a symbol if every character in the symbol is a dot.
Thus, ``a..b`` and ``a.`` are neither dotted identifiers nor symbols; they're
syntax errors.

As a special case, the symbol ``...`` compiles to the :data:`Ellipsis` object,
as in Python.

.. autoclass:: hy.models.Symbol

.. _mangling:

Mangling
~~~~~~~~

Since the rules for Hy symbols and keywords are much more permissive than the rules for
Python identifiers, Hy uses a mangling algorithm to convert its own names to
Python-legal names. The steps are as follows:

#. Remove any leading underscores. Underscores are typically the ASCII
   underscore ``_``, but they may also be any Unicode character that normalizes
   (according to NFKC) to ``_``. Leading underscores have special significance
   in Python, and Python normalizes all Unicode before this test, so we'll
   process the remainder of the name and then add the leading underscores back
   onto the final mangled name.

#. Convert ASCII hyphens (``-``) to underscores (``_``). Thus, ``foo-bar``
   becomes ``foo_bar``. If the name at this step starts with a hyphen, this
   *first* hyphen is not converted, so that we don't introduce a new leading
   underscore into the name. Thus ``--has-dashes?`` becomes ``-_has_dashes?``
   at this step.

#. If the name still isn't Python-legal, make the following changes. A name
   could be Python-illegal because it contains a character that's never legal
   in a Python name or it contains a character that's illegal in that position.

   - Prepend ``hyx_`` to the name.
   - Replace each illegal character with ``XfooX``, where ``foo`` is the Unicode
     character name in lowercase, with spaces replaced by underscores and
     hyphens replaced by ``H``. Replace leading hyphens and ``X`` itself the
     same way. If the character doesn't have a name, use ``U`` followed by its
     code point in lowercase hexadecimal.

   Thus, ``green☘`` becomes ``hyx_greenXshamrockX`` and
   ``-_has_dashes`` becomes ``hyx_XhyphenHminusX_has_dashes``.

#. Take any leading underscores removed in the first step, transliterate them
   to ASCII, and add them back to the mangled name. Thus, ``__green☘`` becomes
   ``__hyx_greenXshamrockX``.

#. Finally, normalize any leftover non-ASCII characters. The result may still
   not be ASCII (e.g., ``α`` is already Python-legal and normalized, so it
   passes through the whole mangling procedure unchanged), but it is now
   guaranteed that any names are equal as strings if and only if they refer to
   the same Python identifier.

You can invoke the mangler yourself with the function :hy:func:`hy.mangle`, and try to undo this (perhaps not quite successfully) with :hy:func:`hy.unmangle`.

Mangling isn't something you should have to think about often, but you may see
mangled names in error messages, the output of ``hy2py``, etc. A catch to be
aware of is that mangling, as well as the inverse "unmangling" operation
offered by :hy:func:`hy.unmangle`, isn't one-to-one. Two different symbols,
like ``foo-bar`` and ``foo_bar``, can mangle to the same string and hence
compile to the same Python variable.

.. _string-literals:

.. _hystring:

String literals
---------------

Hy allows double-quoted strings (e.g., ``"hello"``), but not single-quoted
strings like Python. The single-quote character ``'`` is reserved for
preventing the evaluation of a form, (e.g., ``'(+ 1 1)``), as in most Lisps
(see :ref:`more-sugar`). Python's so-called triple-quoted strings (e.g.,
``'''hello'''`` and ``"""hello"""``) aren't supported, either. However, in Hy, unlike
Python, any string literal can contain newlines; furthermore, Hy has
:ref:`bracket strings <bracket-strings>`. For consistency with Python's
triple-quoted strings, all literal newlines in literal strings are read as in
``"\n"`` (U+000A, line feed) regardless of the newline style in the actual
code.

String literals support :ref:`a variety of backslash escapes <py:strings>`.
Unrecognized escape sequences are a syntax error. To create a "raw string" that
interprets all backslashes literally, prefix the string with ``r``, as in
``r"slash\not"``.

By default, all string literals are regarded as sequences of Unicode characters.
The result is the model type :class:`String <hy.models.String>`.
You may prefix a string literal with ``b`` to treat it as a sequence of bytes,
producing :class:`Bytes <hy.models.Bytes>` instead.

Unlike Python, Hy only recognizes string prefixes (``r``, ``b``, and ``f``) in
lowercase, and doesn't allow the no-op prefix ``u``.

:ref:`F-strings <syntax-fstrings>` are a string-like compound construct
documented further below.

.. autoclass:: hy.models.String
.. autoclass:: hy.models.Bytes

.. _bracket-strings:

Bracket strings
~~~~~~~~~~~~~~~

Hy supports an alternative form of string literal called a "bracket string"
similar to Lua's long brackets. Bracket strings have customizable delimiters,
like the here-documents of other languages. A bracket string begins with
``#[FOO[`` and ends with ``]FOO]``, where ``FOO`` is any string not containing
``[`` or ``]``, including the empty string. (If ``FOO`` is exactly ``f`` or
begins with ``f-``, the bracket string is interpreted as an :ref:`f-string
<syntax-fstrings>`.) For example::

   (print #[["That's very kind of yuo [sic]" Tom wrote back.]])
     ; "That's very kind of yuo [sic]" Tom wrote back.
   (print #[==[1 + 1 = 2]==])
     ; 1 + 1 = 2

Bracket strings are always raw Unicode strings, and don't allow the ``r`` or
``b`` prefixes.

A bracket string can contain newlines, but if it begins with one, the newline
is removed, so you can begin the content of a bracket string on the line
following the opening delimiter with no effect on the content. Any leading
newlines past the first are preserved.

.. _hysequence:

Sequential forms
----------------

Sequential forms (:class:`Sequence <hy.models.Sequence>`) are nested forms
comprising any number of other forms, in a defined order.

.. autoclass:: hy.models.Sequence

.. _expressions:

Expressions
~~~~~~~~~~~

Expressions (:class:`Expression <hy.models.Expression>`) are denoted by
parentheses: ``( … )``. The compiler evaluates expressions by checking the
first element, called the head.

- If the head is a symbol, and the symbol is the name of a currently defined
  macro, the macro is called.

  - Exception: if the symbol is also the name of a function in
    :hy:mod:`hy.pyops`, and one of the arguments is an
    :hy:func:`unpack-iterable` form, the ``pyops`` function is called instead
    of the macro. This makes reasonable-looking expressions work that would
    otherwise fail. For example, ``(+ #* summands)`` is understood as
    ``(hy.pyops.+ #* summands)``, because Python provides no way to sum a list
    of unknown length with a real addition expression.

- If the head is itself an expression of the form ``(. None …)`` (typically
  produced with a :ref:`dotted identifier <dotted-identifiers>` like ``.add``),
  it's used to construct a method call with the element after ``None`` as the
  object: thus, ``(.add my-set 5)`` is equivalent to ``((. my-set add) 5)``,
  which becomes ``my_set.add(5)`` in Python.

  .. _hy.R:

  - Exception: expressions like ``((. hy R module-name macro-name) …)``, or equivalently ``(hy.R.module-name.macro-name …)``, get special treatment. They :hy:func:`require` the module ``module-name`` and call its macro ``macro-name``, so ``(hy.R.foo.bar 1)`` is equivalent to ``(require foo) (foo.bar 1)``, but without bringing ``foo`` or ``foo.bar`` into scope. Thus ``hy.R`` is convenient syntactic sugar for macros you'll only call once in a file, or for macros that you want to appear in the expansion of other macros without having to call :hy:func:`require` in the expansion. As with :hy:class:`hy.I`, dots in the module name must be replaced with slashes.

- Otherwise, the expression is compiled into a Python-level call, with the
  head being the calling object. (So, you can call a function that has
  the same name as a macro with an expression like ``((do setv) …)``.) The
  remaining forms are understood as arguments. Use :hy:func:`unpack-iterable`
  or :hy:func:`unpack-mapping` to break up data structures into individual
  arguments at runtime.

The empty expression ``()`` is legal at the reader level, but has no inherent
meaning. Trying to compile it is an error. For the empty tuple, use ``#()``.

.. autoclass:: hy.models.Expression

.. _hylist:

List, tuple, and set literals
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- Literal :class:`list`\s (:class:`List <hy.models.List>`) are denoted by ``[ …
  ]``.
- Literal :class:`tuple`\s (:class:`Tuple <hy.models.Tuple>`) are denoted by
  ``#( … )``.
- Literal :class:`set`\s (:class:`Set <hy.models.Set>`) are denoted by ``#{ …
  }``.

.. autoclass:: hy.models.List
.. autoclass:: hy.models.Tuple
.. autoclass:: hy.models.Set

.. _dict-literals:

Dictionary literals
~~~~~~~~~~~~~~~~~~~

Literal dictionaries (:class:`dict`, :class:`Dict <hy.models.Dict>`) are
denoted by ``{ … }``. Even-numbered child forms (counting the first as 0)
become the keys whereas odd-numbered child forms become the values. For
example, ``{"a" 1 "b" 2}`` produces a dictionary mapping ``"a"`` to ``1`` and
``"b"`` to ``2``. Trying to compile a :class:`Dict <hy.models.Dict>` with an
odd number of child models is an error.

As in Python, calling :class:`dict` with keyword arguments may be more
convenient than using a literal dictionary when all the keys are
strings. Compare the following alternatives::

    (dict :a 1 :b 2 :c 3 :d 4 :e 5)
    {"a" 1  "b" 2  "c" 3  "d" 4  "e" 5}

.. autoclass:: hy.models.Dict

.. _syntax-fstrings:

Format strings
~~~~~~~~~~~~~~

A format string (or "f-string", or "formatted string literal") is a string
literal with embedded code, possibly accompanied by formatting commands. The
result is an :class:`FString <hy.models.FString>`, Hy f-strings work much like
:ref:`Python f-strings <py:f-strings>` except that the embedded code is in Hy
rather than Python. ::

    (print f"The sum is {(+ 1 1)}.")  ; => The sum is 2.

Since ``=``, ``!``, and ``:`` are identifier characters in Hy, Hy decides where
the code in a replacement field ends (and any debugging ``=``, conversion
specifier, or format specifier begins) by parsing exactly one form. You can use
``do`` to combine several forms into one, as usual. Whitespace may be necessary
to terminate the form::

    (setv foo "a")
    (print f"{foo:x<5}")   ; => NameError: name 'hyx_fooXcolonXxXlessHthan_signX5' is not defined
    (print f"{foo :x<5}")  ; => axxxx

Unlike Python, whitespace is allowed between a conversion and a format
specifier.

Also unlike Python, comments and backslashes are allowed in replacement fields.
The same reader is used for the form to be evaluated as for elsewhere in the
language. Thus e.g. ``f"{"a"}"`` is legal, and equivalent to ``"a"``.

.. autoclass:: hy.models.FString
.. autoclass:: hy.models.FComponent

.. _more-sugar:

Additional sugar
----------------

Syntactic sugar is available to construct two-item :ref:`expressions
<expressions>` with certain heads. When the sugary characters are encountered
by the reader, a new expression is created with the corresponding macro name as
the first element and the next parsed form as the second. No parentheses are
required. Thus, since ``'`` is short for ``quote``, ``'FORM`` is read as
``(quote FORM)``. Whitespace is allowed, as in ``' FORM``. This is all resolved
at the reader level, so the model that gets produced is the same whether you
take your code with sugar or without.

========================== ================
Macro                      Syntax
========================== ================
:hy:func:`quote`           ``'FORM``
:hy:func:`quasiquote`      ```FORM``
:hy:func:`unquote`         ``~FORM``
:hy:func:`unquote-splice`  ``~@FORM``
:hy:func:`unpack-iterable` ``#* FORM``
:hy:func:`unpack-mapping`  ``#** FORM``
========================== ================

Reader macros
-------------

A hash (``#``) followed by a :ref:`symbol <symbols>` invokes the :ref:`reader
macro <reader-macros>` named by the symbol. (Trying to call an undefined reader
macro is a syntax error.) Parsing of the remaining source code is under control
of the reader macro until it returns.
