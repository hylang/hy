import re
import unicodedata

MANGLE_DELIM = "X"

normalizes_to_underscore = "_︳︴﹍﹎﹏＿"


def mangle(s):
    """Stringify the argument (with :class:`str`, not :func:`repr` or
    :hy:func:`hy.repr`) and convert it to a valid Python identifier according
    to :ref:`Hy's mangling rules <mangling>`. ::

        (hy.mangle 'foo-bar)   ; => "foo_bar"
        (hy.mangle "🦑")       ; => "hyx_XsquidX"

    If the stringified argument is already both legal as a Python identifier
    and normalized according to Unicode normalization form KC (NFKC), it will
    be returned unchanged. Thus, ``hy.mangle`` is idempotent. ::

        (setv x '♦-->♠)
        (= (hy.mangle (hy.mangle x)) (hy.mangle x))  ; => True

    Generally, the stringifed input is expected to be parsable as a symbol. As
    a convenience, it can also have the syntax of a :ref:`dotted identifier
    <dotted-identifiers>`, and ``hy.mangle`` will mangle the dot-delimited
    parts separately. ::

        (hy.mangle "a.c!.d")  ; => "a.hyx_cXexclamation_markX.d"
    """

    assert s
    s = str(s)

    if "." in s and s.strip("."):
        return ".".join(mangle(x) if x else "" for x in s.split("."))

    # Remove and save leading underscores
    s2 = s.lstrip(normalizes_to_underscore)
    leading_underscores = "_" * (len(s) - len(s2))
    s = s2

    # Convert hyphens without introducing a new leading underscore
    s = s[0] + s[1:].replace("-", "_") if s else s

    # Convert invalid characters or reserved words
    if not (leading_underscores + s).isidentifier():
        # Replace illegal characters with their Unicode character
        # names, or hexadecimal if they don't have one.
        s = "hyx_" + "".join(
            c if c != MANGLE_DELIM and ("S" + c).isidentifier()
            # We prepend the "S" because some characters aren't
            # allowed at the start of an identifier.
            else "{0}{1}{0}".format(
                MANGLE_DELIM,
                unicodedata.name(c, "").lower().replace("-", "H").replace(" ", "_")
                or "U{:x}".format(ord(c)),
            )
            for c in s
        )

    # Step 5: Add back leading underscores
    s = leading_underscores + s

    # Normalize Unicode per PEP 3131.
    s = unicodedata.normalize("NFKC", s)

    assert s.isidentifier()
    return s


def unmangle(s):
    """Stringify the argument and try to convert it to a pretty unmangled
    form. See :ref:`Hy's mangling rules <mangling>`. ::

        (hy.unmangle "hyx_XsquidX")  ; => "🦑"

    Unmangling may not round-trip, because different Hy symbol names can mangle
    to the same Python identifier. In particular, Python itself already
    considers distinct strings that have the same normalized form (according to
    NFKC), such as ``hello`` and ``𝔥𝔢𝔩𝔩𝔬``, to be the same identifier.

    It's an error to call ``hy.unmangle`` on something that looks like a
    properly mangled name but isn't. For example, ``(hy.unmangle
    "hyx_XpizzazzX")`` is erroneous, because there is no Unicode character
    named "PIZZAZZ" (yet)."""

    s = str(s)

    prefix = ""
    suffix = ""
    m = re.fullmatch(r"(_+)(.*?)(_*)", s, re.DOTALL)
    if m:
        prefix, s, suffix = m.groups()

    if s.startswith("hyx_"):
        s = re.sub(
            "{0}(U)?([_a-z0-9H]+?){0}".format(MANGLE_DELIM),
            lambda mo: chr(int(mo.group(2), base=16))
            if mo.group(1)
            else unicodedata.lookup(
                mo.group(2).replace("_", " ").replace("H", "-").upper()
            ),
            s[len("hyx_") :],
        )
    s = s.replace("_", "-")

    return prefix + s + suffix


def slashes2dots(s):
    'Interpret forward slashes as a substitute for periods.'
    return mangle(re.sub(
        r'/(-*)',
        lambda m: '.' + '_' * len(m.group(1)),
        unmangle(s)))
