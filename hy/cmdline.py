# Copyright (c) 2013 Paul Tagliamonte <paultag@debian.org>
# Copyright (c) 2013 Gergely Nagy <algernon@madhouse-project.org>
# Copyright (c) 2013 James King <james@agentultra.com>
# Copyright (c) 2013 Julien Danjou <julien@danjou.info>
# Copyright (c) 2013 Konrad Hinsen <konrad.hinsen@fastmail.net>
# Copyright (c) 2013 Thom Neale <twneale@gmail.com>
# Copyright (c) 2013 Will Kahn-Greene <willg@bluesock.org>
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

import argparse
import code
import ast
import sys

import hy

from hy.importer import ast_compile, import_buffer_to_module
from hy.lex.states import Idle, LexException
from hy.lex.machine import Machine
from hy.compiler import hy_compile
from hy.completer import completion

from hy.macros import macro, require, process
from hy.models.expression import HyExpression
from hy.models.string import HyString
from hy.models.symbol import HySymbol

_machine = Machine(Idle, 1, 0)

try:
    import __builtin__ as builtins
except ImportError:
    import builtins


class HyQuitter(object):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "Use (%s) or Ctrl-D (i.e. EOF) to exit" % (self.name)

    __str__ = __repr__

    def __call__(self, code=None):
        try:
            sys.stdin.close()
        except:
            pass
        raise SystemExit(code)

builtins.quit = HyQuitter('quit')
builtins.exit = HyQuitter('exit')


class HyREPL(code.InteractiveConsole):
    def runsource(self, source, filename='<input>', symbol='single'):
        global _machine

        try:
            _machine.process(source + "\n")
        except LexException:
            _machine = Machine(Idle, 1, 0)
            self.showsyntaxerror(filename)
            return False

        if type(_machine.state) != Idle:
            _machine = Machine(Idle, 1, 0)
            return True

        try:
            tokens = process(_machine.nodes, "__console__")
        except Exception:
            _machine = Machine(Idle, 1, 0)
            self.showtraceback()
            return False

        _machine = Machine(Idle, 1, 0)
        try:
            _ast = hy_compile(tokens, "__console__", root=ast.Interactive)
            code = ast_compile(_ast, filename, symbol)
        except Exception:
            self.showtraceback()
            return False

        self.runcode(code)
        return False


@macro("koan")
def koan_macro():
    return HyExpression([HySymbol('print'),
                         HyString("""
  Ummon asked the head monk, "What sutra are you lecturing on?"
  "The Nirvana Sutra."
  "The Nirvana Sutra has the Four Virtues, hasn't it?"
  "It has."
  Ummon asked, picking up a cup, "How many virtues has this?"
  "None at all, " said the monk.
  "But ancient people said it had, didn't they?" said Ummon.
  "Whatdo you think of what they said?"
  Ummon struck the cup and asked, "You understand?"
  "No," said the monk.
  "Then," said Ummon, "You'd better go on with your lectures on the sutra."
""")])


@macro("ideas")
def ideas_macro():
    return HyExpression([HySymbol('print'),
                         HyString("""

    => (import [sh [figlet]])
    => (figlet "Hi, Hy!")
     _   _ _     _   _       _
    | | | (_)   | | | |_   _| |
    | |_| | |   | |_| | | | | |
    |  _  | |_  |  _  | |_| |_|
    |_| |_|_( ) |_| |_|\__, (_)
            |/         |___/


;;; string things
(.join ", " ["what" "the" "heck"])


;;; this one plays with command line bits
(import [sh [cat grep]])
(-> (cat "/usr/share/dict/words") (grep "-E" "bro$"))


;;; filtering a list w/ a lambda
(filter (lambda [x] (= (% x 2) 0)) (range 0 10))


;;; swaggin' functional bits (Python rulez)
(max (map (lambda [x] (len x)) ["hi" "my" "name" "is" "paul"]))

""")])

require("hy.cmdline", "__console__")
require("hy.cmdline", "__main__")


def run_command(source):
    try:
        import_buffer_to_module("__main__", source)
    except LexException as exc:
        # TODO: This would be better if we had line, col info.
        print(source)
        print(repr(exc))
        return 1
    return 0


def run_file(filename):
    from hy.importer import import_file_to_module
    import_file_to_module("__main__", filename)
    return 0  # right?


def run_repl(hr=None):
    sys.ps1 = "λ → "
    sys.ps2 = "... "

    with completion():
        if not hr:
            hr = HyREPL()

        hr.interact("{appname} {version}".format(
            appname=hy.__appname__,
            version=hy.__version__
        ))

    return 0


def run_icommand(source):
    hr = HyREPL()
    hr.runsource(source, filename='<input>', symbol='single')
    return run_repl(hr)


USAGE = "%(prog)s [-h | -i cmd | -c cmd | file | -] [arg] ..."
VERSION = "%(prog)s " + hy.__version__
EPILOG = """  file         program read from script
  -            program read from stdin
  [arg] ...    arguments passed to program in sys.argv[1:]
"""


def cmdline_handler(scriptname, argv):
    parser = argparse.ArgumentParser(
        prog="hy",
        usage=USAGE,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=EPILOG)
    parser.add_argument("-c", dest="command",
                        help="program passed in as a string")
    parser.add_argument(
        "-i", dest="icommand",
        help="program passed in as a string, then stay in REPL")

    parser.add_argument("-v", action="version", version=VERSION)

    # this will contain the script/program name and any arguments for it.
    parser.add_argument('args', nargs=argparse.REMAINDER,
                        help=argparse.SUPPRESS)

    # stash the hy exectuable in case we need it later
    # mimics Python sys.executable
    hy.executable = argv[0]

    options = parser.parse_args(argv[1:])

    # reset sys.argv like Python
    sys.argv = options.args

    if options.command:
        # User did "hy -c ..."
        return run_command(options.command)

    if options.icommand:
        # User did "hy -i ..."
        return run_icommand(options.icommand)

    if options.args:
        if options.args[0] == "-":
            # Read the program from stdin
            return run_command(sys.stdin.read())

        else:
            # User did "hy <filename>"
            return run_file(options.args[0])

    # User did NOTHING!
    return run_repl()


# entry point for cmd line script "hy"
def hy_main():
    sys.exit(cmdline_handler("hy", sys.argv))


# entry point for cmd line script "hyc"
def hyc_main():
    from hy.importer import write_hy_as_pyc
    write_hy_as_pyc(sys.argv[1])
