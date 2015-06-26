from hy.models.set import HySet


hyset = HySet([3, 1, 2, 2])


def test_set():
    assert hyset == [1, 2, 3]
