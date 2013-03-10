foo = (x) ->
    if x < 2
        return x
    foo(x - 1) + foo(x - 2)

alert(foo(10))
