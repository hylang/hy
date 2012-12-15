from hy.lex.machine import Machine
from hy.lex.states import Idle

def tokenize(buff):
    m = Machine(Idle)
    m.process(buff)
    return m.nodes
