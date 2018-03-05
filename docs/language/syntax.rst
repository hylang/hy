==============
Syntax
==============

identifiers
-----------

An identifier consists of a nonempty sequence of Unicode characters that are not whitespace nor any of the following: ``( ) [ ] { } ' "``. Hy first tries to parse each identifier into a numeric literal, then into a keyword if that fails, and finally into a symbol if that fails.

numeric literals
----------------

In addition to regular numbers, standard notation from Python 3 for non-base 10
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

Python's so-called triple-quoted strings (e.g., ``'''hello'''`` and
``"""hello"""``) aren't supported. However, in Hy, unlike Python, any string
literal can contain newlines. Furthermore, Hy supports an alternative form of
string literal called a "bracket string" similar to Lua's long brackets.
Bracket strings have customizable delimiters, like the here-documents of other
languages. A bracket string begins with ``#[FOO[`` and ends with ``]FOO]``,
where ``FOO`` is any string not containing ``[`` or ``]``, including the empty
string. For example::

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

Whether running under Python 2 or Python 3, Hy treats all string literals as
sequences of Unicode characters by default, and allows you to prefix a plain
string literal (but not a bracket string) with ``b`` to treat it as a sequence
of bytes. So when running under Python 3, Hy translates ``"foo"`` and
``b"foo"`` to the identical Python code, but when running under Python 2,
``"foo"`` is translated to ``u"foo"`` and ``b"foo"`` is translated to
``"foo"``.

.. _syntax-keywords:

keywords
--------

An identifier headed by a colon, such as ``:foo``, is a keyword. Keywords
evaluate to a string preceded by the Unicode non-character code point U+FDD0,
like ``"\ufdd0:foo"``, so ``:foo`` and ``":foo"`` aren't equal. However, if a
literal keyword appears in a function call, it's used to indicate a keyword
argument rather than passed in as a value. For example, ``(f :foo 3)`` calls
the function ``f`` with the keyword argument named ``foo`` set to ``3``. Hence,
trying to call a function on a literal keyword may fail: ``(f :foo)`` yields
the error ``Keyword argument :foo needs a value``. To avoid this, you can quote
the keyword, as in ``(f ':foo)``, or use it as the value of another keyword
argument, as in ``(f :arg :foo)``.

.. _mangling:

symbols
-------

Symbols are identifiers that are neither legal numeric literals nor legal
keywords. In most contexts, symbols are compiled to Python variable names. Some
example symbols are ``hello``, ``+++``, ``3fiddy``, ``$40``, ``just✈wrong``,
and ``🦑``.

Since the rules for Hy symbols are much more permissive than the rules for
Python identifiers, Hy uses a mangling algorithm to convert its own names to
Python-legal names. The rules are:

- Convert all hyphens (``-``) to underscores (``_``). Thus, ``foo-bar`` becomes
  ``foo_bar``.
- If the name ends with ``?``, remove it and prepend ``is``. Thus, ``tasty?``
  becomes ``is_tasty``.
- If the name still isn't Python-legal, make the following changes. A name
  could be Python-illegal because it contains a character that's never legal in
  a Python name, it contains a character that's illegal in that position, or
  it's equal to a Python reserved word.

  - Prepend ``hyx_`` to the name.
  - Replace each illegal character with ``ΔfooΔ`` (or on Python 2, ``XfooX``),
    where ``foo`` is the the Unicode character name in lowercase, with spaces
    replaced by underscores and hyphens replaced by ``H``. Replace ``Δ`` itself
    (or on Python 2, ``X``) the same way. If the character doesn't have a name,
    use ``U`` followed by its code point in lowercase hexadecimal.

  Thus, ``green☘`` becomes ``hyx_greenΔshamrockΔ`` and ``if`` becomes
  ``hyx_if``.

- Finally, any added ``hyx_`` or ``is_`` is added after any leading
  underscores, because leading underscores have special significance to Python.
  Thus, ``_tasty?`` becomes ``_is_tasty`` instead of ``is__tasty``.

Mangling isn't something you should have to think about often, but you may see
mangled names in error messages, the output of ``hy2py``, etc. A catch to be
aware of is that mangling, as well as the inverse "unmangling" operation
offered by the ``unmangle`` function, isn't one-to-one. Two different symbols
can mangle to the same string and hence compile to the same Python variable.
The chief practical consequence of this is that ``-`` and ``_`` are
interchangeable in all symbol names, so you shouldn't assign to the
one-character name ``_`` , or else you'll interfere with certain uses of
subtraction.

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
