=======
Hy Core
=======


Core Functions
==============

.. _butlast-fn:

butlast
-------

Usage: ``(butlast coll)``

Returns an iterator of all but the last item in *coll*.

.. code-block:: hy

   => (list (butlast (range 10)))
   [0, 1, 2, 3, 4, 5, 6, 7, 8]

   => (list (butlast [1]))
   []

   => (list (butlast []))
   []

   => (list (take 5 (butlast (count 10))))
   [10, 11, 12, 13, 14]


.. _is-coll-fn:

coll?
-----

.. versionadded:: 0.10.0

Usage: ``(coll? x)``

Returns ``True`` if *x* is iterable and not a string.

.. code-block:: hy

   => (coll? [1 2 3 4])
   True

   => (coll? {"a" 1 "b" 2})
   True

   => (coll? "abc")
   False


.. _comp:

comp
----

Usage: ``(comp f g)``

Compose zero or more functions into a new function. The new function will
chain the given functions together, so ``((comp g f) x)`` is equivalent to
``(g (f x))``. Called without arguments, ``comp`` returns ``identity``.

.. code-block:: hy

   => (setv example (comp str +))
   => (example 1 2 3)
   "6"

   => (setv simple (comp))
   => (simple "hello")
   "hello"


.. _complement:

complement
----------

.. versionadded:: 0.12.0

Usage: ``(complement f)``

Returns a new function that returns the same thing as ``f``, but logically
inverted. So, ``((complement f) x)`` is equivalent to ``(not (f x))``.

.. code-block:: hy

   => (setv inverse (complement identity))
   => (inverse True)
   False
   => (inverse 1)
   False
   => (inverse False)
   True


.. _constantly:

constantly
----------

.. versionadded:: 0.12.0

Usage ``(constantly 42)``

Create a new function that always returns the given value, regardless of
the arguments given to it.

.. code-block:: hy

   => (setv answer (constantly 42))
   => (answer)
   42
   => (answer 1 2 3)
   42
   => (answer 1 :foo 2)
   42


.. _dec-fn:

dec
---

Usage: ``(dec x)``

Returns one less than *x*. Equivalent to ``(- x 1)``. Raises ``TypeError``
if ``(not (numeric? x))``.

.. code-block:: hy

   => (dec 3)
   2

   => (dec 0)
   -1

   => (dec 12.3)
   11.3


.. _disassemble-fn:

disassemble
-----------

.. versionadded:: 0.10.0

Usage: ``(disassemble tree &optional [codegen false])``

Dump the Python AST for given Hy *tree* to standard output. If *codegen*
is ``True``, the function prints Python code instead.

.. code-block:: hy

   => (disassemble '(print "Hello World!"))
   Module(
    body=[
        Expr(value=Call(func=Name(id='print'), args=[Str(s='Hello World!')], keywords=[], starargs=None, kwargs=None))])

   => (disassemble '(print "Hello World!") True)
   print('Hello World!')


.. _empty?-fn:

empty?
------

Usage: ``(empty? coll)``

Returns ``True`` if *coll* is empty. Equivalent to ``(= 0 (len coll))``.

.. code-block:: hy

   => (empty? [])
   True

   => (empty? "")
   True

   => (empty? (, 1 2))
   False


.. _eval-fn:

eval
----

``eval`` evaluates a quoted expression and returns the value. The optional
second and third arguments specify the dictionary of globals to use and the
module name. The globals dictionary defaults to ``(local)`` and the module name
defaults to the name of the current module.  An optional fourth keyword parameter,
``compiler``, allows one to re-use an existing ``HyASTCompiler`` object for the
compilation step.

.. code-block:: clj

   => (eval '(print "Hello World"))
   "Hello World"

If you want to evaluate a string, use ``read-str`` to convert it to a
form first:

.. code-block:: clj

   => (eval (read-str "(+ 1 1)"))
   2


.. _every?-fn:

every?
------

.. versionadded:: 0.10.0

Usage: ``(every? pred coll)``

Returns ``True`` if ``(pred x)`` is logical true for every *x* in *coll*,
otherwise ``False``. Return ``True`` if *coll* is empty.

.. code-block:: hy

   => (every? even? [2 4 6])
   True

   => (every? even? [1 3 5])
   False

   => (every? even? [2 4 5])
   False

   => (every? even? [])
   True


.. _exec-fn:

exec
----

Equivalent to Python 3's built-in function :py:func:`exec`.

.. code-block:: clj

    => (exec "print(a + b)" {"a" 1} {"b" 2})
    3


.. _float?-fn:

float?
-------

Usage: ``(float? x)``

Returns ``True`` if *x* is a float.

.. code-block:: hy

   => (float? 3.2)
   True

   => (float? -2)
   False


.. _fraction-fn:

fraction
--------

Returns a Python object of type ``fractions.Fraction``.

.. code-block:: hy

   => (fraction 1 2)
   Fraction(1, 2)

Note that Hy has a built-in fraction literal that does the same thing:

.. code-block:: hy

   => 1/2
   Fraction(1, 2)


.. _even?-fn:

even?
-----

Usage: ``(even? x)``

Returns ``True`` if *x* is even. Raises ``TypeError`` if
``(not (numeric? x))``.

.. code-block:: hy

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

Returns the argument supplied to the function.

.. code-block:: hy

   => (identity 4)
   4

   => (list (map identity [1 2 3 4]))
   [1 2 3 4]


.. _inc-fn:

inc
---

Usage: ``(inc x)``

Returns one more than *x*. Equivalent to ``(+ x 1)``. Raises ``TypeError``
if ``(not (numeric? x))``.

.. code-block:: hy

   => (inc 3)
   4

   => (inc 0)
   1

   => (inc 12.3)
   13.3


.. _instance?-fn:

instance?
---------

Usage: ``(instance? class x)``

Returns ``True`` if *x* is an instance of *class*.

.. code-block:: hy

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

Returns `True` if *x* is an integer. For Python 2, this is
either ``int`` or ``long``. For Python 3, this is ``int``.

.. code-block:: hy

   => (integer? 3)
   True

   => (integer? -2.4)
   False


.. _interleave-fn:

interleave
----------

.. versionadded:: 0.10.1

Usage: ``(interleave seq1 seq2 ...)``

Returns an iterable of the first item in each of the sequences,
then the second, etc.

.. code-block:: hy

   => (list (interleave (range 5) (range 100 105)))
   [0, 100, 1, 101, 2, 102, 3, 103, 4, 104]

   => (list (interleave (range 1000000) "abc"))
   [0, 'a', 1, 'b', 2, 'c']


.. _interpose-fn:

interpose
---------

.. versionadded:: 0.10.1

Usage: ``(interpose item seq)``

Returns an iterable of the elements of the sequence separated by the item.

.. code-block:: hy

   => (list (interpose "!" "abcd"))
   ['a', '!', 'b', '!', 'c', '!', 'd']

   => (list (interpose -1 (range 5)))
   [0, -1, 1, -1, 2, -1, 3, -1, 4]


.. _iterable?-fn:

iterable?
---------

Usage: ``(iterable? x)``

Returns ``True`` if *x* is iterable. Iterable objects return a new iterator
when ``(iter x)`` is called. Contrast with :ref:`iterator?-fn`.

.. code-block:: hy

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

Returns ``True`` if *x* is an iterator. Iterators are objects that return
themselves as an iterator when ``(iter x)`` is called. Contrast with
:ref:`iterable?-fn`.

.. code-block:: hy

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


.. _juxt-fn:

juxt
----

.. versionadded:: 0.12.0

Usage: ``(juxt f &rest fs)``

Return a function that applies each of the supplied functions to a
single set of arguments and collects the results into a list.

.. code-block:: hy

   => ((juxt min max sum) (range 1 101))
   [1, 100, 5050]

   => (dict (map (juxt identity ord) "abcdef"))
   {'f': 102, 'd': 100, 'b': 98, 'e': 101, 'c': 99, 'a': 97}

   => ((juxt + - * /) 24 3)
   [27, 21, 72, 8.0]


.. _keyword-fn:

keyword
-------

.. versionadded:: 0.10.1

Usage: ``(keyword "foo")``

Create a keyword from the given value. Strings, numbers, and even
objects with the `__name__` magic will work.

.. code-block:: hy

   => (keyword "foo")
   HyKeyword('foo')

   => (keyword 1)
   HyKeyword('foo')

.. _keyword?-fn:

keyword?
--------

.. versionadded:: 0.10.1

Usage: ``(keyword? foo)``

Check whether *foo* is a :ref:`keyword<HyKeyword>`.

.. code-block:: hy

   => (keyword? :foo)
   True

   => (setv foo 1)
   => (keyword? foo)
   False


.. _macroexpand-fn:

macroexpand
-----------

.. versionadded:: 0.10.0

Usage: ``(macroexpand form)``

Returns the full macro expansion of *form*.

.. code-block:: hy

    => (macroexpand '(-> (a b) (x y)))
    HyExpression([
      HySymbol('x'),
      HyExpression([
        HySymbol('a'),
        HySymbol('b')]),
      HySymbol('y')])
    => (macroexpand '(-> (a b) (-> (c d) (e f))))
    HyExpression([
      HySymbol('e'),
      HyExpression([
        HySymbol('c'),
        HyExpression([
          HySymbol('a'),
          HySymbol('b')]),
        HySymbol('d')]),
      HySymbol('f')])

.. _macroexpand-1-fn:

macroexpand-1
-------------

.. versionadded:: 0.10.0

Usage: ``(macroexpand-1 form)``

Returns the single step macro expansion of *form*.

.. code-block:: hy

    => (macroexpand-1 '(-> (a b) (-> (c d) (e f))))
    HyExpression([
      HySymbol('_>'),
      HyExpression([
        HySymbol('a'),
        HySymbol('b')]),
      HyExpression([
        HySymbol('c'),
        HySymbol('d')]),
      HyExpression([
        HySymbol('e'),
        HySymbol('f')])])

.. _mangle-fn:

mangle
------

Usage: ``(mangle x)``

Stringify the input and translate it according to :ref:`Hy's mangling rules
<mangling>`.

.. code-block:: hylang

    => (mangle "foo-bar")
    'foo_bar'

.. _merge-with-fn:

merge-with
----------

.. versionadded:: 0.10.1

Usage: ``(merge-with f &rest maps)``

Returns a map that consist of the rest of the maps joined onto first.
If a key occurs in more than one map, the mapping(s) from the latter
(left-to-right) will be combined with the mapping in the result by
calling ``(f val-in-result val-in-latter)``.

.. code-block:: hy

    => (merge-with + {"a" 10 "b" 20} {"a" 1 "c" 30})
    {u'a': 11L, u'c': 30L, u'b': 20L}


.. _name-fn:

name
----

.. versionadded:: 0.10.1

Usage: ``(name :keyword)``

Convert the given value to a string. Keyword special character will be
stripped. Strings will be used as is. Even objects with the `__name__`
magic will work.

.. code-block:: hy

   => (name :foo)
   u'foo'

.. _neg?-fn:

neg?
----

Usage: ``(neg? x)``

Returns ``True`` if *x* is less than zero. Raises ``TypeError`` if
``(not (numeric? x))``.

.. code-block:: hy

   => (neg? -2)
   True

   => (neg? 3)
   False

   => (neg? 0)
   False

.. _none?-fn:

none?
-----

Usage: ``(none? x)``

Returns ``True`` if *x* is ``None``.

.. code-block:: hy

   => (none? None)
   True

   => (none? 0)
   False

   => (setv x None)
   => (none? x)
   True

   => ;; list.append always returns None
   => (none? (.append [1 2 3] 4))
   True


.. _nth-fn:

nth
---

Usage: ``(nth coll n &optional [default None])``

Returns the *n*-th item in a collection, counting from 0. Return the
default value, ``None``, if out of bounds (unless specified otherwise).
Raises ``ValueError`` if *n* is negative.

.. code-block:: hy

   => (nth [1 2 4 7] 1)
   2

   => (nth [1 2 4 7] 3)
   7

   => (none? (nth [1 2 4 7] 5))
   True

   => (nth [1 2 4 7] 5 "default")
   'default'

   => (nth (take 3 (drop 2 [1 2 3 4 5 6])) 2))
   5

   => (nth [1 2 4 7] -1)
   Traceback (most recent call last):
     ...
   ValueError: Indices for islice() must be None or an integer: 0 <= x <= sys.maxsize.


.. _numeric?-fn:

numeric?
--------

Usage: ``(numeric? x)``

Returns ``True`` if *x* is a numeric, as defined in Python's
``numbers.Number`` class.

.. code-block:: hy

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

Returns ``True`` if *x* is odd. Raises ``TypeError`` if
``(not (numeric? x))``.

.. code-block:: hy

   => (odd? 13)
   True

   => (odd? 2)
   False

   => (odd? 0)
   False

.. _partition-fn:

partition
---------

Usage: ``(partition coll [n] [step] [fillvalue])``

Chunks *coll* into *n*-tuples (pairs by default).

.. code-block:: hy

    => (list (partition (range 10)))  ; n=2
    [(0, 1), (2, 3), (4, 5), (6, 7), (8, 9)]

The *step* defaults to *n*, but can be more to skip elements, or less for a sliding window with overlap.

.. code-block:: hy

    => (list (partition (range 10) 2 3))
    [(0, 1), (3, 4), (6, 7)]
    => (list (partition (range 5) 2 1))
    [(0, 1), (1, 2), (2, 3), (3, 4)]

The remainder, if any, is not included unless a *fillvalue* is specified.

.. code-block:: hy

    => (list (partition (range 10) 3))
    [(0, 1, 2), (3, 4, 5), (6, 7, 8)]
    => (list (partition (range 10) 3 :fillvalue "x"))
    [(0, 1, 2), (3, 4, 5), (6, 7, 8), (9, 'x', 'x')]

.. _pos?-fn:

pos?
----

Usage: ``(pos? x)``

Returns ``True`` if *x* is greater than zero. Raises ``TypeError``
if ``(not (numeric? x))``.

.. code-block:: hy

   => (pos? 3)
   True

   => (pos? -2)
   False

   => (pos? 0)
   False


.. _second-fn:

second
------

Usage: ``(second coll)``

Returns the second member of *coll*. Equivalent to ``(get coll 1)``.

.. code-block:: hy

   => (second [0 1 2])
   1


.. _some-fn:

some
----

.. versionadded:: 0.10.0

Usage: ``(some pred coll)``

Returns the first logically-true value of ``(pred x)`` for any ``x`` in
*coll*, otherwise ``None``. Return ``None`` if *coll* is empty.

.. code-block:: hy

   => (some even? [2 4 6])
   True

   => (none? (some even? [1 3 5]))
   True

   => (none? (some identity [0 "" []]))
   True

   => (some identity [0 "non-empty-string" []])
   'non-empty-string'

   => (none? (some even? []))
   True


.. _list?-fn:

list?
-----

Usage: ``(list? x)``

Returns ``True`` if *x* is a list.

.. code-block:: hy

   => (list? '(inc 41))
   True

   => (list? '42)
   False


.. _string?-fn:

string?
-------

Usage: ``(string? x)``

Returns ``True`` if *x* is a string.

.. code-block:: hy

   => (string? "foo")
   True

   => (string? -2)
   False

.. _symbol?-fn:

symbol?
-------

Usage: ``(symbol? x)``

Returns ``True`` if *x* is a symbol.

.. code-block:: hy

   => (symbol? 'foo)
   True

   => (symbol? '[a b c])
   False

.. _zero?-fn:

zero?
-----

Usage: ``(zero? x)``

Returns ``True`` if *x* is zero.

.. code-block:: hy

   => (zero? 3)
   False

   => (zero? -2)
   False

   => (zero? 0)
   True


Sequence Functions
==================

Sequence functions can either create or operate on a potentially
infinite sequence without requiring the sequence be fully realized in
a list or similar container. They do this by returning a Python
iterator.

We can use the canonical infinite Fibonacci number generator
as an example of how to use some of these functions.

.. code-block:: hy

   (defn fib []
     (setv a 0)
     (setv b 1)
     (while True
       (yield a)
       (setv (, a b) (, b (+ a b)))))


Note the ``(while True ...)`` loop. If we run this in the REPL,

.. code-block:: hy

   => (fib)
   <generator object fib at 0x101e642d0>


Calling the function only returns an iterator, but does no
work until we consume it. Trying something like this is not recommend as
the infinite loop will run until it consumes all available RAM, or
in this case until I killed it.

.. code-block:: hy

   => (list (fib))
   [1]    91474 killed     hy


To get the first 10 Fibonacci numbers, use :ref:`take-fn`. Note that
:ref:`take-fn` also returns a generator, so I create a list from it.

.. code-block:: hy

   => (list (take 10 (fib)))
   [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]


To get the Fibonacci number at index 9, (starting from 0):

.. code-block:: hy

   => (nth (fib) 9)
   34


.. _cycle-fn:

cycle
-----

Usage: ``(cycle coll)``

Returns an infinite iterator of the members of coll.

.. code-block:: clj

   => (list (take 7 (cycle [1 2 3])))
   [1, 2, 3, 1, 2, 3, 1]

   => (list (take 2 (cycle [1 2 3])))
   [1, 2]


.. _distinct-fn:

distinct
--------

Usage: ``(distinct coll)``

Returns an iterator containing only the unique members in *coll*.

.. code-block:: hy

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

Returns an iterator, skipping the first *n* members of *coll*.
Raises ``ValueError`` if *n* is negative.

.. code-block:: hy

   => (list (drop 2 [1 2 3 4 5]))
   [3, 4, 5]

   => (list (drop 4 [1 2 3 4 5]))
   [5]

   => (list (drop 0 [1 2 3 4 5]))
   [1, 2, 3, 4, 5]

   => (list (drop 6 [1 2 3 4 5]))
   []


.. _drop-last-fn:

drop-last
---------

Usage: ``(drop-last n coll)``

Returns an iterator of all but the last *n* items in *coll*. Raises
``ValueError`` if *n* is negative.

.. code-block:: hy

   => (list (drop-last 5 (range 10 20)))
   [10, 11, 12, 13, 14]

   => (list (drop-last 0 (range 5)))
   [0, 1, 2, 3, 4]

   => (list (drop-last 100 (range 100)))
   []

   => (list (take 5 (drop-last 100 (count 10))))
   [10, 11, 12, 13, 14]


.. _drop-while-fn:

drop-while
-----------

Usage: ``(drop-while pred coll)``

Returns an iterator, skipping members of *coll* until *pred* is ``False``.

.. code-block:: hy

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

Returns an iterator for all items in *coll* that pass the predicate *pred*.

See also :ref:`remove-fn`.

.. code-block:: hy

   => (list (filter pos? [1 2 3 -4 5 -7]))
   [1, 2, 3, 5]

   => (list (filter even? [1 2 3 -4 5 -7]))
   [2, -4]

.. _flatten-fn:

flatten
-------

.. versionadded:: 0.9.12

Usage: ``(flatten coll)``

Returns a single list of all the items in *coll*, by flattening all
contained lists and/or tuples.

.. code-block:: hy

   => (flatten [1 2 [3 4] 5])
   [1, 2, 3, 4, 5]

   => (flatten ["foo" (, 1 2) [1 [2 3] 4] "bar"])
   ['foo', 1, 2, 1, 2, 3, 4, 'bar']


.. _iterate-fn:

iterate
-------

Usage: ``(iterate fn x)``

Returns an iterator of *x*, *fn(x)*, *fn(fn(x))*, etc.

.. code-block:: hy

   => (list (take 5 (iterate inc 5)))
   [5, 6, 7, 8, 9]

   => (list (take 5 (iterate (fn [x] (* x x)) 5)))
   [5, 25, 625, 390625, 152587890625]


.. _read-fn:

read
----

Usage: ``(read &optional [from-file eof])``

Reads the next Hy expression from *from-file* (defaulting to ``sys.stdin``), and
can take a single byte as EOF (defaults to an empty string). Raises ``EOFError``
if *from-file* ends before a complete expression can be parsed.

.. code-block:: hy

    => (read)
    (+ 2 2)
    HyExpression([
      HySymbol('+'),
      HyInteger(2),
      HyInteger(2)])
    => (eval (read))
    (+ 2 2)
    4
    => (import io)
    => (setv buffer (io.StringIO "(+ 2 2)\n(- 2 1)"))
    => (eval (read :from-file buffer))
    4
    => (eval (read :from-file buffer))
    1

    => (with [f (open "example.hy" "w")]
    ...  (.write f "(print 'hello)\n(print \"hyfriends!\")"))
    35
    => (with [f (open "example.hy")]
    ...  (try (while True
    ...         (setv exp (read f))
    ...         (print "OHY" exp)
    ...         (eval exp))
    ...       (except [e EOFError]
    ...         (print "EOF!"))))
    OHY HyExpression([
      HySymbol('print'),
      HyExpression([
        HySymbol('quote'),
        HySymbol('hello')])])
    hello
    OHY HyExpression([
      HySymbol('print'),
      HyString('hyfriends!')])
    hyfriends!
    EOF!

read-str
--------

Usage: ``(read-str "string")``

This is essentially a wrapper around `read` which reads expressions from a
string:

.. code-block:: hy

    => (read-str "(print 1)")
    HyExpression([
      HySymbol('print'),
      HyInteger(1)])
    => (eval (read-str "(print 1)"))
    1

.. _remove-fn:

remove
------

Usage: ``(remove pred coll)``

Returns an iterator from *coll* with elements that pass the
predicate, *pred*, removed.

See also :ref:`filter-fn`.

.. code-block:: hy

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

Returns an iterator (infinite) of ``x``.

.. code-block:: hy

   => (list (take 6 (repeat "s")))
   [u's', u's', u's', u's', u's', u's']


.. _repeatedly-fn:

repeatedly
----------

Usage: ``(repeatedly fn)``

Returns an iterator by calling *fn* repeatedly.

.. code-block:: hy

   => (import [random [randint]])

   => (list (take 5 (repeatedly (fn [] (randint 0 10)))))
   [6, 2, 0, 6, 7]


.. _take-fn:

take
----

Usage: ``(take n coll)``

Returns an iterator containing the first *n* members of *coll*.
Raises ``ValueError`` if *n* is negative.

.. code-block:: hy

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

Returns an iterator containing every *n*-th member of *coll*.

.. code-block:: hy

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

Returns an iterator from *coll* as long as *pred* returns ``True``.

.. code-block:: hy

   => (list (take-while pos? [ 1 2 3 -4 5]))
   [1, 2, 3]

   => (list (take-while neg? [ -4 -3 1 2 5]))
   [-4, -3]

   => (list (take-while neg? [ 1 2 3 -4 5]))
   []

.. _unmangle-fn:

unmangle
--------

Usage: ``(unmangle x)``

Stringify the input and return a string that would :ref:`mangle <mangling>` to
it. Note that this isn't a one-to-one operation, and nor is ``mangle``, so
``mangle`` and ``unmangle`` don't always round-trip.

.. code-block:: hylang

    => (unmangle "foo_bar")
    'foo-bar'

Included itertools
==================

count cycle repeat accumulate chain compress drop-while remove group-by islice *map take-while tee zip-longest product permutations combinations multicombinations
---------

All of Python's `itertools <https://docs.python.org/3/library/itertools.html>`_
are available. Some of their names have been changed:

  - ``starmap`` has been changed to ``*map``

  - ``combinations_with_replacement`` has been changed to ``multicombinations``

  - ``groupby`` has been changed to ``group-by``

  - ``takewhile`` has been changed to ``take-while``

  - ``dropwhile`` has been changed to ``drop-while``

  - ``filterfalse`` has been changed to ``remove``
