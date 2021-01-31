===========
Destructure
===========

This module is heavily inspired by destructuring from Clojure and provides very similar semantics. It provides several macros that allow for destructuring within their arguments.

Introduction
============

To use these macros, you need to require them like so:

.. code-block:: hy

    (require [hy.contrib.destructure [setv+ fn+ defn+ let+ defn/a+ fn/a+]])

Destructuring allows one to easily peek inside a data structure and assign names to values within. For example,

.. code-block:: hy

    (setv+ {[{name :name [weapon1 weapon2] :weapons} :as all-players] :players
            map-name :map
            :keys [tasks-remaining tasks-completed]}
           data)

would be equivalent to

.. code-block:: hy

    (setv map-name (.get data ':map)
          tasks-remaining (.get data ':tasks-remaining)
          tasks-completed (.get data ':tasks-completed)
          all-players (.get data ':players)
          name (.get (nth all-players 0) ':name)
          weapon1 (get (.get (nth all-players 0) ':weapons) 0)
          weapon2 (get (.get (nth all-players 0) ':weapons) 1))

where ``data`` might be defined by

.. code-block:: hy

    (setv data {:players [{:name Joe :weapons [:sword :dagger]}
                          {:name Max :weapons [:axe :crossbow]}]
                :map "Dungeon"
                :tasks-remaining 4})

This is similar to unpacking iterables in Python, such as ``a, *b, c = range(10)``, however it also works on dictionaries, and has several special options.

Patterns
========

Dictionary Pattern
------------------

Dictionary patterns are specified using dictionaries, where the keys corresponds to the symbols which are to be bound, and the values correspond to which key needs to be looked up in the expression for the given symbol.

.. code-block:: hy

    (setv+ {a :a b "b" c (, 1 0)} {:a 1 "b" 2 (, 1 0) 3})
    [a b c] ; => [1 2 3]

The keys can also be one of the following 4 special options: ``:or``, ``:as``, ``:keys``, ``:strs``.

- ``:or`` takes a dictionary of default values.
- ``:as`` takes a variable name which is bound to the entire expression.
- ``:keys`` takes a list of variable names which are looked up as keywords in the expression.
- ``:strs`` is the same as ``:keys`` but uses strings instead.

The ordering of the special options and the variable names doesn't matter, however each special option can be used at most once.

.. code-block:: hy

    (setv+ {:keys [a b] :strs [c d] :or {b 2 d 4} :as full} {:a 1 :b 2 "c" 3})
    [a b c d full] ; => [1 2 3 4 {:a 1 :b 2 "c" 3}]

Variables which are not found in the expression are set to ``None`` if no default value is specified.

List Pattern
------------

List patterns are specified using lists. The nth symbol in the pattern is bound to the nth value in the expression, or ``None`` if the expression has fewer than n values.

There are 2 special options: ``:&`` and ``:as``.

- ``:&`` takes a pattern which is bound to the rest of the expression. This pattern can be anything, including a dictionary, which allows for keyword arguments.
- ``:as`` takes a variable name which is bound to the entire expression.

If the special options are present, they must be last, with ``:&`` preceding ``:as`` if both are present.

.. code-block:: hy

    (setv+ [a b :& rest :as full] (range 5))
    [a b rest full] ; => [0 1 [2 3 4] [0 1 2 3 4]]

    (setv+ [a b :& {:keys [c d] :or {c 3}}] [1 2 :d 4 :e 5]
    [a b c d] ; => [1 2 3 4]

Note that this pattern calls ``list`` on the expression before binding the variables, and hence cannot be used with infinite iterators.

Iterator Pattern
----------------

Iterator patterns are specified using round brackets. They are the same as list patterns, but can be safely used with infinite generators. The iterator pattern does not allow for recursive destructuring within the ``:as`` special option.

Exports
=======

setv+
-----

Usage: ``(setv+ pattern_1 expression_1 ...  pattern_n expression_n)```


Destructuring equivalent of ``setv``. Binds symbols found in a pattern using the corresponding expression.

defn+/fn+
---------

Usage:
``(defn+ function-name argument-list doc+body)``
``(fn+ argument-list body)``

Destructuring equivalents of ``defn``/``fn``. Note that these ignore special symbol ``&optional``, ``&rest`` etc. These will be treated like any other variable name. However the argument list is destructured as a list, so keywords can be used with the ``:&`` special option.

.. code-block:: hy

    (defn+ foo [[x y] :& {d :debug v :verbose :or {d False v False}]
      "doc string"
      [x y d v])

    (foo [1 2] :debug True) ; => [1 2 True False]

defn/a+ / fn/a+
===============

Usage:
``(defn/a+ function-name argument-list doc+body)``
``(fn/a+ argument-list body)``

Async equivalents of defn+ and fn+.

let+
----

Usage: ``(let+ [pattern_1 expression_1 ...  pattern_n expression_n] body)```

Destructuring equivalent of ``let``.

Other useful function/macros
----------------------------

- ``destructure`` function

  Implements the core logic, which would be useful for macros that want to make use of destructuring.

- ``dict=:`` macro

  Same as ``setv+``, except returns a dictionary with symbols to be defined, instead of actually declaring them.

