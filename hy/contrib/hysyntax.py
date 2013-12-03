"""
   Inspired by PyXL, register.py.
"""
from __future__ import with_statement

import codecs, cStringIO, encodings
import sys
from encodings import utf_8
from hy.lex import tokenize
from hy.importer import import_buffer_to_hst, incr_import_buffer_to_ast
import astor.codegen
import ast
from hy.lex import tokenize, LexException, PrematureEndOfInput

def hy_transform(stream):
    try:
        py_buffer = ""
        lisp_expr = ""
        prv_char = None
        in_lisp = False
        counter = 0
        ctx = {}
        for char in stream.read():
            if in_lisp == False and prv_char == "@" and char == "(":
                in_lisp = True
                lisp_expr = "("
                counter += 1
                py_buffer = py_buffer[:-1]
            elif in_lisp == True:
                lisp_expr += char
                if char == ")":
                    counter -= 1
                elif char == "(":
                    counter += 1
                if counter == 0:
                    in_lisp = False
                    genc, ctx = incr_import_buffer_to_ast(lisp_expr, "none", ctx=ctx)
                    py_buffer += astor.codegen.to_source(genc)
            else:
                py_buffer += char
            prv_char = char
        output = py_buffer
    except Exception, ex:
        print ex
        raise

    return output.rstrip()

def hy_transform_string(text):
    stream = cStringIO.StringIO(text)
    return hy_transform(stream)

def hy_decode(input, errors='strict'):
    return utf_8.decode(hy_transform_string(input), errors)

class HyIncrementalDecoder(utf_8.IncrementalDecoder):
    def decode(self, input, final=False):
        self.buffer += input
        if final:
            buff = self.buffer
            self.buffer = ''
            return super(HyIncrementalDecoder, self).decode(
                hy_transform_string(buff), final=True)

class HyStreamReader(utf_8.StreamReader):
    def __init__(self, *args, **kwargs):
        codecs.StreamReader.__init__(self, *args, **kwargs)
        self.stream = cStringIO.StringIO(hy_transform(self.stream))

def search_function(encoding):
    if encoding != 'hy': return None
    # Assume utf8 encoding
    utf8 = encodings.search_function('utf8')
    return codecs.CodecInfo(
        name = 'hy',
        encode = utf8.encode,
        decode = hy_decode,
        incrementalencoder = utf8.incrementalencoder,
        incrementaldecoder = HyIncrementalDecoder,
        streamreader = HyStreamReader,
        streamwriter = utf8.streamwriter)

codecs.register(search_function)

