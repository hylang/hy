=================
Hy (the language)
=================

.. warning::
    This is incomplete; please consider contributing to the documentation
    effort.


Theory of Hy
============

Hy maintains, over everything else, 100% compatibility in both directions
with Python itself. All Hy code follows a few simple rules. Memorize
this, as it's going to come in handy.

These rules help ensure that Hy code is idiomatic and interfaceable in both
languages.


  * Symbols in earmufs will be translated to the upper-cased version of that
    string. For example, ``foo`` will become ``FOO``.

  * UTF-8 entities will be encoded using
    `punycode <http://en.wikipedia.org/wiki/Punycode>`_ and prefixed with
    ``hy_``. For instance, ``⚘`` will become ``hy_w7h``, ``♥`` will become
    ``hy_g6h``, and ``i♥u`` will become ``hy_iu_t0x``.

  * Symbols that contain dashes will have them replaced with underscores. For
    example, ``render-template`` will become ``render_template``. This means
    that symbols with dashes will shadow their underscore equivalents, and vice
    versa.


Built-Ins
=========

Hy features a number of special forms that are used to help generate
correct Python AST. The following are "special" forms, which may have
behavior that's slightly unexpected in some situations.

.
-

.. versionadded:: 0.10.0

``.`` is used to perform attribute access on objects. It uses a small DSL
to allow quick access to attributes and items in a nested data structure.

For instance,

.. code-block:: clj

    (. foo bar baz [(+ 1 2)] frob)

Compiles down to:

.. code-block:: python

     foo.bar.baz[1 + 2].frob

``.`` compiles its first argument (in the example, *foo*) as the object on
which to do the attribute dereference. It uses bare symbols as attributes
to access (in the example, *bar*, *baz*, *frob*), and compiles the contents
of lists (in the example, ``[(+ 1 2)]``) for indexation. Other arguments
throw a compilation error.

Access to unknown attributes throws an :exc:`AttributeError`. Access to
unknown keys throws an :exc:`IndexError` (on lists and tuples) or a
:exc:`KeyError` (on dictionaries).

->
--

``->`` (or the *threading macro*) is used to avoid nesting of expressions. The
threading macro inserts each expression into the next expression's first argument
place. The following code demonstrates this:

.. code-block:: clj

    => (defn output [a b] (print a b))
    => (-> (+ 4 6) (output 5))
    10 5


->>
---

``->>`` (or the *threading tail macro*) is similar to the *threading macro*, but
instead of inserting each expression into the next expression's first argument,
it appends it as the last argument. The following code demonstrates this:

.. code-block:: clj

    => (defn output [a b] (print a b))
    => (->> (+ 4 6) (output 5))
    5 10


apply
-----

``apply`` is used to apply an optional list of arguments and an optional
dictionary of kwargs to a function.

Usage: ``(apply fn-name [args] [kwargs])``

Examples:

.. code-block:: clj

    (defn thunk []
      "hy there")

    (apply thunk)
    ;=> "hy there"

    (defn total-purchase [price amount &optional [fees 1.05] [vat 1.1]]
      (* price amount fees vat))

    (apply total-purchase [10 15])
    ;=> 173.25

    (apply total-purchase [10 15] {"vat" 1.05})
    ;=> 165.375

    (apply total-purchase [] {"price" 10 "amount" 15 "vat" 1.05})
    ;=> 165.375


and
---

``and`` is used in logical expressions. It takes at least two parameters. If
all parameters evaluate to ``True``, the last parameter is returned. In any
other case, the first false value will be returned. Example usage:

.. code-block:: clj

    => (and True False)
    False

    => (and True True)
    True

    => (and True 1)
    1

    => (and True [] False True)
    []

.. note::

    ``and`` short-circuits and stops evaluating parameters as soon as the first
    false is encountered.

.. code-block:: clj

    => (and False (print "hello"))
    False


assert
------

``assert`` is used to verify conditions while the program is
running. If the condition is not met, an :exc:`AssertionError` is
raised. ``assert`` may take one or two parameters.  The first
parameter is the condition to check, and it should evaluate to either
``True`` or ``False``. The second parameter, optional, is a label for
the assert, and is the string that will be raised with the
:exc:`AssertionError`. For example:

.. code-block:: clj

  (assert (= variable expected-value))

  (assert False)
  ; AssertionError

  (assert (= 1 2) "one should equal two")
  ; AssertionError: one should equal two


assoc
-----

``assoc`` is used to associate a key with a value in a dictionary or to set an
index of a list to a value. It takes at least three parameters: the *data
structure* to be modified, a *key* or *index*, and a *value*. If more than
three parameters are used, it will associate in pairs.

Examples of usage:

.. code-block:: clj

  =>(let [[collection {}]]
  ... (assoc collection "Dog" "Bark")
  ... (print collection))
  {u'Dog': u'Bark'}

  =>(let [[collection {}]]
  ... (assoc collection "Dog" "Bark" "Cat" "Meow")
  ... (print collection))
  {u'Cat': u'Meow', u'Dog': u'Bark'}

  =>(let [[collection [1 2 3 4]]]
  ... (assoc collection 2 None)
  ... (print collection))
  [1, 2, None, 4]

.. note:: ``assoc`` modifies the datastructure in place and returns ``None``.


break
-----

``break`` is used to break out from a loop. It terminates the loop immediately.
The following example has an infinite ``while`` loop that is terminated as soon
as the user enters *k*.

.. code-block:: clj

    (while True (if (= "k" (raw-input "? "))
                  (break)
                  (print "Try again")))


cond
----

``cond`` can be used to build nested ``if`` statements. The following example
shows the relationship between the macro and its expansion:

.. code-block:: clj

    (cond [condition-1 result-1]
          [condition-2 result-2])

    (if condition-1 result-1
      (if condition-2 result-2))

As shown below, only the first matching result block is executed.

.. code-block:: clj

    => (defn check-value [value]
    ...  (cond [(< value 5) (print "value is smaller than 5")]
    ...        [(= value 5) (print "value is equal to 5")]
    ...        [(> value 5) (print "value is greater than 5")]
    ...	       [True (print "value is something that it should not be")]))

    => (check-value 6)
    value is greater than 5


continue
--------

``continue`` returns execution to the start of a loop. In the following example,
``(side-effect1)`` is called for each iteration. ``(side-effect2)``, however,
is only called on every other value in the list.

.. code-block:: clj

    ;; assuming that (side-effect1) and (side-effect2) are functions and
    ;; collection is a list of numerical values

    (for [x collection]
      (do
        (side-effect1 x)
        (if (% x 2)
          (continue))
        (side-effect2 x)))


dict-comp
---------

``dict-comp`` is used to create dictionaries. It takes three or four parameters.
The first two parameters are for controlling the return value (key-value pair)
while the third is used to select items from a sequence. The fourth and optional
parameter can be used to filter out some of the items in the sequence based on a
conditional expression.

.. code-block:: hy

    => (dict-comp x (* x 2) [x (range 10)] (odd? x))
    {1: 2, 3: 6, 9: 18, 5: 10, 7: 14}


do / progn
----------

``do`` and `progn` are used to evaluate each of their arguments and return the
last one. Return values from every other than the last argument are discarded.
It can be used in ``lambda`` or ``list-comp`` to perform more complex logic as
shown in one of the following examples.

Some example usage:

.. code-block:: clj

    => (if true
    ...  (do (print "Side effects rock!")
    ...      (print "Yeah, really!")))
    Side effects rock!
    Yeah, really!

    ;; assuming that (side-effect) is a function that we want to call for each
    ;; and every value in the list, but whose return value we do not care about
    => (list-comp (do (side-effect x)
    ...               (if (< x 5) (* 2 x)
    ...                   (* 4 x)))
    ...           (x (range 10)))
    [0, 2, 4, 6, 8, 20, 24, 28, 32, 36]

``do`` can accept any number of arguments, from 1 to n.


def / setv
----------

``def`` and ``setv`` are used to bind a value, object, or function to a symbol.
For example:

.. code-block:: clj

    => (def names ["Alice" "Bob" "Charlie"])
    => (print names)
    [u'Alice', u'Bob', u'Charlie']

    => (setv counter (fn [collection item] (.count collection item)))
    => (counter [1 2 3 4 5 2 3] 2)
    2


defclass
--------

New classes are declared with ``defclass``. It can takes two optional parameters:
a vector defining a possible super classes and another vector containing
attributes of the new class as two item vectors.

.. code-block:: clj

    (defclass class-name [super-class-1 super-class-2]
      [[attribute value]])

Both values and functions can be bound on the new class as shown by the example
below:

.. code-block:: clj

    => (defclass Cat []
    ...  [[age None]
    ...   [colour "white"]
    ...   [speak (fn [self] (print "Meow"))]])

    => (def spot (Cat))
    => (setv spot.colour "Black")
    'Black'
    => (.speak spot)
    Meow


.. _defn:

defn / defun
------------

``defn`` and ``defun`` macros are used to define functions. They take three
parameters: the *name* of the function to define, a vector of *parameters*,
and the *body* of the function:

.. code-block:: clj

    (defn name [params] body)

Parameters may have the following keywords in front of them:

&optional
    Parameter is optional. The parameter can be given as a two item list, where
    the first element is parameter name and the second is the default value. The
    parameter can be also given as a single item, in which case the default
    value is ``None``.

    .. code-block:: clj

        => (defn total-value [value &optional [value-added-tax 10]]
        ...  (+ (/ (* value value-added-tax) 100) value))

	=> (total-value 100)
        110.0

    	=> (total-value 100 1)
	101.0

&key


&kwargs
    Parameter will contain 0 or more keyword arguments.

    The following code examples defines a function that will print all keyword
    arguments and their values.

    .. code-block:: clj

        => (defn print-parameters [&kwargs kwargs]
        ...    (for [(, k v) (.items kwargs)] (print k v)))

        => (apply print-parameters [] {"parameter-1" 1 "parameter-2" 2})
        parameter-2 2
        parameter-1 1

&rest
    Parameter will contain 0 or more positional arguments. No other positional
    arguments may be specified after this one.

    The following code example defines a function that can be given 0 to n
    numerical parameters. It then sums every odd number and subtracts
    every even number.

    .. code-block:: clj

        => (defn zig-zag-sum [&rest numbers]
             (let [[odd-numbers (list-comp x [x numbers] (odd? x))]
	           [even-numbers (list-comp x [x numbers] (even? x))]]
               (- (sum odd-numbers) (sum even-numbers))))

        => (zig-zag-sum)
        0
        => (zig-zag-sum 3 9 4)
        8
        => (zig-zag-sum 1 2 3 4 5 6)
        -3

.. _defn-alias / defun-alias:

defn-alias / defun-alias
------------------------

.. versionadded:: 0.10.0

The ``defn-alias`` and ``defun-alias`` macros are much like `defn`_,
with the distinction that instead of defining a function with a single
name, these can also define aliases. Other than taking a list of
symbols for function names as the first parameter, ``defn-alias`` and
``defun-alias`` are no different from ``defn`` and ``defun``.

.. code-block:: clj

  => (defn-alias [main-name alias] []
  ...  (print "Hello!"))
  => (main-name)
  "Hello!"
  => (alias)
  "Hello!"


defmain
-------

.. versionadded:: 0.10.1

The ``defmain`` macro defines a main function that is immediately called
with ``sys.argv`` as arguments if and only if this file is being executed
as a script.  In other words, this:

.. code-block:: clj

   (defmain [&rest args]
     (do-something-with args))

is the equivalent of::

   def main(*args):
       do_something_with(args)
       return 0

   if __name__ == "__main__":
       import sys
       retval = main(*sys.arg)

       if isinstance(retval, int):
           sys.exit(retval)

Note that as you can see above, if you return an integer from this
function, this will be used as the exit status for your script.
(Python defaults to exit status 0 otherwise, which means everything's
okay!)

(Since ``(sys.exit 0)`` is not run explicitly in the case of a non-integer
return from ``defmain``, it's a good idea to put ``(defmain)`` as the last
piece of code in your file.)


.. _defmacro:

defmacro
--------

``defmacro`` is used to define macros. The general format is
``(defmacro name [parameters] expr)``.

The following example defines a macro that can be used to swap order of elements
in code, allowing the user to write code in infix notation, where operator is in
between the operands.

.. code-block:: clj

  => (defmacro infix [code]
  ...  (quasiquote (
  ...    (unquote (get code 1))
  ...    (unquote (get code 0))
  ...    (unquote (get code 2)))))

  => (infix (1 + 1))
  2

.. _defmacro-alias:

defmacro-alias
--------------

``defmacro-alias`` is used to define macros with multiple names
(aliases). The general format is ``(defmacro-alias [names] [parameters]
expr)``. It creates multiple macros with the same parameter list and
body, under the specified list of names.

The following example defines two macros, both of which allow the user
to write code in infix notation.

.. code-block:: clj

  => (defmacro-alias [infix infi] [code]
  ...  (quasiquote (
  ...    (unquote (get code 1))
  ...    (unquote (get code 0))
  ...    (unquote (get code 2)))))

  => (infix (1 + 1))
  2
  => (infi (1 + 1))
  2

.. _defmacro/g!:

defmacro/g!
------------

.. versionadded:: 0.9.12

``defmacro/g!`` is a special version of ``defmacro`` that is used to
automatically generate :ref:`gensym` for any symbol that starts with
``g!``.

For example, ``g!a`` would become ``(gensym "a")``.

.. seealso::

   Section :ref:`using-gensym`

defreader
---------

.. versionadded:: 0.9.12

``defreader`` defines a reader macro, enabling you to restructure or
modify syntax.

.. code-block:: clj

    => (defreader ^ [expr] (print expr))
    => #^(1 2 3 4)
    (1 2 3 4)
    => #^"Hello"
    "Hello"

.. seealso::

    Section :ref:`Reader Macros <reader-macros>`

del
---

.. versionadded:: 0.9.12

``del`` removes an object from the current namespace.

.. code-block:: clj

  => (setv foo 42)
  => (del foo)
  => foo
  Traceback (most recent call last):
    File "<console>", line 1, in <module>
  NameError: name 'foo' is not defined

``del`` can also remove objects from mappings, lists, and more.

.. code-block:: clj

  => (setv test (list (range 10)))
  => test
  [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
  => (del (slice test 2 4)) ;; remove items from 2 to 4 excluded
  => test
  [0, 1, 4, 5, 6, 7, 8, 9]
  => (setv dic {"foo" "bar"})
  => dic
  {"foo": "bar"}
  => (del (get dic "foo"))
  => dic
  {}

doto
----

.. versionadded:: 0.10.1

``doto`` is used to simplify a sequence of method calls to an object.

.. code-block:: clj

  => (doto [] (.append 1) (.append 2) .reverse)
  [2 1]

.. code-block:: clj

  => (setv collection [])
  => (.append collection 1)
  => (.append collection 2)
  => (.reverse collection)
  => collection
  [2 1]

eval
----

``eval`` evaluates a quoted expression and returns the value.

.. code-block:: clj

   => (eval '(print "Hello World"))
   "Hello World"

eval-and-compile
----------------


eval-when-compile
-----------------


first / car
-----------

``first`` and ``car`` are macros for accessing the first element of a collection:

.. code-block:: clj

    => (first (range 10))
    0


for
---

``for`` is used to call a function for each element in a list or vector.
The results of each call are discarded and the ``for`` expression returns
``None`` instead. The example code iterates over *collection* and for each
*element* in *collection* calls the ``side-effect`` function with *element*
as its argument:

.. code-block:: clj

    ;; assuming that (side-effect) is a function that takes a single parameter
    (for [element collection] (side-effect element))

    ;; for can have an optional else block
    (for [element collection] (side-effect element)
         (else (side-effect-2)))

The optional ``else`` block is only executed if the ``for`` loop terminates
normally. If the execution is halted with ``break``, the ``else`` block does
not execute.

.. code-block:: clj

    => (for [element [1 2 3]] (if (< element 3)
    ...                             (print element)
    ...                             (break))
    ...    (else (print "loop finished")))
    1
    2

    => (for [element [1 2 3]] (if (< element 4)
    ...                             (print element)
    ...                             (break))
    ...    (else (print "loop finished")))
    1
    2
    3
    loop finished


genexpr
-------

``genexpr`` is used to create generator expressions. It takes two or three
parameters. The first parameter is the expression controlling the return value,
while the second is used to select items from a list. The third and optional
parameter can be used to filter out some of the items in the list based on a
conditional expression. ``genexpr`` is similar to ``list-comp``, except it
returns an iterable that evaluates values one by one instead of evaluating them
immediately.

.. code-block:: hy

    => (def collection (range 10))
    => (def filtered (genexpr x [x collection] (even? x)))
    => (list filtered)
    [0, 2, 4, 6, 8]


.. _gensym:

gensym
------

.. versionadded:: 0.9.12

``gensym`` is used to generate a unique symbol that allows macros to be
written without accidental variable name clashes.

.. code-block:: clj

   => (gensym)
   u':G_1235'

   => (gensym "x")
   u':x_1236'

.. seealso::

   Section :ref:`using-gensym`

get
---

``get`` is used to access single elements in lists and dictionaries. ``get``
takes two parameters: the *data structure* and the *index* or *key* of the
item. It will then return the corresponding value from the dictionary or the
list. Example usage:

.. code-block:: clj

   => (let [[animals {"dog" "bark" "cat" "meow"}]
   ...      [numbers ["zero" "one" "two" "three"]]]
   ...  (print (get animals "dog"))
   ...  (print (get numbers 2)))
   bark
   two

.. note:: ``get`` raises a KeyError if a dictionary is queried for a
          non-existing key.

.. note:: ``get`` raises an IndexError if a list or a tuple is queried for an
          index that is out of bounds.


global
------

``global`` can be used to mark a symbol as global. This allows the programmer to
assign a value to a global symbol. Reading a global symbol does not require the
``global`` keyword -- only assigning it does.

The following example shows how the global symbol ``a`` is assigned a value in a
function and is later on printed in another function. Without the ``global``
keyword, the second function would have thrown a ``NameError``.

.. code-block:: clj

    (defn set-a [value]
      (global a)
      (setv a value))

    (defn print-a []
      (print a))

    (set-a 5)
    (print-a)

if / if-not
-----------

.. versionadded:: 0.10.0
   if-not

``if`` is used to conditionally select code to be executed. It has to contain a
condition block and the block to be executed if the condition block evaluates
to ``True``. Optionally, it may contain a final block that is executed in case
the evaluation of the condition is ``False``.

``if-not`` is similar, but the second block will be executed when the condition
fails while the third and final block is executed when the test succeeds -- the
opposite order of ``if``.

Example usage:

.. code-block:: clj

    (if (money-left? account)
      (print "let's go shopping")
      (print "let's go and work"))

    (if-not (money-left? account)
      (print "let's go and work")
      (print "let's go shopping"))

Python truthiness is respected. ``None``, ``False``, zero of any numeric type,
an empty sequence, and an empty dictionary are considered ``False``; everything
else is considered ``True``.


lisp-if / lif and lisp-if-not / lif-not
---------------------------------------

.. versionadded:: 0.10.0

.. versionadded:: 0.10.2
   lisp-if-not / lif-not

For those that prefer a more Lispy ``if`` clause, we have ``lisp-if``, or
``lif``. This *only* considers ``None`` / ``nil`` to be false! All other
"false-ish" Python values are considered true. Conversely, we have
``lisp-if-not`` and ``lif-not`` in parallel to ``if`` and ``if-not`` which
reverses the comparison.


.. code-block:: clj

    => (lisp-if True "true" "false")
    "true"
    => (lisp-if False "true" "false")
    "true"
    => (lisp-if 0 "true" "false")
    "true"
    => (lisp-if nil "true" "false")
    "false"
    => (lisp-if None "true" "false")
    "false"
    => (lisp-if-not nil "true" "false")
    "true"
    => (lisp-if-not None "true" "false")
    "true"
    => (lisp-if-not False "true" "false")
    "false"

    ; Equivalent but shorter
    => (lif True "true" "false")
    "true"
    => (lif nil "true" "false")
    "false"
    => (lif-not None "true" "false")
    "true"


import
------

``import`` is used to import modules, like in Python. There are several ways
that ``import`` can be used.

.. code-block:: clj

    ;; Imports each of these modules
    ;;
    ;; Python:
    ;; import sys
    ;; import os.path
    (import sys os.path)

    ;; Import from a module
    ;;
    ;; Python: from os.path import exists, isdir, isfile
    (import [os.path [exists isdir isfile]])

    ;; Import with an alias
    ;;
    ;; Python: import sys as systest
    (import [sys :as systest])

    ;; You can list as many imports as you like of different types.
    (import [tests.resources [kwtest function-with-a-dash]]
            [os.path [exists isdir isfile]]
            [sys :as systest])

    ;; Import all module functions into current namespace
    (import [sys [*]])


lambda / fn
-----------

``lambda`` and ``fn`` can be used to define an anonymous function. The parameters are
similar to ``defn``: the first parameter is vector of parameters and the rest is the
body of the function. ``lambda`` returns a new function. In the following example, an
anonymous function is defined and passed to another function for filtering output.

.. code-block:: clj

    => (def people [{:name "Alice" :age 20}
    ...             {:name "Bob" :age 25}
    ...             {:name "Charlie" :age 50}
    ...             {:name "Dave" :age 5}])

    => (defn display-people [people filter]
    ...  (for [person people] (if (filter person) (print (:name person)))))

    => (display-people people (fn [person] (< (:age person) 25)))
    Alice
    Dave

Just as in normal function definitions, if the first element of the
body is a string, it serves as a docstring. This is useful for giving
class methods docstrings.

.. code-block:: clj

    => (setv times-three
    ...   (fn [x]
    ...    "Multiplies input by three and returns the result."
    ...    (* x 3)))

This can be confirmed via Python's built-in ``help`` function::

    => (help times-three)
    Help on function times_three:

    times_three(x)
    Multiplies input by three and returns result
    (END)
	
last
-----------

.. versionadded:: 0.10.2

``last`` can be used for accessing the last element of a collection:

.. code-block:: clj

    => (last [2 4 6])
    6
	

let
---

``let`` is used to create lexically scoped variables. They are created at the
beginning of the ``let`` form and cease to exist after the form. The following
example showcases this behaviour:

.. code-block:: clj

    => (let [[x 5]] (print x)
    ...  (let [[x 6]] (print x))
    ...  (print x))
    5
    6
    5

The ``let`` macro takes two parameters: a vector defining *variables* and the
*body* which gets executed. *variables* is a vector where each element is either
a single variable or a vector defining a variable value pair. In the case of a
single variable, it is assigned value ``None``; otherwise, the supplied value is
used.

.. code-block:: clj

    => (let [x [y 5]] (print x y))
    None 5


list-comp
---------

``list-comp`` performs list comprehensions. It takes two or three parameters.
The first parameter is the expression controlling the return value, while
the second is used to select items from a list. The third and optional
parameter can be used to filter out some of the items in the list based on a
conditional expression. Some examples:

.. code-block:: clj

    => (def collection (range 10))
    => (list-comp x [x collection])
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

    => (list-comp (* x 2) [x collection])
    [0, 2, 4, 6, 8, 10, 12, 14, 16, 18]

    => (list-comp (* x 2) [x collection] (< x 5))
    [0, 2, 4, 6, 8]


not
---

``not`` is used in logical expressions. It takes a single parameter and
returns a reversed truth value. If ``True`` is given as a parameter, ``False``
will be returned, and vice-versa. Example usage:

.. code-block:: clj

    => (not True)
    False

    => (not False)
    True

    => (not None)
    True


or
--

``or`` is used in logical expressions. It takes at least two parameters. It
will return the first non-false parameter. If no such value exists, the last
parameter will be returned.

.. code-block:: clj

    => (or True False)
    True

    => (and False False)
    False

    => (and False 1 True False)
    1

.. note:: ``or`` short-circuits and stops evaluating parameters as soon as the
          first true value is encountered.

.. code-block:: clj

    => (or True (print "hello"))
    True


print
-----

``print`` is used to output on screen. Example usage:

.. code-block:: clj

    (print "Hello world!")

.. note:: ``print`` always returns ``None``.


quasiquote
----------

``quasiquote`` allows you to quote a form, but also selectively evaluate
expressions. Expressions inside a ``quasiquote`` can be selectively evaluated
using ``unquote`` (``~``). The evaluated form can also be spliced using
``unquote-splice`` (``~@``). Quasiquote can be also written using the backquote
(`````) symbol.

.. code-block:: clj

    ;; let `qux' be a variable with value (bar baz)
    `(foo ~qux)
    ; equivalent to '(foo (bar baz))
    `(foo ~@qux)
    ; equivalent to '(foo bar baz)


quote
-----

``quote`` returns the form passed to it without evaluating it. ``quote`` can
alternatively be written using the apostrophe (``'``) symbol.

.. code-block:: clj

    => (setv x '(print "Hello World"))
    ; variable x is set to expression & not evaluated
    => x
    (u'print' u'Hello World')
    => (eval x)
    Hello World


require
-------

``require`` is used to import macros from a given module. It takes at least one
parameter specifying the module which macros should be imported. Multiple
modules can be imported with a single ``require``.

The following example will import macros from ``module-1`` and ``module-2``:

.. code-block:: clj

    (require module-1 module-2)


rest / cdr
----------

``rest`` and ``cdr`` return the collection passed as an argument without the
first element:

.. code-block:: clj

    => (rest (range 10))
    [1, 2, 3, 4, 5, 6, 7, 8, 9]


set-comp
--------

``set-comp`` is used to create sets. It takes two or three parameters.
The first parameter is for controlling the return value, while the second is
used to select items from a sequence. The third and optional parameter can be
used to filter out some of the items in the sequence based on a conditional
expression.

.. code-block:: hy

    => (setv data [1 2 3 4 5 2 3 4 5 3 4 5])
    => (set-comp x [x data] (odd? x))
    {1, 3, 5}


slice
-----

``slice`` can be used to take a subset of a list and create a new list from it.
The form takes at least one parameter specifying the list to slice. Two
optional parameters can be used to give the start and end position of the
subset. If they are not supplied, the default value of ``None`` will be used
instead. The third optional parameter is used to control step between the elements.

``slice`` follows the same rules as its Python counterpart. Negative indices are
counted starting from the end of the list. Some example usage:

.. code-block:: clj

    => (def collection (range 10))

    => (slice collection)
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

    => (slice collection 5)
    [5, 6, 7, 8, 9]

    => (slice collection 2 8)
    [2, 3, 4, 5, 6, 7]

    => (slice collection 2 8 2)
    [2, 4, 6]

    => (slice collection -4 -2)
    [6, 7]


throw / raise
-------------

The ``throw`` or ``raise`` forms can be used to raise an ``Exception`` at
runtime. Example usage:

.. code-block:: clj

    (throw)
    ; re-rase the last exception

    (throw IOError)
    ; Throw an IOError

    (throw (IOError "foobar"))
    ; Throw an IOError("foobar")


``throw`` can accept a single argument (an ``Exception`` class or instance)
or no arguments to re-raise the last ``Exception``.


try
---

The ``try`` form is used to start a ``try`` / ``catch`` block. The form is
used as follows:

.. code-block:: clj

    (try
        (error-prone-function)
        (catch [e ZeroDivisionError] (print "Division by zero"))
        (else (print "no errors"))
        (finally (print "all done")))

``try`` must contain at least one ``catch`` block, and may optionally include
an ``else`` or ``finally`` block. If an error is raised with a matching catch
block during the execution of ``error-prone-function``, that ``catch`` block
will be executed. If no errors are raised, the ``else`` block is executed. The
``finally`` block will be executed last regardless of whether or not an error
was raised.


unless
------

The ``unless`` macro is a shorthand for writing an ``if`` statement that checks if
the given conditional is ``False``. The following shows the expansion of this macro.

.. code-block:: clj

    (unless conditional statement)

    (if conditional
      None
      (do statement))


unquote
-------

Within a quasiquoted form, ``unquote`` forces evaluation of a symbol. ``unquote``
is aliased to the tilde (``~``) symbol.

.. code-block:: clj

    (def name "Cuddles")
    (quasiquote (= name (unquote name)))
    ;=> (u'=' u'name' u'Cuddles')

    `(= name ~name)
    ;=> (u'=' u'name' u'Cuddles')


unquote-splice
--------------

``unquote-splice`` forces the evaluation of a symbol within a quasiquoted form,
much like ``unquote``. ``unquote-splice`` can only be used when the symbol
being unquoted contains an iterable value, as it "splices" that iterable into
the quasiquoted form. ``unquote-splice`` is aliased to the ``~@`` symbol.

.. code-block:: clj

    (def nums [1 2 3 4])
    (quasiquote (+ (unquote-splice nums)))
    ;=> (u'+' 1L 2L 3L 4L)

    `(+ ~@nums)
    ;=> (u'+' 1L 2L 3L 4L)


when
----

``when`` is similar to ``unless``, except it tests when the given conditional is
``True``. It is not possible to have an ``else`` block in a ``when`` macro. The
following shows the expansion of the macro.

.. code-block:: clj

    (when conditional statement)

    (if conditional (do statement))


while
-----

``while`` is used to execute one or more blocks as long as a condition is met.
The following example will output "Hello world!" to the screen indefinitely:

.. code-block:: clj

    (while True (print "Hello world!"))


with
----

``with`` is used to wrap the execution of a block within a context manager. The
context manager can then set up the local system and tear it down in a controlled
manner. The archetypical example of using ``with`` is when processing files.
``with`` can bind context to an argument or ignore it completely, as shown below:

.. code-block:: clj

    (with [[arg (expr)]] block)

    (with [[(expr)]] block)

    (with [[arg (expr)] [(expr)]] block)

The following example will open the ``NEWS`` file and print its content to the
screen. The file is automatically closed after it has been processed.

.. code-block:: clj

    (with [[f (open "NEWS")]] (print (.read f)))


with-decorator
--------------

``with-decorator`` is used to wrap a function with another. The function
performing the decoration should accept a single value: the function being
decorated, and return a new function. ``with-decorator`` takes a minimum
of two parameters: the function performing decoration and the function
being decorated. More than one decorator function can be applied; they
will be applied in order from outermost to innermost, ie. the first
decorator will be the outermost one, and so on. Decorators with arguments
are called just like a function call.

.. code-block:: clj

   (with-decorator decorator-fun
      (defn some-function [] ...)

   (with-decorator decorator1 decorator2 ...
      (defn some-function [] ...)

   (with-decorator (decorator arg) ..
      (defn some-function [] ...)


In the following example, ``inc-decorator`` is used to decorate the function
``addition`` with a function that takes two parameters and calls the
decorated function with values that are incremented by 1. When
the decorated ``addition`` is called with values 1 and 1, the end result
will be 4 (``1+1 + 1+1``).

.. code-block:: clj

    => (defn inc-decorator [func]
    ...  (fn [value-1 value-2] (func (+ value-1 1) (+ value-2 1))))
    => (defn inc2-decorator [func]
    ...  (fn [value-1 value-2] (func (+ value-1 2) (+ value-2 2))))

    => (with-decorator inc-decorator (defn addition [a b] (+ a b)))
    => (addition 1 1)
    4
    => (with-decorator inc2-decorator inc-decorator
    ...	 (defn addition [a b] (+ a b)))
    => (addition 1 1)
    8


.. _with-gensyms:

with-gensyms
-------------

.. versionadded:: 0.9.12

``with-gensym`` is used to generate a set of :ref:`gensym` for use in a macro.
The following code:

.. code-block:: hy

   (with-gensyms [a b c]
     ...)

expands to:

.. code-block:: hy

   (let [[a (gensym)
         [b (gensym)
         [c (gensym)]]
     ...)

.. seealso::

   Section :ref:`using-gensym`


yield
-----

``yield`` is used to create a generator object that returns one or more values.
The generator is iterable and therefore can be used in loops, list
comprehensions and other similar constructs.

The function ``random-numbers`` shows how generators can be used to generate
infinite series without consuming infinite amount of memory.

.. code-block:: clj

    => (defn multiply [bases coefficients]
    ...  (for [[(, base coefficient) (zip bases coefficients)]]
    ...   (yield (* base coefficient))))

    => (multiply (range 5) (range 5))
    <generator object multiply at 0x978d8ec>

    => (list-comp value [value (multiply (range 10) (range 10))])
    [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]

    => (import random)
    => (defn random-numbers [low high]
    ...  (while True (yield (.randint random low high))))
    => (list-comp x [x (take 15 (random-numbers 1 50))])])
    [7, 41, 6, 22, 32, 17, 5, 38, 18, 38, 17, 14, 23, 23, 19]


yield-from
----------

.. versionadded:: 0.9.13

**PYTHON 3.3 AND UP ONLY!**

``yield-from`` is used to call a subgenerator.  This is useful if you
want your coroutine to be able to delegate its processes to another
coroutine, say, if using something fancy like
`asyncio <http://docs.python.org/3.4/library/asyncio.html>`_.
