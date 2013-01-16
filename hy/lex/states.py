from hy.lang.expression import HYExpression
from hy.lex.errors import LexException
from hy.lang.string import HYString
from hy.lang.symbol import HYSymbol
from hy.lang.number import HYNumber
from hy.lex.machine import Machine
from hy.lang.list import HYList
from hy.lang.bool import HYBool
from hy.lang.map import HYMap


WHITESPACE = [" ", "\t", "\n", "\r"]


def _resolve_atom(value, self):
    def _mangle(obj):
        obj.line = self.machine.line
        obj.column = self.machine.column
        return obj

    if value == "true":
        return _mangle(HYBool(True))
    elif value == "false":
        return _mangle(HYBool(False))

    try:
        return _mangle(HYNumber(value))
    except ValueError:
        pass

    # LISP Variants tend to use *foo* for constants. Let's make it
    # the more pythonic "FOO"
    if value.startswith("*") and value.endswith("*") and len(value) > 1:
        value = value.upper()[1:-1]

    # LISP Variants have a tendency to use "-" in symbols n' shit.
    if value != "-":  # we need subtraction
        value = value.replace("-", "_")

    return _mangle(HYSymbol(value))


class State(object):
    def __init__(self, machine):
        self.machine = machine
        self.sub_machine = None

    def enter(self):
        pass

    def exit(self):
        pass

    def sub(self, machine):
        self.sub_machine = Machine(machine)

    def process(self, x):
        if self.sub_machine:
            self.sub_machine.process(x)
            idle = type(self.sub_machine.state) == Idle
            if idle:
                self.nodes += self.sub_machine.nodes
                self.sub_machine = None
            return

        return self.p(x)


class Comment(State):
    def p(self, x):
        if x == '\n':
            return Idle


class Idle(State):
    def p(self, x):
        if x == "#":
            return HashExpression
        if x == ";":
            return Comment
        if x == "(":
            return Expression
        if x in WHITESPACE:
            return

        raise LexException("Unknown char: %s" % (x))


class HashExpression(State):
    def p(self, x):
        if x == "!":
            return Comment

        raise LexException("Unknwon Hash modifier - %s" % (x))


class Expression(State):
    def enter(self):
        self.nodes = HYExpression([])
        self.bulk = ""

    def exit(self):
        if self.bulk:
            self.nodes.append(_resolve_atom(self.bulk, self))

        self.machine.add_node(self.nodes)

    def commit(self):
        if self.bulk.strip() != "":
            self.nodes.append(_resolve_atom(self.bulk, self))
            self.bulk = ""

    def p(self, x):
        if x == ")":
            return Idle
        if x in WHITESPACE:
            self.commit()
            return
        if x == "\"":
            self.sub(String)
            return
        if x == "(":
            self.sub(Expression)
            return
        if x == "[":
            self.sub(List)
            return
        if x == "{":
            self.sub(Map)
            return
        if x == ";":
            self.sub(Comment)
            return
        self.bulk += x


class List(State):
    def enter(self):
        self.nodes = HYList([])
        self.bulk = ""

    def exit(self):
        if self.bulk:
            self.nodes.append(_resolve_atom(self.bulk, self))
        self.machine.add_node(self.nodes)

    def commit(self):
        if self.bulk.strip() != "":
            self.nodes.append(_resolve_atom(self.bulk, self))
            self.bulk = ""

    def p(self, x):
        if x == "]":
            return Idle
        if x in WHITESPACE:
            self.commit()
            return
        if x == "\"":
            self.sub(String)
            return
        if x == "[":
            self.sub(List)
            return
        if x == "(":
            self.sub(Expression)
            return
        if x == "{":
            self.sub(Map)
            return
        if x == ";":
            self.sub(Comment)
            return
        self.bulk += x


class Map(State):
    def enter(self):
        self.nodes = []
        self.bulk = ""

    def exit(self):
        if self.bulk:
            self.nodes.append(_resolve_atom(self.bulk, self))

        if (len(self.nodes) % 2) != 0:
            raise LexException("Hash map is screwed up")

        ret = HYMap({})
        i = iter(self.nodes)
        hmap = zip(i, i)
        for key, val in hmap:
            ret[key] = val
        self.machine.add_node(ret)

    def commit(self):
        if self.bulk.strip() != "":
            self.nodes.append(_resolve_atom(self.bulk, self))
            self.bulk = ""

    def p(self, x):
        if x == "}":
            return Idle
        if x in WHITESPACE:
            self.commit()
            return
        if x == "\"":
            self.sub(String)
            return
        if x == "[":
            self.sub(List)
            return
        if x == "{":
            self.sub(Map)
            return
        if x == "(":
            self.sub(Expression)
            return
        if x == ";":
            self.sub(Comment)
            return
        self.bulk += x


class String(State):
    magic = {"n": "\n", "t": "\t", "\\": "\\", "\"": "\""}

    def enter(self):
        self.buf = ""
        self.esc = False

    def exit(self):
        self.machine.add_node(HYString(self.buf))

    def p(self, x):
        if x == "\\":
            self.esc = True
            return

        if x == "\"" and not self.esc:
            return Idle

        if self.esc and x not in self.magic:
            raise LexException("Unknown escape: \\%s" % (x))

        elif self.esc:
            x = self.magic[x]

        self.esc = False

        self.buf += x
