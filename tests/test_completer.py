import pytest
from hy.completer import Completer


def test_completion_hy_core_lang():
    x = Completer()

    assert "accumulate" in x.global_matches("acc")
    assert "take-nth" in x.global_matches("t")


def test_completion_hy_core_shadow():
    x = Completer()

    assert "+" in x.global_matches("+")
    assert "+=" in x.global_matches("+")


def test_completion_hy_attrs():
    x = Completer()

    assert "str.format" in x.attr_matches("str.f")
    assert "print.--class--" in x.attr_matches("print.")


def test_completion_modules():
    import itertools
    import itertools as it
    x = Completer(namespace={"itertools": itertools,
                             "it": itertools})

    assert "itertools.tee" in x.attr_matches("itertools.")
    assert "itertools.tee" in x.attr_matches("itertools.t")
    assert "itertools.tee" not in x.attr_matches("itertools")

    assert "itertools.chain.from-iterable" in x.attr_matches("itertools.chain.")
    assert "itertools.chain.--class--" in x.attr_matches("itertools.chain.")
    assert "itertools.chain.--class--" in x.attr_matches("itertools.chain.-")

    assert "it.chain.--class--" not in x.attr_matches("itertools.chain.-")
    assert "it.chain.--class--" in x.attr_matches("it.chain.-")

    assert "it" in x.global_matches("it")
    assert "itertools" in x.global_matches("it")


def test_completion_unmangling():
    x = Completer()

    assert "numeric?" in x.global_matches("num")

    x.path.append(["func_bang"])
    assert "func!" in x.global_matches("fun")
