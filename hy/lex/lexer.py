# Copyright 2021 the authors.
# This file is part of Hy, which is free software licensed under the Expat
# license. See the LICENSE.

from rply import LexerGenerator


lg = LexerGenerator()


# A regexp for something that should end a quoting/unquoting operator
# i.e. a space or a closing brace/paren/curly
end_quote_set = r'\s\)\]\}'
end_quote = r'(?![%s])' % end_quote_set

identifier = r'[^()\[\]{}\'"\s;]+'

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
lg.add('ANNOTATION', r'\^(?![=%s])' % end_quote_set)
lg.add('DISCARD', r'#_')
lg.add('HASHSTARS', r'#\*+')
lg.add('BRACKETSTRING', r'''(?x)
    \# \[ ( [^\[\]]* ) \[    # Opening delimiter
    \n?                      # A single leading newline will be ignored
    ((?:\n|.)*?)             # Content of the string
    \] \1 \]                 # Closing delimiter
    ''')
lg.add('HASHOTHER', r'#%s' % identifier)

# A regexp which matches incomplete strings, used to support
# multi-line strings in the interpreter
partial_string = r'''(?x)
    (?:u|r|ur|ru|b|br|rb|f|fr|rf)? # prefix
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
