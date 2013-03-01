from hy.lex.machine import Machine
from hy.lex.states import Idle

def tokenize(buf):
    machine = Machine(Idle, 0, 0)
    machine.process(buf)
    return machine.nodes
