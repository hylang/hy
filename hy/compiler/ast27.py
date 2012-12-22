# output ast for cpython 2.7

from hy.lang.builtins import builtins
# check compiler/modfaker for other crap

offset = 0
def _new_fn_name():
    global offset
    offset += 1
    return "_hy_fn_%s" % (offset)

# body=[Print(dest=None,
#             values=[BinOp(left=Num(n=1), op=Add(), right=Num(n=1))],
#             nl=True)]
# body=[Expr(value=BinOp(left=Num(n=1), op=Add(), right=Num(n=1)))]



def forge_ast(name, forest):
    for tree in forest:
        print tree
