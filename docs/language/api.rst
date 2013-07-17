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
this, it's going to come in handy.

These rules help make sure code is idiomatic and interface-able in both
languages.


  * Symbols in earmufs will be translated to the uppercased version of that
    string. For example, `*foo*` will become `FOO`.

  * UTF-8 entities will be encoded using
    `punycode <http://en.wikipedia.org/wiki/Punycode>`_ and prefixed with
    `hy_`. For instance, `⚘` will become `hy_w7h`, and `♥` will become
    `hy_g6h`.

  * Symbols that contain dashes will have them replaced with underscores. For
    example, `render-template` will become `render_template`.


Builtins
========

Hy features a number special forms that are used to help generate
correct Python AST. The following are "special" forms, which may have
behavior that's slightly unexpected in some situations.

and
---

`and` form is used in logical expressions. It takes at least two parameters. If
all parameters evaluate to `True` the last parameter is returned. In any other
case the first false value will be returned. Examples of usage:

.. code-block:: clj

    => (and True False)
    False

    => (and True True)
    True

    => (and True 1)
    1

    => (and True [] False True)
    []

.. note:: `and` shortcuts and stops evaluating parameters as soon as the first
          false is encountered. However, in the current implementation of Hy
          statements are executed as soon as they are converted to expressions.
          The following two examples demonstrates the difference.

.. code-block:: clj

    => (and False (print "hello"))
    hello
    False

    => (defn side-effects [x] (print "I can has" x) x)
    => (and (side-effects false) (side-effects 42))
    I can has False
    False

assert
------

`assert` is used to verify conditions while the program is running. If the 
condition is not met, an `AssertionError` is raised. The example usage:

.. code-block:: clj

    (assert (= variable expected-value))

Assert takes a single parameter, a conditional that evaluates to either `True`
or `False`.

assoc
-----

`assoc` form is used to associate a key with a value in a dictionary or to set
an index of a list to a value. It takes three parameters: `datastructure` to be
modified, `key` or `index`  and `value`.

Examples of usage:

.. code-block:: clj

  =>(let [[collection ({})]]
  ... (assoc collection "Dog" "Bark")
  ... (print collection))
  {u'Dog': u'Bark'}

  =>(let [[collection [1 2 3 4]]]
  ... (assoc collection 2 None)
  ... (print collection))
  [1, 2, None, 4]

.. note:: `assoc` modifies the datastructure in place and returns `None`.

break
-----

`break` is used to break out from a loop. It terminates the loop immediately.

The following example has an infinite while loop that is terminated as soon as
the user enters `k`.

.. code-block:: clj

    (while True (if (= "k" (raw-input "? ")) 
                  (break) 
                  (print "Try again")))


continue
--------

`continue` returns execution to the start of a loop. In the following example,
function `(side-effect1)` is called for each iteration. `(side-effect2)` 
however is called only for every other value in the list.

.. code-block:: clj

    ;; assuming that (side-effect1) and (side-effect2) are functions and
    ;; collection is a list of numerical values

    (for (x collection) (do
      (side-effect1 x)
      (if (% x 2)
        (continue))
      (side-effect2 x)))

do / progn
----------

the `do` and `progn` forms are used to evaluate each of their arguments and
return the last one. Return values from every other than the last argument are
discarded. It can be used in `lambda` or `list-comp` to perform more complex
logic as show by one of the examples.

Some example usage:

.. code-block:: clj

    => (if true
    ...  (do (print "Side effects rock!")
    ...      (print "Yeah, really!")))
    Side effects rock!
    Yeah, really!

    ;; assuming that (side-effect) is a function that we want to call for each
    ;; and every value in the list, but which return values we do not care
    => (list-comp (do (side-effect x) 
    ...               (if (< x 5) (* 2 x) 
    ...                   (* 4 x))) 
    ...           (x (range 10)))
    [0, 2, 4, 6, 8, 20, 24, 28, 32, 36]

`do` can accept any number of arguments, from 1 to n.


def / setv
-----------------


defclass
--------


defmacro
--------


eval
----


eval-and-compile
----------------


eval-when-compile
-----------------


foreach
-------


get
---

`get` form is used to access single elements in lists and dictionaries. `get`
takes two parameters, the `datastructure` and the `index` or `key` of the item.
It will then return the corresponding value from the dictionary or the list. 
Example usages:

.. code-block:: clj

   => (let [[animals {"dog" "bark" "cat" "meow"}]
   ...      [numbers ["zero" "one" "two" "three"]]]
   ...  (print (get animals "dog"))
   ...  (print (get numbers 2)))
   bark
   two

.. note:: `get` raises a KeyError if a dictionary is queried for a non-existing
          key.

.. note:: `get` raises an IndexError if a list is queried for an index that is
          out of bounds.

global
------


if
--

the `if` form is used to conditionally select code to be executed. It has to
contain the condition block and the block to be executed if the condition
evaluates `True`. Optionally it may contain a block that is executed in case
the evaluation of the condition is `False`.

Example usage:

.. code-block:: clj

    (if (money-left? account)
      (print "lets go shopping")
      (print "lets go and work"))

Truth values of Python objects are respected. Values `None`, `False`, zero of
any numeric type, empty sequence and empty dictionary are considered `False`.
Everything else is considered `True`.


import
------

`import` is used to import modules, like in Python. There are several forms
of import you can use.

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


kwapply
-------


lambda / fn
-----------


list-comp
---------

`list-comp` performs list comprehensions. It takes two or three parameters.
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

`not` form is used in logical expressions. It takes a single parameter and
returns a reversed truth value. If `True` is given as a parameter, `False`
will be returned and vice-versa. Examples for usage:

.. code-block:: clj

    => (not True)
    False

    => (not False)
    True

    => (not None)
    True


or
--

`or` form is used in logical expressions. It takes at least two parameters. It
will return the first non-false parameter. If no such value exist, the last
parameter will be returned.

.. code-block:: clj

    => (or True False)
    True

    => (and False False)
    False

    => (and False 1 True False)
    1

.. note:: `or` shortcuts and stops evaluating parameters as soon as the first
          true is encountered. However, in the current implementation of Hy
          statements are executed as soon as they are converted to expressions.
          The following two examples demonstrates the difference.

.. code-block:: clj

    => (or True (print "hello"))
    hello
    True

    => (defn side-effects [x] (print "I can has" x) x)
    => (or (side-effects 42) (side-effects False))
    I can has 42
    42


print
-----

the `print` form is used to output on screen. Example usage:

.. code-block:: clj

    (print "Hello world!")

.. note:: `print` always returns None

require
-------


slice
-----

`slice` can be used to take a subset of a list and create a new list from it.
The form takes at least one parameter specifying the list to slice. Two
optional parameters can be used to give the start and end position of the
subset. If they are not supplied, default value of None will be used instead.
Third optional parameter is used to control step between the elements.

`slice` follows the same rules as the Python counterpart. Negative indecies are
counted starting from the end of the list.
Some examples of
usage:

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

the `throw` or `raise` forms can be used to raise an Exception at runtime.


Example usage

.. code-block:: clj

    (throw)
    ; re-rase the last exception
    
    (throw IOError)
    ; Throw an IOError
    
    (throw (IOError "foobar"))
    ; Throw an IOError("foobar")


`throw` can acccept a single argument (an `Exception` class or instance), or
no arguments to re-raise the last Exception.


try
---

the `try` form is used to start a `try` / `catch` block. The form is used
as follows

.. code-block:: clj

    (try
        (error-prone-function)
        (catch [e ZeroDivisionError] (print "Division by zero"))
        (else (print "no errors"))
        (finally (print "all done")))

`try` must contain at least one `catch` block, and may optionally have an
`else` or `finally` block. If an error is raised with a matching catch
block during execution of `error-prone-function` then that catch block will
be executed. If no errors are raised the `else` block is executed. Regardless
if an error was raised or not, the `finally` block is executed as last.


while
-----

`while` form is used to execute a single or more blocks as long as a condition
is being met.

The following example will output "hello world!" on screen indefinetely:

.. code-block:: clj

    (while True (print "hello world!"))

with
----


with-decorator
--------------


yield
-----



