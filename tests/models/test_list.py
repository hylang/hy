from hy.models.list import HyList


def test_list_add():
    """Check that adding two HyLists generates a HyList"""
    a = HyList([1, 2, 3])
    b = HyList([3, 4, 5])
    c = a + b
    assert c == [1, 2, 3, 3, 4, 5]
    assert c.__class__ == HyList


def test_list_slice():
    """Check that slicing a HyList produces a HyList"""
    a = HyList([1, 2, 3, 4])
    sl1 = a[1:]
    sl5 = a[5:]

    assert type(sl1) == HyList
    assert sl1 == HyList([2, 3, 4])
    assert type(sl5) == HyList
    assert sl5 == HyList([])
