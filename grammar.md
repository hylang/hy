## Lexical syntax ##

    OPEN-PAREN   :=   '('
    
    CLOSE-PAREN  :=   ')'
    
    OPEN-SQUARE  :=   '['
    
    CLOSE-SQUARE :=   ']'
    
    OPEN-CURLY   :=   '{'
    
    CLOSE-CURLY  :=   '}'
    
    WHITESPACE   :=   ' '  |  '\t'  |  '\n'  |  '\r'
    
    COMMENT      :=   ';'  ???
    
    STRING       :=   '"'  ???  '"'
    
    CONSTANT     :=   '*'  ???  '*'
    
    BOOLEAN      :=   'true'  |  'false'
    
    SYMBOL       :=   ???
    
    NUMBER       :=   ???
    
    HASH         :=   '#!'  ???


## Grammar ## ([example](http://docs.python.org/2/reference/grammar.html))

    Hy           :=  HASH  |  COMMENT  |  WHITESPACE  |  Expression

    Expression   :=  OPEN-PAREN  Operator  Args  Close-Paren
    
    Operator     :=  ???
    
    Args         :=  Value(*)
    
    List         :=  OPEN-SQUARE  Value(*)  CLOSE-SQUARE
    
    Map          :=  OPEN-CURLY  ( Value  Value )(*)  CLOSE-CURLY
    
    Value        :=  STRING  |  CONSTANT  |  BOOLEAN  |  SYMBOL  |  NUMBER  |  Expression  |  List  |  Map
 