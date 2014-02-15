=================
Hy Core
=================


Core Functions
===============

.. _is-coll-fn:

coll?
-----

.. versionadded:: 0.9.13

Usage: ``(coll? x)``

Returns true if argument is iterable and not a string.

.. code-block:: clojure

   => (coll? [1 2 3 4])
   True

   => (coll? {"a" 1 "b" 2})
   True

   => (coll? "abc")
   False


cons
----

.. versionadded:: 0.9.13

Usage: ``(cons a b)``

Returns a fresh :ref:`cons cell <hycons>` with car `a` and cdr `b`.

.. code-block:: clojure

   => (setv a (cons 'hd 'tl))

   => (= 'hd (car a))
   True

   => (= 'tl (cdr a))
   True


cons?
-----

.. versionadded:: 0.9.13

Usage: ``(cons? foo)``

Checks whether ``foo`` is a :ref:`cons cell <hycons>`.

.. code-block:: clojure

   => (setv a (cons 'hd 'tl))

   => (cons? a)
   True

   => (cons? nil)
   False

   => (cons? [1 2 3])
   False

.. _dec-fn:

dec
---

Usage: ``(dec x)``

Return one less than x. Equivalent to ``(- x 1)``.

Raises ``TypeError`` if ``(not (numeric? x))``.

.. code-block:: clojure

   => (dec 3)
   2

   => (dec 0)
   -1

   => (dec 12.3)
   11.3


.. _disassemble-fn:

disassemble
-----------

.. versionadded:: 0.9.13

Usage: ``(disassemble tree &optional [codegen false])``

Dump the Python AST for given Hy ``tree`` to standard output. If *codegen*
is ``true`` function prints Python code instead.

.. code-block:: clojure

   => (disassemble '(print "Hello World!"))
   Module(
    body=[
        Expr(value=Call(func=Name(id='print'), args=[Str(s='Hello World!')], keywords=[], starargs=None, kwargs=None))])

   => (disassemble '(print "Hello World!") true)
   print('Hello World!')


.. _emtpy?-fn:

empty?
------

Usage: ``(empty? coll)``

Return True if ``coll`` is empty, i.e. ``(= 0 (len coll))``.

.. code-block:: clojure

   => (empty? [])
   True

   => (empty? "")
   True

   => (empty? (, 1 2))
   False


.. _every?-fn:

every?
------

.. versionadded:: 0.9.13

Usage: ``(every? pred coll)``

Return True if ``(pred x)`` is logical true for every ``x`` in ``coll``, otherwise False. Return True if ``coll`` is empty.

.. code-block:: clojure

   => (every? even? [2 4 6])
   True

   => (every? even? [1 3 5])
   False

   => (every? even? [2 4 5])
   False

   => (every? even? [])
   True


.. _float?-fn:

float?
-------

Usage: ``(float? x)``

Return True if x is a float.

.. code-block:: clojure

   => (float? 3.2)
   True

   => (float? -2)
   False


.. _even?-fn:

even?
-----

Usage: ``(even? x)``

Return True if x is even.

Raises ``TypeError`` if ``(not (numeric? x))``.

.. code-block:: clojure

   => (even? 2)
   True

   => (even? 13)
   False

   => (even? 0)
   True


.. _identity-fn:

identity
--------

Usage: ``(identity x)``

Returns argument supplied to the function

.. code-block:: clojure

   => (identity 4)
   4

   => (list (map identity [1 2 3 4]))
   [1 2 3 4]


.. _inc-fn:

inc
---

Usage: ``(inc x)``

Return one more than x. Equivalent to ``(+ x 1)``.

Raises ``TypeError`` if ``(not (numeric? x))``.

.. code-block:: clojure

   => (inc 3)
   4

   => (inc 0)
   1

   => (inc 12.3)
   13.3


.. _instance?-fn:

instance?
---------

Usage: ``(instance? CLASS x)``

Return True if x is an instance of CLASS.

.. code-block:: clojure

   => (instance? float 1.0)
   True

   => (instance? int 7)
   True

   => (instance? str (str "foo"))
   True

   => (defclass TestClass [object])
   => (setv inst (TestClass))
   => (instance? TestClass inst)
   True

.. _integer?-fn:

integer?
--------

Usage: ``(integer? x)``

Return True if x is an integer. For Python 2, this is
either ``int`` or ``long``. For Python 3, this is ``int``.

.. code-block:: clojure

   => (integer? 3)
   True

   => (integer? -2.4)
   False


.. _iterable?-fn:

iterable?
---------

Usage: ``(iterable? x)``

Return True if x is iterable. Iterable objects return a new iterator
when ``(iter x)`` is called. Contrast with :ref:`iterator?-fn`.

.. code-block:: clojure

   => ;; works for strings
   => (iterable? (str "abcde"))
   True

   => ;; works for lists
   => (iterable? [1 2 3 4 5])
   True

   => ;; works for tuples
   => (iterable? (, 1 2 3))
   True

   => ;; works for dicts
   => (iterable? {:a 1 :b 2 :c 3})
   True

   => ;; works for iterators/generators
   => (iterable? (repeat 3))
   True


.. _iterator?-fn:

iterator?
---------

Usage: ``(iterator? x)``

Return True if x is an iterator. Iterators are objects that return
themselves as an iterator when ``(iter x)`` is called.
Contrast with :ref:`iterable?-fn`.

.. code-block:: clojure

   => ;; doesn't work for a list
   => (iterator? [1 2 3 4 5])
   False

   => ;; but we can get an iter from the list
   => (iterator? (iter [1 2 3 4 5]))
   True

   => ;; doesn't work for dict
   => (iterator? {:a 1 :b 2 :c 3})
   False

   => ;; create an iterator from the dict
   => (iterator? (iter {:a 1 :b 2 :c 3}))
   True

list*
-----

Usage: ``(list* head &rest tail)``

Generate a chain of nested cons cells (a dotted list) containing the
arguments. If the argument list only has one element, return it.

.. code-block:: clojure

   => (list* 1 2 3 4)
   (1 2 3 . 4)

   => (list* 1 2 3 [4])
   [1, 2, 3, 4]

   => (list* 1)
   1

   => (cons? (list* 1 2 3 4))
   True

.. _macroexpand-fn:

macroexpand
-----------

.. versionadded:: 0.9.13

Usage: ``(macroexpand form)``

Returns the full macro expansion of form.

.. code-block:: clojure

   => (macroexpand '(-> (a b) (x y)))
   (u'x' (u'a' u'b') u'y')

   => (macroexpand '(-> (a b) (-> (c d) (e f))))
   (u'e' (u'c' (u'a' u'b') u'd') u'f')

.. _macroexpand-1-fn:

macroexpand-1
-------------

.. versionadded:: 0.9.13

Usage: ``(macroexpand-1 form)``

Returns the single step macro expansion of form.

.. code-block:: clojure

   => (macroexpand-1 '(-> (a b) (-> (c d) (e f))))
   (u'_>' (u'a' u'b') (u'c' u'd') (u'e' u'f'))

.. _neg?-fn:

neg?
----

Usage: ``(neg? x)``

Return True if x is less than zero (0).

Raises ``TypeError`` if ``(not (numeric? x))``.

.. code-block:: clojure

   => (neg? -2)
   True

   => (neg? 3)
   False

   => (neg? 0)
   False


.. _nil?-fn:

nil?
-----

Usage: ``(nil? x)``

Return True if x is nil/None.

.. code-block:: clojure

   => (nil? nil)
   True

   => (nil? None)
   True

   => (nil? 0)
   False

   => (setf x nil)
   => (nil? x)
   True

   => ;; list.append always returns None
   => (nil? (.append [1 2 3] 4))
   True


.. _none?-fn:

none?
-----

Usage: ``(none? x)``

Return True if x is None.

.. code-block:: clojure

   => (none? None)
   True

   => (none? 0)
   False

   => (setf x None)
   => (none? x)
   True

   => ;; list.append always returns None
   => (none? (.append [1 2 3] 4))
   True


.. _nth-fn:

nth
---

Usage: ``(nth coll n)``

Return the `nth` item in a collection, counting from 0. Unlike
``get``, ``nth`` works on both iterators and iterables. Returns ``None``
if the `n` is outside the range of `coll`.

.. code-block:: clojure

   => (nth [1 2 4 7] 1)
   2

   => (nth [1 2 4 7] 3)
   7

   => (none? (nth [1 2 4 7] 5))
   True

   => (nth (take 3 (drop 2 [1 2 3 4 5 6])) 2))
   5

.. _numeric?-fn:

numeric?
---------

Usage: ``(numeric? x)``

Return True if x is a numeric, as defined in the Python
numbers module class ``numbers.Number``.

.. code-block:: clojure

   => (numeric? -2)
   True

   => (numeric? 3.2)
   True

   => (numeric? "foo")
   False


.. _odd?-fn:

odd?
----

Usage: ``(odd? x)``

Return True if x is odd.

Raises ``TypeError`` if ``(not (numeric? x))``.

.. code-block:: clojure

   => (odd? 13)
   True

   => (odd? 2)
   False

   => (odd? 0)
   False


.. _pos?-fn:

pos?
----

Usage: ``(pos? x)``

Return True if x is greater than zero (0).

Raises ``TypeError`` if ``(not (numeric? x))``.

.. code-block:: clojure

   => (pos? 3)
   True

   => (pos? -2)
   False

   => (pos? 0)
   False


.. _second-fn:

second
-------

Usage: ``(second coll)``

Return the second member of ``coll``. Equivalent to
``(get coll 1)``

.. code-block:: clojure

   => (second [0 1 2])
   1


.. _some-fn:

some
----

.. versionadded:: 0.9.13

Usage: ``(some pred coll)``

Return True if ``(pred x)`` is logical true for any ``x`` in ``coll``, otherwise False. Return False if ``coll`` is empty.

.. code-block:: clojure

   => (some even? [2 4 6])
   True

   => (some even? [1 3 5])
   False

   => (some even? [1 3 6])
   True

   => (some even? [])
   False


.. _string?-fn:

string?
-------

Usage: ``(string? x)``

Return True if x is a string.

.. code-block:: clojure

   => (string? "foo")
   True

   => (string? -2)
   False

.. _zero?-fn:

zero?
-----

Usage: ``(zero? x)``

Return True if x is zero (0).

.. code-block:: clojure

   => (zero? 3)
   False

   => (zero? -2)
   False

   => (zero? 0)
   True


Sequence Functions
=======================

Sequence functions can either create or operate on a potentially
infinite sequence without requiring the sequence be fully realized in
a list or similar container. They do this by returning a Python
iterator.

We can use the canonical infinite Fibonacci number generator
as an example of how to use some of these functions.

.. code-block:: clojure

   (defn fib []
     (setv a 0)
     (setv b 1)
     (while true
       (yield a)
       (setv (, a b) (, b (+ a b)))))


Note the ``(while true ...)`` loop. If we run this in the REPL,

.. code-block:: clojure

   => (fib)
   <generator object fib at 0x101e642d0>


Calling the function only returns an iterator, but does no
work until we consume it. Trying something like this is not recommend as
the infinite loop will run until it consumes all available RAM, or
in this case until I killed it.

.. code-block:: clojure

   => (list (fib))
   [1]    91474 killed     hy


To get the first 10 Fibonacci numbers, use :ref:`take-fn`. Note that
:ref:`take-fn` also returns a generator, so I create a list from it.

.. code-block:: clojure

   => (list (take 10 (fib)))
   [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]


To get the Fibonacci number at index 9, (starting from 0):

.. code-block:: clojure

   => (nth (fib) 9)
   34


.. _cycle-fn:

cycle
------

Usage: ``(cycle coll)``

Return an infinite iterator of the members of coll.

.. code-block:: clj

   => (list (take 7 (cycle [1 2 3])))
   [1, 2, 3, 1, 2, 3, 1]

   => (list (take 2 (cycle [1 2 3])))
   [1, 2]


.. _distinct-fn:

distinct
--------

Usage: ``(distinct coll)``

Returns an iterator containing only the unique members in ``coll``.

.. code-block:: clojure

   => (list (distinct [ 1 2 3 4 3 5 2 ]))
   [1, 2, 3, 4, 5]

   => (list (distinct []))
   []

   => (list (distinct (iter [ 1 2 3 4 3 5 2 ])))
   [1, 2, 3, 4, 5]


.. _drop-fn:

drop
----

Usage: ``(drop n coll)``

Return an iterator, skipping the first ``n`` members of ``coll``

.. code-block:: clojure

   => (list (drop 2 [1 2 3 4 5]))
   [3, 4, 5]

   => (list (drop 4 [1 2 3 4 5]))
   [5]

   => (list (drop 0 [1 2 3 4 5]))
   [1, 2, 3, 4, 5]

   => (list (drop 6 [1 2 3 4 5]))
   []

.. _drop-while-fn:

drop-while
-----------

Usage: ``(drop-while pred coll)``

Return an iterator, skipping members of ``coll`` until ``pred``
is False.

.. code-block:: clojure

   => (list (drop-while even? [2 4 7 8 9]))
   [7, 8, 9]

   => (list (drop-while numeric? [1 2 3 None "a"])))
   [None, u'a']

   => (list (drop-while pos? [2 4 7 8 9]))
   []


.. _filter-fn:

filter
------

Usage: ``(filter pred coll)``

Return an iterator for all items in ``coll`` that pass the predicate ``pred``.

See also :ref:`remove-fn`.

.. code-block:: clojure

   => (list (filter pos? [1 2 3 -4 5 -7]))
   [1, 2, 3, 5]

   => (list (filter even? [1 2 3 -4 5 -7]))
   [2, -4]

.. _flatten-fn:

flatten
-------

.. versionadded:: 0.9.12

Usage: ``(flatten coll)``

Return a single list of all the items in ``coll``, by flattening all
contained lists and/or tuples.

.. code-block:: clojure

   => (flatten [1 2 [3 4] 5])
   [1, 2, 3, 4, 5]

   => (flatten ["foo" (, 1 2) [1 [2 3] 4] "bar"])
   ['foo', 1, 2, 1, 2, 3, 4, 'bar']


.. _iterate-fn:

iterate
-------

Usage: ``(iterate fn x)``

Return an iterator of `x`, `fn(x)`, `fn(fn(x))`.

.. code-block:: clojure

   => (list (take 5 (iterate inc 5)))
   [5, 6, 7, 8, 9]

   => (list (take 5 (iterate (fn [x] (* x x)) 5)))
   [5, 25, 625, 390625, 152587890625]


.. _remove-fn:

remove
------

Usage: ``(remove pred coll)``

Return an iterator from ``coll`` with elements that pass the
predicate, ``pred``, removed.

See also :ref:`filter-fn`.

.. code-block:: clojure

   => (list (remove odd? [1 2 3 4 5 6 7]))
   [2, 4, 6]

   => (list (remove pos? [1 2 3 4 5 6 7]))
   []

   => (list (remove neg? [1 2 3 4 5 6 7]))
   [1, 2, 3, 4, 5, 6, 7]



.. _repeat-fn:

repeat
------

Usage: ``(repeat x)``

Return an iterator (infinite) of ``x``.

.. code-block:: clojure

   => (list (take 6 (repeat "s")))
   [u's', u's', u's', u's', u's', u's']


.. _repeatedly-fn:

repeatedly
----------

Usage: ``(repeatedly fn)``

Return an iterator by calling ``fn`` repeatedly.

.. code-block:: clojure

   => (import [random [randint]])

   => (list (take 5 (repeatedly (fn [] (randint 0 10)))))
   [6, 2, 0, 6, 7]


.. _take-fn:

take
----

Usage: ``(take n coll)``

Return an iterator containing the first ``n`` members of ``coll``.

.. code-block:: clojure

   => (list (take 3 [1 2 3 4 5]))
   [1, 2, 3]

   => (list (take 4 (repeat "s")))
   [u's', u's', u's', u's']

   => (list (take 0 (repeat "s")))
   []

.. _take-nth-fn:

take-nth
--------

Usage: ``(take-nth n coll)``

Return an iterator containing every ``nth`` member of ``coll``.

.. code-block:: clojure

   => (list (take-nth 2 [1 2 3 4 5 6 7]))
   [1, 3, 5, 7]

   => (list (take-nth 3 [1 2 3 4 5 6 7]))
   [1, 4, 7]

   => (list (take-nth 4 [1 2 3 4 5 6 7]))
   [1, 5]

   => (list (take-nth 10 [1 2 3 4 5 6 7]))
   [1]


.. _take-while-fn:

take-while
----------

Usage: ``(take-while pred coll)``

Return an iterator from ``coll`` as long as predicate, ``pred`` returns True.

.. code-block:: clojure

   => (list (take-while pos? [ 1 2 3 -4 5]))
   [1, 2, 3]

   => (list (take-while neg? [ -4 -3 1 2 5]))
   [-4, -3]

   => (list (take-while neg? [ 1 2 3 -4 5]))
   []
