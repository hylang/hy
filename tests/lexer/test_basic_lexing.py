from hy.lex.tokenize import tokenize


def test_simple_tokenize():
    """Checking we can still handle something simple."""

    assert [["+", 1, 1]] == tokenize("(+ 1 1)")


def test_double_tokenize():
    """Checking if we can lex two things at once."""

    assert [
        ["+", 1, 2],
        ["-", 1, 1]
    ] == tokenize("(+ 1 2) (- 1 1)")


def test_simple_recurse():
    """ Test recursion """
    assert [
        ['fn',
            'one',
            ['fn', 'two'],
        ]
    ] == tokenize("(fn one (fn two))")


def test_mid_recurse():
    """ Test some crazy recursion """

    assert [
        ['fn',
            'one',
            ['fn', 'two'],
            ['fn', 'three'],
        ]
    ] == tokenize("(fn one (fn two)(fn three))")


def test_mid_recurse_comment():
    """ Test some crazy recursion with a comment """

    assert [
        ['fn',
            'one',
            ['fn', 'two'],
            ['fn', 'three'],
        ]
    ] == tokenize("""
(fn one ; this is a test
    (fn two)(fn three)) ; and so is this
""")


def test_full_recurse():
    """ Test something we could see for real """
    assert [
        ['fn',
            'el',
            ['+',
                1,
                2,
                ['==',
                    1,
                    20
                ],
                ['-',
                    1,
                    1
                ],
            ]
        ],
        ['fn1', 'foo', 'bar']
    ] == tokenize("(fn el (+ 1 2 (== 1 20) (- 1 1)))(fn1 foo bar)")

    
def test_string():
    """ Lex a lone string """
    assert ['"a string"'] == tokenize('"a string"')
