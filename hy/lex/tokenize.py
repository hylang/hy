from hy.lex.machine import Machine
from hy.lex.states import Idle
from hy.lex.errors import LexException


def tokenize(buff):
    m = Machine(Idle)
    m.process(buff)
    if type(m.state) != Idle:
        raise LexException("End of file.")
    return m.nodes
