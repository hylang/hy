def kwtest(*args, **kwargs):
    return kwargs


def function_with_a_dash():
    pass


class AsyncWithTest:
    def __init__(self, val):
        self.val = val

    async def __aenter__(self):
        return self.val

    async def __aexit__(self, exc_type, exc, traceback):
        self.val = None


async def async_loop(items):
    import asyncio

    for x in items:
        yield x
        await asyncio.sleep(0)
