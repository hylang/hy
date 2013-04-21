from hy import util


def test_temporary_attribute_value():
    class O(object):
        def __init__(self):
            self.foobar = 0

    o = O()

    with util.temporary_attribute_value(o, "foobar", 42):
        assert o.foobar == 42
    assert o.foobar == 0
