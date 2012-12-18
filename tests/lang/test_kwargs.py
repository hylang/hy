import hy.lang.importer


def shim(*args, **kwargs):
    return {"a": args,
            "k": kwargs}


def test_kwargs_proper():
    import tests.lang.kwargs
    val = tests.lang.kwargs.kiwi()
    assert val == {
        "a": ('one', 'two'),
        "k": {
            "three": "three",
            "four": "four"
        }
    }
