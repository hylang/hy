# Copyright 2021 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.

import re
import keyword
import unicodedata

MANGLE_DELIM = 'X'

def mangle(s):
    """Stringify the argument and convert it to a valid Python identifier
    according to :ref:`Hy's mangling rules <mangling>`.

    Examples:
      ::

         => (hy.mangle 'foo-bar)
         "foo_bar"

         => (hy.mangle 'foo-bar?)
         "is_foo_bar"

         => (hy.mangle '*)
         "hyx_XasteriskX"

         => (hy.mangle '_foo/a?)
         "_hyx_is_fooXsolidusXa"

         => (hy.mangle '-->)
         "hyx_XhyphenHminusX_XgreaterHthan_signX"

         => (hy.mangle '<--)
         "hyx_XlessHthan_signX__"
    """
    def unicode_char_to_hex(uchr):
        # Covert a unicode char to hex string, without prefix
        if len(uchr) == 1 and ord(uchr) < 128:
            return format(ord(uchr), 'x')
        return (uchr.encode('unicode-escape').decode('utf-8')
            .lstrip('\\U').lstrip('\\u').lstrip('\\x').lstrip('0'))

    assert s
    s = str(s)

    if "." in s:
        return ".".join(mangle(x) if x else "" for x in s.split("."))

    # Step 1: Remove and save leading underscores
    s2 = s.lstrip('_')
    leading_underscores = '_' * (len(s) - len(s2))
    s = s2

    # Step 2: Convert hyphens without introducing a new leading underscore
    s = s[0] + s[1:].replace("-", "_") if s else s

    # Step 3: Convert trailing `?` to leading `is_`
    if s.endswith("?"):
        s = 'is_' + s[:-1]

    # Step 4: Convert invalid characters or reserved words
    if not isidentifier(leading_underscores + s):
        # Replace illegal characters with their Unicode character
        # names, or hexadecimal if they don't have one.
        s = 'hyx_' + ''.join(
            c
               if c != MANGLE_DELIM and isidentifier('S' + c)
                 # We prepend the "S" because some characters aren't
                 # allowed at the start of an identifier.
               else '{0}{1}{0}'.format(MANGLE_DELIM,
                   unicodedata.name(c, '').lower().replace('-', 'H').replace(' ', '_')
                   or 'U{}'.format(unicode_char_to_hex(c)))
            for c in s)

    # Step 5: Add back leading underscores
    s = leading_underscores + s

    assert isidentifier(s)
    return s


def unmangle(s):
    """Stringify the argument and try to convert it to a pretty unmangled
    form. This may not round-trip, because different Hy symbol names can
    mangle to the same Python identifier. See :ref:`Hy's mangling rules <mangling>`.

    Examples:
      ::

         => (hy.unmangle 'foo_bar)
         "foo-bar"

         => (hy.unmangle 'is_foo_bar)
         "foo-bar?"

         => (hy.unmangle 'hyx_XasteriskX)
         "*"

         => (hy.unmangle '_hyx_is_fooXsolidusXa)
         "_foo/a?"

         => (hy.unmangle 'hyx_XhyphenHminusX_XgreaterHthan_signX)
         "-->"

         => (hy.unmangle 'hyx_XlessHthan_signX__)
         "<--"

         => (hy.unmangle '__dunder_name__)
         "__dunder-name__"
    """

    s = str(s)

    prefix = ""
    suffix = ""
    m = re.fullmatch(r'(_+)(.*?)(_*)', s, re.DOTALL)
    if m:
        prefix, s, suffix = m.groups()

    if s.startswith('hyx_'):
        s = re.sub('{0}(U)?([_a-z0-9H]+?){0}'.format(MANGLE_DELIM),
            lambda mo:
               chr(int(mo.group(2), base=16))
               if mo.group(1)
               else unicodedata.lookup(
                   mo.group(2).replace('_', ' ').replace('H', '-').upper()),
            s[len('hyx_'):])
    if s.startswith('is_'):
        s = s[len("is_"):] + "?"
    s = s.replace('_', '-')

    return prefix + s + suffix



def isidentifier(x):
    if x in ('True', 'False', 'None'):
        return True
    if keyword.iskeyword(x):
        return False
    return x.isidentifier()
