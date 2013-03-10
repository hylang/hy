# Copyright (c) 2011 Larry Myers <larry@larrymyers.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.


from jinja2 import nodes
from jinja2.ext import Extension

from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import guess_lexer, get_lexer_by_name


class PygmentsExtension(Extension):
    """
    A Pygments extension for use with the Jinja2 template language.

    Setup:

    import PygmentsExtension
    from jinja2 import Environment

    jinja2_env = Environment(extensions=[PygmentsExtension])

    Usage:

    {% code 'javascript' %}
    function foo() { console.log('bar'); }
    {% endcode %}
    """
    tags = set(['code'])

    def __init__(self, environment):
        super(PygmentsExtension, self).__init__(environment)

        # add the defaults to the environment
        environment.extend(
            pygments=self
        )

    def parse(self, parser):
        lineno = parser.stream.next().lineno

        args = []
        lang_type = parser.parse_expression()

        if lang_type is not None:
            args.append(lang_type)

        body = parser.parse_statements(['name:endcode'], drop_needle=True)

        return nodes.CallBlock(self.call_method('_pygmentize', args),
                               [], [], body).set_lineno(lineno)

    def _pygmentize(self, lang_type, caller):
        lexer = None
        formatter = HtmlFormatter()
        content = caller()

        if lang_type is None:
            lexer = guess_lexer(content)
        else:
            lexer = get_lexer_by_name(lang_type)

        return highlight(content, lexer, formatter)
