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
    `hy_`. For instance, `⚘` will become `hy_w7h`, `♥` will become `hy_g6h`,
    and `i♥u` will become `hy_iu_t0x`.

  * Symbols that contain dashes will have them replaced with underscores. For
    example, `render-template` will become `render_template`. This means that
    symbols with dashes will shadow their underscore equivalents, and vice
    versa.


Builtins
========

Hy features a number of special forms that are used to help generate
correct Python AST. The following are "special" forms, which may have
behavior that's slightly unexpected in some situations.

.
-

.. versionadded:: 0.9.13


`.` is used to perform attribute access on objects. It uses a small DSL
to allow quick access to attributes and items in a nested datastructure.

For instance,

.. code-block:: clj

    (. foo bar baz [(+ 1 2)] frob)

Compiles down to

.. code-block:: python

     foo.bar.baz[1 + 2].frob

`.` compiles its first argument (in the example, `foo`) as the object on
which to do the attribute dereference. It uses bare symbols as
attributes to access (in the example, `bar`, `baz`, `frob`), and
compiles the contents of lists (in the example, ``[(+ 1 2)]``) for
indexation. Other arguments throw a compilation error.

Access to unknown attributes throws an :exc:`AttributeError`. Access to
unknown keys throws an :exc:`IndexError` (on lists and tuples) or a
:exc:`KeyError` (on dicts).

->
--

`->` or `threading macro` is used to avoid nesting of expressions. The threading
macro inserts each expression into the next expression’s first argument place.
The following code demonstrates this:

.. code-block:: clj

    => (defn output [a b] (print a b))
    => (-> (+ 5 5) (output 5))
    10 5


->>
---

`->>` or `threading tail macro` is similar to `threading macro` but instead of
inserting each expression into the next expression’s first argument place, it
appends it as the last argument. The following code demonstrates this:

.. code-block:: clj

    => (defn output [a b] (print a b))
    => (->> (+ 5 5) (output 5))
    5 10


apply
-----

`apply` is used to apply an optional list of arguments and an optional
dictionary of kwargs to a function.

Usage: `(apply fn-name [args] [kwargs])`

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
an index of a list to a value. It takes at least three parameters: `datastructure` 
to be modified, `key` or `index`  and `value`. If more than three parameters are
used it will associate in pairs.

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


cond
----

`cond` macro can be used to build nested if-statements.

The following example shows the relationship between the macro and the expanded
code:

.. code-block:: clj

    (cond [condition-1 result-1]
          [condition-2 result-2])

    (if condition-1 result-1
      (if condition-2 result-2))

As shown below only the first matching result block is executed.

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

`continue` returns execution to the start of a loop. In the following example,
function `(side-effect1)` is called for each iteration. `(side-effect2)` 
however is called only for every other value in the list.

.. code-block:: clj

    ;; assuming that (side-effect1) and (side-effect2) are functions and
    ;; collection is a list of numerical values

    (for [x collection]
      (do
        (side-effect1 x)
        (if (% x 2)
          (continue))
        (side-effect2 x)))


do / progn
----------

the `do` and `progn` forms are used to evaluate each of their arguments and
return the last one. Return values from every other than the last argument are
discarded. It can be used in `lambda` or `list-comp` to perform more complex
logic as shown by one of the examples.

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

`def` and `setv` are used to bind value, object or a function to a symbol. For
example:

.. code-block:: clj

    => (def names ["Alice" "Bob" "Charlie"])
    => (print names)
    [u'Alice', u'Bob', u'Charlie']

    => (setv counter (fn [collection item] (.count collection item)))
    => (counter [1 2 3 4 5 2 3] 2)
    2


defclass
--------

new classes are declared with `defclass`. It can takes two optional parameters:
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


defn / defun
------------

`defn` and `defun` macros are used to define functions. They take three
parameters: `name` of the function to define, vector of `parameters` and the
`body` of the function:

.. code-block:: clj

    (defn name [params] body)

Parameters may have following keywords in front of them:

&optional
    parameter is optional. The parameter can be given as a two item list, where
    the first element is parameter name and the second is the default value. The
    parameter can be also given as a single item, in which case the default
    value is None.

    .. code-block:: clj

        => (defn total-value [value &optional [value-added-tax 10]]
        ...  (+ (/ (* value value-added-tax) 100) value))

	=> (total-value 100)
        110.0

    	=> (total-value 100 1)
	101.0

&key
    

&kwargs
    parameter will contain 0 or more keyword arguments.

    The following code examples defines a function that will print all keyword
    arguments and their values.

    .. code-block:: clj

        => (defn print-parameters [&kwargs kwargs]
        ...    (for [(, k v) (.items kwargs)] (print k v)))

        => (kwapply (print-parameters) {"parameter-1" 1 "parameter-2" 2})
        parameter-2 2
        parameter-1 1

&rest
    parameter will contain 0 or more positional arguments. No other positional
    arguments may be specified after this one.

    The following code example defines a function that can be given 0 to n
    numerical parameters. It then sums every odd number and substracts
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

.. _defmacro:

defmacro
--------

`defmacro` is used to define macros. The general format is
`(defmacro name [parameters] expr)`.

The following example defines a macro that can be used to swap order of elements in
code, allowing the user to write code in infix notation, where operator is in
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

`defmacro-alias` is used to define macros with multiple names
(aliases). The general format is `(defmacro-alias [names] [parameters]
expr)`. It creates multiple macros with the same parameter list and
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

`defmacro/g!` is a special version of `defmacro` that is used to
automatically generate :ref:`gensym` for any symbol that
starts with ``g!``.

So ``g!a`` would become ``(gensym "a")``.

.. seealso::

   Section :ref:`using-gensym`

defreader
---------

.. versionadded:: 0.9.12

`defreader` defines a reader macro, enabling you to restructure or
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

`del` removes an object from the current namespace.

.. code-block:: clj

  => (setv foo 42)
  => (del foo)
  => foo
  Traceback (most recent call last):
    File "<console>", line 1, in <module>
  NameError: name 'foo' is not defined

`del` can also remove objects from a mapping, a list, ...

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

eval
----

`eval` evaluates a quoted expression and returns the value.

.. code-block:: clj

   => (eval '(print "Hello World"))
   "Hello World"

eval-and-compile
----------------


eval-when-compile
-----------------


first / car
-----------

`first` and `car` are macros for accessing the first element of a collection:

.. code-block:: clj

    => (first (range 10))
    0


for
-------

`for` is used to call a function for each element in a list or vector.
The results of each call are discarded and the for expression returns
None instead. The example code iterates over `collection` and
for each `element` in `collection` calls the `side-effect`
function with `element` as its argument:

.. code-block:: clj

    ;; assuming that (side-effect) is a function that takes a single parameter
    (for [element collection] (side-effect element))

    ;; for can have an optional else block
    (for [element collection] (side-effect element)
         (else (side-effect-2)))

The optional `else` block is executed only if the `for` loop terminates
normally. If the execution is halted with `break`, the `else` does not execute.

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


.. _gensym:

gensym
------

.. versionadded:: 0.9.12

`gensym` form is used to generate a unique symbol to allow writing macros
without accidental variable name clashes.

.. code-block:: clj

   => (gensym)
   u':G_1235'

   => (gensym "x")
   u':x_1236'

.. seealso::

   Section :ref:`using-gensym`

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

.. note:: `get` raises an IndexError if a list or a tuple is queried for an index
          that is out of bounds.


global
------

`global` can be used to mark a symbol as global. This allows the programmer to
assign a value to a global symbol. Reading a global symbol does not require the
`global` keyword, just the assigning does.

Following example shows how global `a` is assigned a value in a function and later
on printed on another function. Without the `global` keyword, the second function
would thrown a `NameError`.

.. code-block:: clj

    (defn set-a [value]
      (global a)
      (setv a value))

    (defn print-a []
      (print a))

    (set-a 5)
    (print-a)

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

`kwapply` can be used to supply keyword arguments to a function.

For example:

.. code-block:: clj

    => (defn rent-car [&kwargs kwargs]
    ...  (cond [(in :brand kwargs) (print "brand:" (:brand kwargs))]
    ...        [(in :model kwargs) (print "model:" (:model kwargs))]))

    => (kwapply (rent-car) {:model "T-Model"})
    model: T-Model

    => (defn total-purchase [price amount &optional [fees 1.05] [vat 1.1]] 
    ...  (* price amount fees vat))

    => (total-purchase 10 15)
    173.25

    => (kwapply (total-purchase 10 15) {"vat" 1.05})
    165.375


lambda / fn
-----------

`lambda` and `fn` can be used to define an anonymous function. The parameters are
similar to `defn`: first parameter is vector of parameters and the rest is the
body of the function. lambda returns a new function. In the example an anonymous
function is defined and passed to another function for filtering output.

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


let
---

`let` is used to create lexically scoped variables. They are created at the
beginning of `let` form and cease to exist after the form. The following
example showcases this behaviour:

.. code-block:: clj

    => (let [[x 5]] (print x) 
    ...  (let [[x 6]] (print x)) 
    ...  (print x))
    5
    6
    5

`let` macro takes two parameters: a vector defining `variables` and `body`,
which is being executed. `variables` is a vector where each element is either
a single variable or a vector defining a variable value pair. In case of a
single variable, it is assigned value None, otherwise the supplied value is
used.

.. code-block:: clj

    => (let [x [y 5]] (print x y))
    None 5


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


quasiquote
----------

`quasiquote` allows you to quote a form, but also to
selectively evaluate expressions, expressions inside a `quasiquote`
can be selectively evaluated using `unquote` (~). The evaluated form can
also be spliced using `unquote-splice` (~@). Quasiquote can be also written
using the backquote (`) symbol.


.. code-block:: clj

    ;; let `qux' be a variable with value (bar baz)
    `(foo ~qux)
    ; equivalent to '(foo (bar baz))
    `(foo ~@qux)
    ; equivalent to '(foo bar baz)


quote
-----

`quote` returns the form passed to it without evaluating. `quote` can
be alternatively written using the (') symbol


.. code-block:: clj

    => (setv x '(print "Hello World"))
    ; variable x is set to expression & not evaluated
    => x
    (u'print' u'Hello World')
    => (eval x)
    Hello World


require
-------

`require` is used to import macros from a given module. It takes at least one
parameter specifying the module which macros should be imported. Multiple
modules can be imported with a single `require`.

The following example will import macros from `module-1` and `module-2`:

.. code-block:: clj

    (require module-1 module-2)


rest / cdr
----------

`rest` and `cdr` return the collection passed as an argument without the first
element:

.. code-block:: clj

    => (rest (range 10))
    [1, 2, 3, 4, 5, 6, 7, 8, 9]


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


unless
------

`unless` macro is a shorthand for writing a if-statement that checks if the
given conditional is False. The following shows how the macro expands into code.

.. code-block:: clj

    (unless conditional statement)

    (if conditional 
      None 
      (do statement))


unquote
-------

Within a quasiquoted form, `unquote` forces evaluation of a symbol. `unquote`
is aliased to the `~` symbol.

.. code-block:: clj

    (def name "Cuddles")
    (quasiquote (= name (unquote name)))
    ;=> (u'=' u'name' u'Cuddles')

    `(= name ~name)
    ;=> (u'=' u'name' u'Cuddles')


unquote-splice
--------------

`unquote-splice` forces the evaluation of a symbol within a quasiquoted form,
much like `unquote`. `unquote-splice` can only be used when the symbol being
unquoted contains an iterable value, as it "splices" that iterable into the
quasiquoted form. `unquote-splice` is aliased to the `~@` symbol.

.. code-block:: clj

    (def nums [1 2 3 4])
    (quasiquote (+ (unquote-splice nums)))
    ;=> (u'+' 1L 2L 3L 4L)

    `(+ ~@nums)
    ;=> (u'+' 1L 2L 3L 4L)



when
----

`when` is similar to `unless`, except it tests when the given conditional is
True. It is not possible to have an `else` block in `when` macro. The following
shows how the macro is expanded into code.

.. code-block:: clj

    (when conditional statement)

    (if conditional (do statement))

while
-----

`while` form is used to execute a single or more blocks as long as a condition
is being met.

The following example will output "hello world!" on screen indefinetely:

.. code-block:: clj

    (while True (print "hello world!"))


with
----

`with` is used to wrap execution of a block with a context manager. The context
manager can then set up the local system and tear it down in a controlled
manner. Typical example of using `with` is processing files. `with`  can bind
context to an argument or ignore it completely, as shown below:

.. code-block:: clj

    (with [[arg (expr)]] block)

    (with [[(expr)]] block)

    (with [[arg (expr)] [(expr)]] block)

The following example will open file `NEWS` and print its content on screen. The
file is automatically closed after it has been processed.

.. code-block:: clj

    (with [[f (open "NEWS")]] (print (.read f)))


with-decorator
--------------

`with-decorator` is used to wrap a function with another. The function performing
decoration should accept a single value, the function being decorated and return
a new function. `with-decorator` takes two parameters, the function performing
decoration and the function being decorated.

In the following example, `inc-decorator` is used to decorate function `addition`
with a function that takes two parameters and calls the decorated function with
values that are incremented by 1. When decorated `addition` is called with values
1 and 1, the end result will be 4 (1+1 + 1+1).

.. code-block:: clj

    => (defn inc-decorator [func] 
    ...  (fn [value-1 value-2] (func (+ value-1 1) (+ value-2 1))))
    => (with-decorator inc-decorator (defn addition [a b] (+ a b)))
    => (addition 1 1)
    4


.. _with-gensyms:

with-gensyms
-------------

.. versionadded:: 0.9.12

`with-gensym` form is used to generate a set of :ref:`gensym` for use
in a macro.

.. code-block:: clojure

   (with-gensyms [a b c]
     ...)

expands to:

.. code-block:: clojure

   (let [[a (gensym)
         [b (gensym)
         [c (gensym)]]
     ...)

.. seealso::

   Section :ref:`using-gensym`


yield
-----

`yield` is used to create a generator object, that returns 1 or more values.
The generator is iterable and therefore can be used in loops, list
comprehensions and other similar constructs.

The function random-numbers shows how generators can be used to generate
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
