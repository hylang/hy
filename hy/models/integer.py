from hy.models import HyObject


class HyInteger(HyObject, int):
    def __new__(cls, number, *args, **kwargs):
        number = int(number)
        return super(HyInteger, cls).__new__(cls, number)
