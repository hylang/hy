#


class HYNamespaceCOW(object):
    def __init__(self, inmutable_copy):
        self._inmute = inmutable_copy
        self._mute = {}

    def __contains__(self, key):
        if key in self._mute:
            return True
        return key in self._inmute

    def __getitem__(self, key):
        if key in self._mute:
            return self._mute[key]
        return self._inmute[key]

    def __setitem__(self, key, value):
        self._mute[key] = value

    def clone(self):
        return HYNamespaceCOW(self)
