import hy.lang.importer
import tests.lang.foo


def square(x):
    return x * x


def test_squares_properly():
    assert tests.lang.foo.square
    assert tests.lang.foo.square(2) == 4
    for x in range(0, 10):
        tests.lang.foo.square(x)
