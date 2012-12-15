
from hy.lex.tokenize import tokenize

print tokenize("""
(+ 2 (+ 1 1) (- 1 1))
""")
