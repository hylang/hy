from hy.models.list import HyList


def test_list_add():
    a = HyList([1, 2, 3])
    b = HyList([3, 4, 5])
    c = a + b
    assert c == [1, 2, 3, 3, 4, 5]
    assert c.__class__ == HyList
