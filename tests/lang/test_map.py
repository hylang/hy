from hy.lex.tokenize import tokenize

def test_map_lex():
    assert tokenize('(def {"foo" "bar"})') == [['def', {'foo': 'bar'}]]


def test_map_lex():
    assert tokenize('(def {"foo" "bar" "baz" {"one" "two"}})') == [
        ['def', {
            'foo': 'bar',
            'baz': {
                "one": "two"
            }
        }]
    ]
