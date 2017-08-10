# -*- encoding: utf-8 -*-
# Copyright 2017 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.

import re
from rply import LexerGenerator
from rply.lexergenerator import Rule, Match


lg = LexerGenerator()


# A regexp for something that should end a quoting/unquoting operator
# i.e. a space or a closing brace/paren/curly
end_quote = r'(?![\s\)\]\}])'

identifier = r'[^()\[\]{}\'"\s;]+'

hashstring_paired_delims = (
  # Unicode General Category "Pi" with the matching closing mark
  (u"«", u"»"), (u"‘", u"’"), (u"‛", u"’"), (u"“", u"”"), (u"‹", u"›"), (u"⸂", u"⸃"), (u"⸄", u"⸅"), (u"⸉", u"⸊"), (u"⸌", u"⸍"), (u"⸜", u"⸝"), (u"⸠", u"⸡"),  # noqa
  # BidiBrackets.txt
  (u"(", u")"), (u"[", u"]"), (u"{", u"}"), (u"༺", u"༻"), (u"༼", u"༽"), (u"᚛", u"᚜"), (u"⁅", u"⁆"), (u"⁽", u"⁾"), (u"₍", u"₎"), (u"⌈", u"⌉"), (u"⌊", u"⌋"), (u"〈", u"〉"), (u"❨", u"❩"), (u"❪", u"❫"), (u"❬", u"❭"), (u"❮", u"❯"), (u"❰", u"❱"), (u"❲", u"❳"), (u"❴", u"❵"), (u"⟅", u"⟆"), (u"⟦", u"⟧"), (u"⟨", u"⟩"), (u"⟪", u"⟫"), (u"⟬", u"⟭"), (u"⟮", u"⟯"), (u"⦃", u"⦄"), (u"⦅", u"⦆"), (u"⦇", u"⦈"), (u"⦉", u"⦊"), (u"⦋", u"⦌"), (u"⦍", u"⦐"), (u"⦏", u"⦎"), (u"⦑", u"⦒"), (u"⦓", u"⦔"), (u"⦕", u"⦖"), (u"⦗", u"⦘"), (u"⧘", u"⧙"), (u"⧚", u"⧛"), (u"⧼", u"⧽"), (u"⸢", u"⸣"), (u"⸤", u"⸥"), (u"⸦", u"⸧"), (u"⸨", u"⸩"), (u"〈", u"〉"), (u"《", u"》"), (u"「", u"」"), (u"『", u"』"), (u"【", u"】"), (u"〔", u"〕"), (u"〖", u"〗"), (u"〘", u"〙"), (u"〚", u"〛"), (u"﹙", u"﹚"), (u"﹛", u"﹜"), (u"﹝", u"﹞"), (u"（", u"）"), (u"［", u"］"), (u"｛", u"｝"), (u"｟", u"｠"), (u"｢", u"｣"))  # noqa

lg.add('LPAREN', r'\(')
lg.add('RPAREN', r'\)')
lg.add('LBRACKET', r'\[')
lg.add('RBRACKET', r'\]')
lg.add('LCURLY', r'\{')
lg.add('RCURLY', r'\}')
lg.add('HLCURLY', r'#\{')
lg.add('QUOTE', r'\'%s' % end_quote)
lg.add('QUASIQUOTE', r'`%s' % end_quote)
lg.add('UNQUOTESPLICE', r'~@%s' % end_quote)
lg.add('UNQUOTE', r'~%s' % end_quote)
lg.add('HASHSTARS', r'#\*+')

class BalancedQStringRule(Rule):
    # We use this class instead of a regex so we can match nested
    # matching delimiters. (Python's `re` doesn't support recursive
    # regexes.)
    name = 'QSTRING'

    def __init__(self, opener, closer):
        self.opener, self.closer = opener, closer

    def matches(self, s, pos):
        # Match `#q{ ... }`, where the curly braces stand for the
        # delimiters and `...` can contain nested pairs of matching
        # delimiters.
        start = pos
        if not s[pos:pos + 3] == '#q' + self.opener:
            return None
        pos += 3
        depth = 1
        while True:
            if pos >= len(s):
                return None
            elif s[pos] == self.opener:
                depth += 1
            elif s[pos] == self.closer:
                depth -= 1
                if depth == 0:
                    break
            pos += 1
        return Match(start, pos + 1)

# q-string, balanced style: #q{ ... }
for opener, closer in hashstring_paired_delims:
    lg.rules.append(BalancedQStringRule(opener, closer))
# q-string, pointy style: #q<foo> ... foo
lg.add('QSTRING', r'#q<([^>]+)>(?:.|\n)*?\1')
# q-string, plain style: #qX ... X
lg.add('QSTRING', u'#q([^<{}])(?:.|\\n)*?\\1'.format(''.join(
    re.escape(opener) for opener, _ in hashstring_paired_delims)))

lg.add('HASHOTHER', r'#%s' % identifier)

# A regexp which matches incomplete strings, used to support
# multi-line strings in the interpreter
partial_string = r'''(?x)
    (?:u|r|ur|ru|b|br|rb)? # prefix
    "  # start string
    (?:
       | [^"\\]             # non-quote or backslash
       | \\(.|\n)           # or escaped single character or newline
       | \\x[0-9a-fA-F]{2}  # or escaped raw character
       | \\u[0-9a-fA-F]{4}  # or unicode escape
       | \\U[0-9a-fA-F]{8}  # or long unicode escape
    )* # one or more times
'''

lg.add('STRING', r'%s"' % partial_string)
lg.add('PARTIAL_STRING', partial_string)

lg.add('IDENTIFIER', identifier)


lg.ignore(r';.*(?=\r|\n|$)')
lg.ignore(r'\s+')


lexer = lg.build()
