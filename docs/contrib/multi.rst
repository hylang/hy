========
defmulti
========

.. versionadded:: 0.9.13

`defmulti` lets you arity-overload a function by the given number of 
args and/or kwargs. Inspired by clojures take on `defn`.

.. code-block:: clj

    => (require hy.contrib.multi)
    =>   (defmulti fun
    ...     ([a] a)
    ...     ([a b] "a b")
    ...     ([a b c] "a b c"))
    => (fun 1 2 3)
    'a b c'
    => (fun a b)
    "a b"
    => (fun 1)
    1

