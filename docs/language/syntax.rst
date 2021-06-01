.. _syntax:

==============
Syntax
==============

identifiers
-----------

An identifier consists of a nonempty sequence of Unicode characters that are not whitespace nor any of the following: ``( ) [ ] { } ' "``. Hy first tries to parse each identifier into a numeric literal, then into a keyword if that fails, and finally into a symbol if that fails.

numeric literals
----------------

In addition to regular numbers, standard notation from Python for non-base 10
integers is used. ``0x`` for Hex, ``0o`` for Octal, ``0b`` for Binary.

.. code-block:: clj

    (print 0x80 0b11101 0o102 30)

Underscores and commas can appear anywhere in a numeric literal except the very
beginning. They have no effect on the value of the literal, but they're useful
for visually separating digits.

.. code-block:: clj

    (print 10,000,000,000 10_000_000_000)

Unlike Python, Hy provides literal forms for NaN and infinity: ``NaN``,
``Inf``, and ``-Inf``.

string literals
---------------

Hy allows double-quoted strings (e.g., ``"hello"``), but not single-quoted
strings like Python. The single-quote character ``'`` is reserved for
preventing the evaluation of a form (e.g., ``'(+ 1 1)``), as in most Lisps.

.. _syntax-bracket-strings:

Python's so-called triple-quoted strings (e.g., ``'''hello'''`` and
``"""hello"""``) aren't supported. However, in Hy, unlike Python, any string
literal can contain newlines. Furthermore, Hy supports an alternative form of
string literal called a "bracket string" similar to Lua's long brackets.
Bracket strings have customizable delimiters, like the here-documents of other
languages. A bracket string begins with ``#[FOO[`` and ends with ``]FOO]``,
where ``FOO`` is any string not containing ``[`` or ``]``, including the empty
string. (If ``FOO`` is exactly ``f`` or begins with ``f-``, the bracket string
is interpreted as a :ref:`format string <syntax-fstrings>`.) For example::

   => (print #[["That's very kind of yuo [sic]" Tom wrote back.]])
   "That's very kind of yuo [sic]" Tom wrote back.
   => (print #[==[1 + 1 = 2]==])
   1 + 1 = 2

A bracket string can contain newlines, but if it begins with one, the newline
is removed, so you can begin the content of a bracket string on the line
following the opening delimiter with no effect on the content. Any leading
newlines past the first are preserved.

Plain string literals support :ref:`a variety of backslash escapes
<py:strings>`. To create a "raw string" that interprets all backslashes
literally, prefix the string with ``r``, as in ``r"slash\not"``. Bracket
strings are always raw strings and don't allow the ``r`` prefix.

Like Python, Hy treats all string literals as sequences of Unicode characters
by default. You may prefix a plain string literal (but not a bracket string)
with ``b`` to treat it as a sequence of bytes.

Unlike Python, Hy only recognizes string prefixes (``r``, etc.) in lowercase.

.. _syntax-fstrings:

format strings
--------------

A format string (or "f-string", or "formatted string literal") is a string
literal with embedded code, possibly accompanied by formatting commands. Hy
f-strings work much like :ref:`Python f-strings <py:f-strings>` except that the
embedded code is in Hy rather than Python.

::

    => (print f"The sum is {(+ 1 1)}.")
    The sum is 2.

Since ``!`` and ``:`` are identifier characters in Hy, Hy decides where the
code in a replacement field ends, and any conversion or format specifier
begins, by parsing exactly one form. You can use ``do`` to combine several
forms into one, as usual. Whitespace may be necessary to terminate the form::

    => (setv foo "a")
    => (print f"{foo:x<5}")
    …
    NameError: name 'hyx_fooXcolonXxXlessHthan_signX5' is not defined
    => (print f"{foo :x<5}")
    axxxx

Unlike Python, whitespace is allowed between a conversion and a format
specifier.

Also unlike Python, comments and backslashes are allowed in replacement fields.
Hy's lexer will still process the whole format string normally, like any other
string, before any replacement fields are considered, so you may need to
backslash your backslashes, and you can't comment out a closing brace or the
string delimiter.

Hy's f-strings are compatible with Python's "=" debugging syntax, subject to
the above limitations on delimiting identifiers. For example::

    => (setv foo "bar")
    => (print f"{foo = }")
    foo = 'bar'
    => (print f"{foo = !s :_^7}")
    foo = __bar__

.. _syntax-keywords:

keywords
--------

An identifier headed by a colon, such as ``:foo``, is a keyword. If a
literal keyword appears in a function call, it's used to indicate a keyword
argument rather than passed in as a value. For example, ``(f :foo 3)`` calls
the function ``f`` with the keyword argument named ``foo`` set to ``3``. Hence,
trying to call a function on a literal keyword may fail: ``(f :foo)`` yields
the error ``Keyword argument :foo needs a value``. To avoid this, you can quote
the keyword, as in ``(f ':foo)``, or use it as the value of another keyword
argument, as in ``(f :arg :foo)``. It is important to note that a keyword argument
cannot be a Python reserved word. This will raise a ``SyntaxError`` similar to Python.
See :ref:`defn <reserved_param_names>` for examples.

Keywords can be called like functions as shorthand for ``get``. ``(:foo obj)``
is equivalent to ``(get obj (hy.mangle "foo"))``. An optional ``default`` argument
is also allowed: ``(:foo obj 2)`` or ``(:foo obj :default 2)`` returns ``2`` if
``(get obj "foo")`` raises a ``KeyError``.

.. _mangling:

symbols
-------

Symbols are identifiers that are neither legal numeric literals nor legal
keywords. In most contexts, symbols are compiled to Python variable names. Some
example symbols are ``hello``, ``+++``, ``3fiddy``, ``$40``, ``just✈wrong``,
and ``🦑``.

Since the rules for Hy symbols are much more permissive than the rules for
Python identifiers, Hy uses a mangling algorithm to convert its own names to
Python-legal names. The steps are as follows:

#. Remove any leading underscores (``_``). Leading underscores have special
   significance in Python, so we will mangle the remainder of the name and
   then add the leading underscores back in to the final mangled name.

#. Convert hyphens (``-``) to underscores (``_``). Thus, ``foo-bar`` becomes
   ``foo_bar``. If the name at this step starts with a hyphen, this *first* hyphen is not
   converted, so that we don't introduce a new leading underscore into the name. Thus
   ``--has-dashes?`` becomes ``-_has_dashes?`` at this step.

#. If the name ends with ``?``, remove it and prepend ``is_``. Thus, ``tasty?``
   becomes ``is_tasty`` and ``-_has_dashes?`` becomes ``is_-_has_dashes``.

#. If the name still isn't Python-legal, make the following changes. A name
   could be Python-illegal because it contains a character that's never legal
   in a Python name, it contains a character that's illegal in that position,
   or it's equal to a Python reserved word.

   - Prepend ``hyx_`` to the name.
   - Replace each illegal character with ``XfooX``, where ``foo`` is the Unicode
     character name in lowercase, with spaces replaced by underscores and
     hyphens replaced by ``H``. Replace leading hyphens and ``X`` itself the
     same way. If the character doesn't have a name, use ``U`` followed by its
     code point in lowercase hexadecimal.

   Thus, ``green☘`` becomes ``hyx_greenXshamrockX``, ``if`` becomes
   ``hyx_if``, and ``is_-_has_dashes`` becomes ``hyx_is_XhyphenHminusX_has_dashes``.

#. Finally, any leading underscores removed in the first step are added back
   to the mangled name.
   Thus, ``(hy.mangle '_tasty?)`` is ``"_is_tasty"`` instead of ``"is__tasty"``
   and ``(hy.mangle '__-_has-dashes?)`` is ``"__hyx_is_XhyphenHminusX_has_dashes"``.

Mangling isn't something you should have to think about often, but you may see
mangled names in error messages, the output of ``hy2py``, etc. A catch to be
aware of is that mangling, as well as the inverse "unmangling" operation
offered by the ``unmangle`` function, isn't one-to-one. Two different symbols
can mangle to the same string and hence compile to the same Python variable.
The chief practical consequence of this is that (non-initial) ``-`` and ``_`` are
interchangeable in all symbol names, so you shouldn't use, e.g., both
``foo-bar`` and ``foo_bar`` as separate variables.

discard prefix
--------------

Hy supports the Extensible Data Notation discard prefix, like Clojure.
Any form prefixed with ``#_`` is discarded instead of compiled.
This completely removes the form so it doesn't evaluate to anything,
not even None.
It's often more useful than linewise comments for commenting out a
form, because it respects code structure even when part of another
form is on the same line. For example:

.. code-block:: clj

   => (print "Hy" "cruel" "World!")
   Hy cruel World!
   => (print "Hy" #_"cruel" "World!")
   Hy World!
   => (+ 1 1 (print "Math is hard!"))
   Math is hard!
   Traceback (most recent call last):
      ...
   TypeError: unsupported operand type(s) for +: 'int' and 'NoneType'
   => (+ 1 1 #_(print "Math is hard!"))
   2
