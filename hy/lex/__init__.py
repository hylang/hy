from hy.lex.machine import Machine
from hy.lex.states import Idle, LexException

def tokenize(buf):
    machine = Machine(Idle, 0, 0)
    machine.process(buf)
    if type(machine.state) != Idle:
        raise LexException("Incomplete Lex.")
    return machine.nodes
