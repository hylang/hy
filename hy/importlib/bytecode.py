import os
import sys
import marshal
from hy._compat import PY3

from .util import MAGIC_NUMBER, w_long, r_long, _verbose_message


BYTECODE_SUFFIX = '.pyc'

_PYCACHE = '__pycache__'
_OPT = 'opt-'


if PY3:
    def _import_error(*args, **kwargs):
        return ImportError(*args, **kwargs)
else:
    def _import_error(*args, **kwargs):
        return ImportError(*args)


# TODO: Why not use `importlib.util.cache_from_source`?  Assuming we'll
# have a different bytecode suffix?
def get_path(path, optimization=None):
    head, tail = os.path.split(path)
    base, sep, rest = tail.rpartition('.')

    if not PY3:
        return os.path.join(head, base + BYTECODE_SUFFIX)

    tag = sys.implementation.cache_tag
    if tag is None:
        raise NotImplementedError('sys.implementation.cache_tag is None')
    almost_filename = ''.join([(base if base else rest), sep, tag])
    if optimization is None:
        if sys.flags.optimize == 0:
            optimization = ''
        else:
            optimization = sys.flags.optimize
    optimization = str(optimization)
    if optimization != '':
        if not optimization.isalnum():
            raise ValueError('{!r} is not alphanumeric'.format(optimization))
        almost_filename = '{}.{}{}'.format(almost_filename, _OPT, optimization)
    return os.path.join(head, _PYCACHE, almost_filename + BYTECODE_SUFFIX)


def validate_header(data, source_stats=None, name=None, path=None):
    exc_details = {}
    if path is not None:
        exc_details['path'] = path

    magic = data[:4]
    raw_timestamp = data[4:8]
    raw_size = data[8:12]

    if magic != MAGIC_NUMBER:
        message = 'bad python magic number in {!r}: {!r}'.format(name, magic)
        _verbose_message('{}', message)
        raise _import_error(message, **exc_details)
    elif len(raw_timestamp) != 4:
        message = 'reached EOF while reading timestamp in {!r}'.format(name)
        _verbose_message('{}', message)
        raise EOFError(message)
    elif PY3 and len(raw_size) != 4:
        message = 'reached EOF while reading size of source in {!r}'.format(name)
        _verbose_message('{}', message)
        raise EOFError(message)

    if source_stats is not None:
        try:
            source_mtime = int(source_stats['mtime'])
        except KeyError:
            pass
        else:
            if r_long(raw_timestamp) != source_mtime:
                message = 'bytecode is stale for {!r}'.format(name)
                _verbose_message('{}', message)
                raise _import_error(message, **exc_details)

        if PY3:
            try:
                source_size = source_stats['size'] & 0xFFFFFFFF
            except KeyError:
                pass
            else:
                if r_long(raw_size) != source_size:
                    message = 'bytecode is stale for {!r}'.format(name)
                    _verbose_message('{}', message)
                    raise _import_error(message, **exc_details)

    return data[12:] if PY3 else data[8:]


if PY3:
    _code_type = type(validate_header.__code__)
else:
    _code_type = type(validate_header.func_code)


def load(data, name=None, bytecode_path=None, source_path=None):
    """Compile bytecode as returned by validate_header()."""
    code = marshal.loads(data)
    if isinstance(code, _code_type):
        _verbose_message('code object from {!r}', bytecode_path)
        return code
    else:
        raise _import_error('Non-code object in {!r}'.format(bytecode_path),
                            name=name, path=bytecode_path)


def dump(code, mtime=0, source_size=0):
    data = bytearray(MAGIC_NUMBER)
    data.extend(w_long(mtime))
    if PY3:
        data.extend(w_long(source_size))
    data.extend(marshal.dumps(code))
    return data
