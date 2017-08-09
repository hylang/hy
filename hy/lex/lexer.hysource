(import [rply [LexerGenerator]])
(defclass Py2HyReturnException [Exception]
  (defn __init__ [self retvalue]
    (setv self.retvalue retvalue)))
(setv lg (LexerGenerator))
(setv end_quote "(?![\\s\\)\\]\\}])")
(setv identifier "[^()\\[\\]{}\\'\"\\s;]+")
(lg.add "LPAREN" "\\(")
(lg.add "RPAREN" "\\)")
(lg.add "LBRACKET" "\\[")
(lg.add "RBRACKET" "\\]")
(lg.add "LCURLY" "\\{")
(lg.add "RCURLY" "\\}")
(lg.add "HLCURLY" "#\\{")
(lg.add "QUOTE" (% "\\'%s" end_quote))
(lg.add "QUASIQUOTE" (% "`%s" end_quote))
(lg.add "UNQUOTESPLICE" (% "~@%s" end_quote))
(lg.add "UNQUOTE" (% "~%s" end_quote))
(lg.add "HASHSTARS" "#\\*+")
(lg.add "HASHOTHER" (% "#%s" identifier))
(setv partial_string "(?x)
    (?:u|r|ur|ru|b|br|rb)? # prefix
    \"  # start string
    (?:
       | [^\"\\\\]             # non-quote or backslash
       | \\\\(.|\\n)           # or escaped single character or newline
       | \\\\x[0-9a-fA-F]{2}  # or escaped raw character
       | \\\\u[0-9a-fA-F]{4}  # or unicode escape
       | \\\\U[0-9a-fA-F]{8}  # or long unicode escape
    )* # one or more times
")
(lg.add "STRING" (% "%s\"" partial_string))
(lg.add "PARTIAL_STRING" partial_string)
(lg.add "IDENTIFIER" identifier)
(lg.ignore ";.*(?=\\r|\\n|$)")
(lg.ignore "\\s+")
(setv lexer (lg.build))
