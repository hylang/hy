#
import ast


def emit_node(node):
    print type(node)
    body = []
    for sn in node.get_children():
        body.append(emit_node(sn))
    print body


def emit(tree):
    ret = []
    for node in tree:
        ret.append(emit_node(node))
    return ret
