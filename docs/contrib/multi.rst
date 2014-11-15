========
defmulti
========

.. versionadded:: 0.10.0

`defmulti` lets you arity-overload a function by the given number of 
args and/or kwargs. Inspired by clojures take on `defn`.

.. code-block:: clj

    => (require hy.contrib.multi)
    =>   (defmulti fun
    ...     ([a] "a")
    ...     ([a b] "a b")
    ...     ([a b c] "a b c"))
    => (fun 1)
    "a"
    => (fun 1 2)
    "a b"
    => (fun 1 2 3)
    "a b c"

