============
Hy Quick Ref
============

--------------------
How Do I ... in Hy?
--------------------

.. contents:: Contents
    :local:

This page aims to provide more in-depth examples of ``Hy`` syntax for those
coming from ``Python``.

Import Modules
==============
    
.. code-block:: hy
    
    ; Hy imports
    ; Specify namespace using keyword `as`
    (import
        argparse
        pathlib [Path]
        matplotlib [
            colors
            pyplot :as plt
            animation
        ]
        numpy :as np
        ; global import
        kmeans *)
    ; can have multiple import expressions
    (import itertools)

The equivalent ``Python`` is:

.. code-block:: python

    import argparse
    from pathlib import Path
    from matplotlib import colors, pyplot as plt, animation
    import numpy as np
    from kmeans import *

    import itertools

Set Variables
=============

Use :hy:func:`setv`::

    => (setv var-name value)
    => (setv x 3 y 4)
    => (setv [x y] [y x])  ; x = 4; y = 3
    => (setv [a b #* c] [1 2])
    a = 1
    b = 2
    c = []

Due to non-guaranteed evaluation order, it may be worthwhile to assign the
results of complex expressions through multiple calls rather than all at once. 

Use Conditionals
================

``if``, ``when``, ``cond``

For basic ``if...else`` statements, use :hy:func:`if`:

.. code-block:: hy

    (if (and True False)  ; the predicate
        (foo)
        (bar))  ; second clause is the else statement

If you have a branch of form ``if...else pass``, you can use :hy:func:`when`

.. code-block:: hy

    (when (and True True)  ; the predicate
        (foo))  ; second clause is None by default

``if...elif...elif...else`` chains can be written directly using nested ``if``
expressions, but the nested leveling becomes untenable in terms of
organization. Instead, use the :hy:func:`cond` macro:

.. code-block:: hy

    (cond 
        (CONDITION 1)   ; if
            BODY 1
        (CONDITION 2)   ; elif
            BODY 2
        ...
        (CONDITION N)   ; elif
            BODY N
        ; The following is optional. To provide an `else` clause:
        True
            ; else clause stuff here
        )

Coming from Python, you may be familiar with the ``pass`` keyword. This is not
a thing in ``Hy``, so use ``None`` instead. Also, should you want to execute
multiple statements in a single body, use the :hy:func:`do` macro::

    (setv x 10)
    (cond 
        (< x 5) 
            (do 
                (print "Won't get here.")
                foo
                (bar))
        (= x 7) 
            None  ; pass
        (= (% x 2) 1)
            (print "Odd number.")
        True
            (do
                (print "Reached the else clause.")
                (baz)
                (buzz)))

You don't have to format the indentation like this, but it provides a useful
visual association between clauses.

Execute Flow Control
====================

Here's how to do a ``while`` loop:

.. code-block:: hy

    (while (CONDITION)
        ; loop execution here
        LOOP BODY
        ; optional. Executes if loop exits naturally (i.e. the condition is broken)
        (else
            BODY))

A ``for`` loop:

.. code-block:: hy

    ; format
    (for [variable iterable]
        BODY
        (else
            BODY))

    ; example
    => (setv greeting "Hello, World!")
    => (for [[i char] (enumerate greeting)]
            (print i char :sep ": "))
    0: H
    1: e
    2: l
    3: l
    4: o
    5: ,
    6:
    7: W
    8: o
    9: r
    10: l
    11: d
    12: !
Pass Keyword Arguments
======================

.. code-block:: hy

    "Use the `:keyword` symbol followed by the value"
    (print "text1" "text2" :sep "\n")  ; using the `sep` keyword

Python equivalent:

.. code-block:: python

    print("text1", "text2", sep="\n")


Define Functions
================

.. code-block:: hy
    
    ; Named
    (defn <function_name> [<arglist>]
        <body>)

    ; Anonymous
    (fn [x] (* x x))  ; Pass as an argument or assign it a name using `setv`

Optionally, you can use decorators, define type parameters, and provide a
function return annotation before declaring the function name. If you include
more than one of the optional descriptors, they must appear in the above order. 

.. code-block:: hy
    
    ; Format
    (defn [decorator1 decorator2] :tp [T1 T2] #^ type-annotation func-name [params] ...)

    ; Example (note the type annotations)
    (defn #^ (get tuple #(dict np.ndarray)) cluster [
            #^ list data
            #^ int k
            *
            [initial_means None]
            #^ int [ndim None]
            #^ float [tolerance 0.001]
            #^ int [max-iterations 250]
        ]
        ; FUNCTION BODY
        ...)

Here's the Python equivalent:

.. code-block:: python

        def cluster(
                data: list,
                k: int,
                *,
                initial_means = None,
                ndim: int = None,
                tolerance: float = 0.001, 
                max_iterations: int = 250,
        ) -> tuple[dict, np.ndarray]:
            # BODY
            ...

The traditional ``*args``, ``**kwargs`` is represented using the respective
unpacking operators such that they are written ``#* args``, ``#** kwargs``.


Access Class Methods and Attributes
===================================

.. code-block:: hy

    (import numpy :as np)
    (setv arr (np.arange 10))
    (print arr.shape)                 ; => (10,)
    (print (. arr shape))             ; => (10,)
    (print (.sum arr))                ; => 45
    (print (arr.sum :axis None))      ; => 45
    (print (. arr (sum :axis None)))  ; => 45

Define a Class
==============

.. code-block:: hy

    (defclass MyClass [<insert super classes here>]
        (defn __init__ [self x #* args #** kwargs]
            (setv self._x x))
        
        (defn [property] x [self]
            self._x)
            
        (defn [x.setter] x [self value]
            ; perform checks here
            ...
            (setv self._x value)))

    (setv myclass (MyClass 27))
    (print myclass.x)               ; 27
    (setv myclass.x 28)
    (print myclass.x)               ; 28

For the following concepts, it is useful to study the examples in the API page
and read the entries for important usage details.

Use Comprehensions
==================

The examples in `the API page <https://hylang.org/hy/doc/v0.28.0/api#lfor>`_
are very useful.

Use Context Managers
====================

Check out the examples `here <https://hylang.org/hy/doc/v0.28.0/api#with>`_

Handle Exceptions
=================

Check out the examples of `try blocks <https://hylang.org/hy/doc/v0.28.0/api#try>`_

Also for `raising exceptions <https://hylang.org/hy/doc/v0.28.0/api#raise>`_.
