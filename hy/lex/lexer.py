# Copyright (c) 2013 Nicolas Dandrimont <nicolas.dandrimont@crans.org>
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.

from rply import LexerGenerator


lg = LexerGenerator()


# A regexp for something that should end a quoting/unquoting operator
# i.e. a space or a closing brace/paren/curly
end_quote = r'(?![\s\)\]\}])'


lg.add('LPAREN', r'\(')
lg.add('RPAREN', r'\)')
lg.add('LBRACKET', r'\[')
lg.add('RBRACKET', r'\]')
lg.add('LCURLY', r'\{')
lg.add('RCURLY', r'\}')
lg.add('QUOTE', r'\'%s' % end_quote)
lg.add('QUASIQUOTE', r'`%s' % end_quote)
lg.add('UNQUOTESPLICE', r'~@%s' % end_quote)
lg.add('UNQUOTE', r'~%s' % end_quote)
lg.add('HASHBANG', r'#!.*[^\r\n]')


lg.add('STRING', r'''(?x)
    (?:u|r|ur|ru)? # prefix
    "  # start string
    (?:
       | [^"\\]             # non-quote or backslash
       | \\.                # or escaped single character
       | \\x[0-9a-fA-F]{2}  # or escaped raw character
       | \\u[0-9a-fA-F]{4}  # or unicode escape
       | \\U[0-9a-fA-F]{8}  # or long unicode escape
    )* # one or more times
    "  # end string
''')


lg.add('IDENTIFIER', r'[^()\[\]{}\'"\s;]+')


lg.ignore(r';.*[\r\n]+')
lg.ignore(r'\s+')


lexer = lg.build()
