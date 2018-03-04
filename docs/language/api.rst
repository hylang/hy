=================
Built-Ins
=================

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
raise a compilation error.

Access to unknown attributes raises an :exc:`AttributeError`. Access to
unknown keys raises an :exc:`IndexError` (on lists and tuples) or a
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


as->
----

.. versionadded:: 0.12.0

Expands to sequence of assignments to the provided name, starting with head.
The previous result is thus available in the subsequent form. Returns the final
result, and leaves the name bound to it in the local scope. This behaves much
like the other threading macros, but requires you to specify the threading
point per form via the name instead of always the first or last argument.

.. code-block:: clj

  ;; example how -> and as-> relate

  => (as-> 0 it
  ...      (inc it)
  ...      (inc it))
  2

  => (-> 0 inc inc)
  2

  ;; create data for our cuttlefish database

  => (setv data [{:name "hooded cuttlefish"
  ...             :classification {:subgenus "Acanthosepion"
  ...                              :species "Sepia prashadi"}
  ...             :discovered {:year 1936
  ...                          :name "Ronald Winckworth"}}
  ...            {:name "slender cuttlefish"
  ...             :classification {:subgenus "Doratosepion"
  ...                              :species "Sepia braggi"}
  ...             :discovered {:year 1907
  ...                          :name "Sir Joseph Cooke Verco"}}])

  ;; retrieve name of first entry      
  => (as-> (first data) it
  ...      (:name it))
  'hooded cuttlefish'

  ;; retrieve species of first entry
  => (as-> (first data) it
  ...      (:classification it)
  ...      (:species it))
  'Sepia prashadi'

  ;; find out who discovered slender cuttlefish
  => (as-> (filter (fn [entry] (= (:name entry)
  ...                           "slender cuttlefish")) data) it
  ...      (first it)
  ...      (:discovered it)
  ...      (:name it))
  'Sir Joseph Cooke Verco'

  ;; more convoluted example to load web page and retrieve data from it
  => (import [urllib.request [urlopen]])
  => (as-> (urlopen "http://docs.hylang.org/en/stable/") it
  ...      (.read it)
  ...      (.decode it "utf-8")
  ...      (drop (.index it "Welcome") it)
  ...      (take 30 it)
  ...      (list it)
  ...      (.join "" it))
  'Welcome to Hy’s documentation!

.. note::

  In these examples, the REPL will report a tuple (e.g. `('Sepia prashadi', 
  'Sepia prashadi')`) as the result, but only a single value is actually
  returned.


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

  =>(do
  ... (setv collection {})
  ... (assoc collection "Dog" "Bark")
  ... (print collection))
  {u'Dog': u'Bark'}

  =>(do
  ... (setv collection {})
  ... (assoc collection "Dog" "Bark" "Cat" "Meow")
  ... (print collection))
  {u'Cat': u'Meow', u'Dog': u'Bark'}

  =>(do
  ... (setv collection [1 2 3 4])
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


comment
----

The ``comment`` macro ignores its body and always expands to ``None``.
Unlike linewise comments, the body of the ``comment`` macro must
be grammatically valid Hy, so the compiler can tell where the comment ends.
Besides the semicolon linewise comments,
Hy also has the ``#_`` discard prefix syntax to discard the next form.
This is completely discarded and doesn't expand to anything, not even ``None``.

.. code-block:: clj

   => (print (comment <h1>Surprise!</h1>
   ...                <p>You'd be surprised what's grammatically valid in Hy.</p>
   ...                <p>(Keep delimiters in balance, and you're mostly good to go.)</p>)
   ...        "Hy")
   None Hy
   => (print #_(comment <h1>Surprise!</h1>
   ...                  <p>You'd be surprised what's grammatically valid in Hy.</p>
   ...                  <p>(Keep delimiters in balance, and you're mostly good to go.)</p>))
   ...        "Hy")
   Hy


cond
----

``cond`` can be used to build nested ``if`` statements. The following example
shows the relationship between the macro and its expansion:

.. code-block:: clj

    (cond [condition-1 result-1]
          [condition-2 result-2])

    (if condition-1 result-1
      (if condition-2 result-2))

If only the condition is given in a branch, then the condition is also used as
the result. The expansion of this single argument version is demonstrated
below:

.. code-block:: clj

    (cond [condition-1]
          [condition-2])

    (if condition-1 condition-1
      (if condition-2 condition-2))

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
      (side-effect1 x)
      (if (% x 2)
        (continue))
      (side-effect2 x))


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


do
----------

``do`` is used to evaluate each of its arguments and return the
last one. Return values from every other than the last argument are discarded.
It can be used in ``list-comp`` to perform more complex logic as shown in one
of the following examples.

Some example usage:

.. code-block:: clj

    => (if True
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


doc / #doc
----------

Documentation macro and tag macro.
Gets help for macros or tag macros, respectively.

.. code-block:: clj

    => (doc doc)
    Help on function (doc) in module hy.core.macros:

    (doc)(symbol)
        macro documentation

        Gets help for a macro function available in this module.
        Use ``require`` to make other macros available.

        Use ``#doc foo`` instead for help with tag macro ``#foo``.
        Use ``(help foo)`` instead for help with runtime objects.

    => (doc comment)
    Help on function (comment) in module hy.core.macros:

    (comment)(*body)
        Ignores body and always expands to None

    => #doc doc
    Help on function #doc in module hy.core.macros:

    #doc(symbol)
        tag macro documentation

    Gets help for a tag macro function available in this module.


setv
----

``setv`` is used to bind a value, object, or function to a symbol.
For example:

.. code-block:: clj

    => (setv names ["Alice" "Bob" "Charlie"])
    => (print names)
    [u'Alice', u'Bob', u'Charlie']

    => (setv counter (fn [collection item] (.count collection item)))
    => (counter [1 2 3 4 5 2 3] 2)
    2

They can be used to assign multiple variables at once:

.. code-block:: hy

    => (setv a 1 b 2)
    (1L, 2L)
    => a
    1L
    => b
    2L
    =>


defclass
--------

New classes are declared with ``defclass``. It can takes two optional parameters:
a vector defining a possible super classes and another vector containing
attributes of the new class as two item vectors.

.. code-block:: clj

    (defclass class-name [super-class-1 super-class-2]
      [attribute value]

      (defn method [self] (print "hello!")))

Both values and functions can be bound on the new class as shown by the example
below:

.. code-block:: clj

    => (defclass Cat []
    ...  [age None
    ...   colour "white"]
    ...
    ...  (defn speak [self] (print "Meow")))

    => (setv spot (Cat))
    => (setv spot.colour "Black")
    'Black'
    => (.speak spot)
    Meow


.. _defn:

defn
----

``defn`` macro is used to define functions. It takes three
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
    Parameter is a dict of keyword arguments. The keys of the dict
    specify the parameter names and the values give the default values
    of the parameters.

    .. code-block:: clj

       => (defn key-parameters [&key {"a" 1 "b" 2}]
       ... (print "a is" a "and b is" b))
       => (key-parameters :a 1 :b 2)
       a is 1 and b is 2
       => (key-parameters :b 1 :a 2)
       a is 2 and b is 1

    The following declarations are equivalent:

    .. code-block:: clj

       (defn key-parameters [&key {"a" 1 "b" 2}])

       (defn key-parameters [&optional [a 1] [b 2]])

&kwargs
    Parameter will contain 0 or more keyword arguments.

    The following code examples defines a function that will print all keyword
    arguments and their values.

    .. code-block:: clj

        => (defn print-parameters [&kwargs kwargs]
        ...    (for [(, k v) (.items kwargs)] (print k v)))

        => (print-parameters :parameter-1 1 :parameter-2 2)
        parameter_1 1
        parameter_2 2

        ; to avoid the mangling of '-' to '_', use unpacking:
        => (print-parameters #** {"parameter-1" 1 "parameter-2" 2})
        parameter-1 1
        parameter-2 2

&rest
    Parameter will contain 0 or more positional arguments. No other positional
    arguments may be specified after this one.

    The following code example defines a function that can be given 0 to n
    numerical parameters. It then sums every odd number and subtracts
    every even number.

    .. code-block:: clj

        => (defn zig-zag-sum [&rest numbers]
             (setv odd-numbers (list-comp x [x numbers] (odd? x))
	           even-numbers (list-comp x [x numbers] (even? x)))
             (- (sum odd-numbers) (sum even-numbers)))

        => (zig-zag-sum)
        0
        => (zig-zag-sum 3 9 4)
        8
        => (zig-zag-sum 1 2 3 4 5 6)
        -3

&kwonly
    .. versionadded:: 0.12.0

    Parameters that can only be called as keywords. Mandatory
    keyword-only arguments are declared with the argument's name;
    optional keyword-only arguments are declared as a two-element list
    containing the argument name followed by the default value (as
    with `&optional` above).

    .. code-block:: clj

        => (defn compare [a b &kwonly keyfn [reverse False]]
        ...  (setv result (keyfn a b))
        ...  (if (not reverse)
        ...    result
        ...    (- result)))
        => (compare "lisp" "python"
        ...         :keyfn (fn [x y]
        ...                  (reduce - (map (fn [s] (ord (first s))) [x y]))))
        -4
        => (compare "lisp" "python"
        ...         :keyfn (fn [x y]
        ...                   (reduce - (map (fn [s] (ord (first s))) [x y])))
        ...         :reverse True)
        4

    .. code-block:: python

        => (compare "lisp" "python")
        Traceback (most recent call last):
          File "<input>", line 1, in <module>
        TypeError: compare() missing 1 required keyword-only argument: 'keyfn'

    Availability: Python 3.


defn/a
------

``defn/a`` macro is a variant of ``defn`` that instead defines
coroutines. It takes three parameters: the *name* of the function to
define, a vector of *parameters*, and the *body* of the function:

.. code-block:: clj

    (defn/a name [params] body)

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
       retval = main(*sys.argv)

       if isinstance(retval, int):
           sys.exit(retval)

Note that as you can see above, if you return an integer from this
function, this will be used as the exit status for your script.
(Python defaults to exit status 0 otherwise, which means everything's
okay!) Since ``(sys.exit 0)`` is not run explicitly in the case of a
non-integer return from ``defmain``, it's a good idea to put ``(defmain)``
as the last piece of code in your file.

If you want fancy command-line arguments, you can use the standard Python
module ``argparse`` in the usual way:

.. code-block:: clj

    (import argparse)

    (defmain [&rest _]
      (setv parser (argparse.ArgumentParser))
      (.add-argument parser "STRING"
        :help "string to replicate")
      (.add-argument parser "-n" :type int :default 3
        :help "number of copies")
      (setv args (parser.parse_args))

      (print (* args.STRING args.n))

      0)

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

.. _defmacro!:

defmacro!
---------

``defmacro!`` is like ``defmacro/g!`` plus automatic once-only evaluation for
``o!`` parameters, which are available as the equivalent ``g!`` symbol.

For example,

.. code-block:: clj

    => (defn expensive-get-number [] (print "spam") 14)
    => (defmacro triple-1 [n] `(+ ~n ~n ~n))
    => (triple-1 (expensive-get-number))  ; evals n three times
    spam
    spam
    spam
    42
    => (defmacro/g! triple-2 [n] `(do (setv ~g!n ~n) (+ ~g!n ~g!n ~g!n)))
    => (triple-2 (expensive-get-number))  ; avoid repeats with a gensym
    spam
    42
    => (defmacro! triple-3 [o!n] `(+ ~g!n ~g!n ~g!n))
    => (triple-3 (expensive-get-number))  ; easier with defmacro!
    spam
    42


deftag
--------

.. versionadded:: 0.13.0

``deftag`` defines a tag macro. A tag macro is a unary macro that has the
same semantics as an ordinary macro defined with ``defmacro``. It is called with
the syntax ``#tag FORM``, where ``tag`` is the name of the macro, and ``FORM``
is any form. The ``tag`` is often only one character, but it can be any symbol.

.. code-block:: clj

    => (deftag ♣ [expr] `[~expr ~expr])
    <function <lambda> at 0x7f76d0271158>
    => #♣ 5
    [5, 5]
    => (setv x 0)
    => #♣(+= x 1)
    [None, None]
    => x
    2

In this example, if you used ``(defmacro ♣ ...)`` instead of ``(deftag
♣ ...)``, you would call the macro as ``(♣ 5)`` or ``(♣ (+= x 1))``.

The syntax for calling tag macros is similar to that of reader macros a la
Common Lisp's ``SET-MACRO-CHARACTER``. In fact, before Hy 0.13.0, tag macros
were called "reader macros", and defined with ``defreader`` rather than
``deftag``. True reader macros are not (yet) implemented in Hy.

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
  => (del (cut test 2 4)) ;; remove items from 2 to 4 excluded
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
  [2, 1]

.. code-block:: clj

  => (setv collection [])
  => (.append collection 1)
  => (.append collection 2)
  => (.reverse collection)
  => collection
  [2, 1]


eval-and-compile
----------------

``eval-and-compile`` is a special form that takes any number of forms. The input forms are evaluated as soon as the ``eval-and-compile`` form is compiled, instead of being deferred until run-time. The input forms are also left in the program so they can be executed at run-time as usual. So, if you compile and immediately execute a program (as calling ``hy foo.hy`` does when ``foo.hy`` doesn't have an up-to-date byte-compiled version), ``eval-and-compile`` forms will be evaluated twice.

One possible use of ``eval-and-compile`` is to make a function available both at compile-time (so a macro can call it while expanding) and run-time (so it can be called like any other function)::

    (eval-and-compile
      (defn add [x y]
        (+ x y)))

    (defmacro m [x]
      (add x 2))

    (print (m 3))     ; prints 5
    (print (add 3 6)) ; prints 9

Had the ``defn`` not been wrapped in ``eval-and-compile``, ``m`` wouldn't be able to call ``add``, because when the compiler was expanding ``(m 3)``, ``add`` wouldn't exist yet.

eval-when-compile
-----------------

``eval-when-compile`` is like ``eval-and-compile``, but the code isn't executed at run-time. Hence, ``eval-when-compile`` doesn't directly contribute any code to the final program, although it can still change Hy's state while compiling (e.g., by defining a function).

.. code-block:: clj

    (eval-when-compile
      (defn add [x y]
        (+ x y)))

    (defmacro m [x]
      (add x 2))

    (print (m 3))     ; prints 5
    (print (add 3 6)) ; raises NameError: name 'add' is not defined

first
-----

``first`` is a function for accessing the first element of a collection.

.. code-block:: clj

    => (first (range 10))
    0

It is implemented as ``(next (iter coll) None)``, so it works with any
iterable, and if given an empty iterable, it will return ``None`` instead of
raising an exception.

.. code-block:: clj

    => (first (repeat 10))
    10
    => (first [])
    None

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


for/a
-----

``for/a`` behaves like ``for`` but is used to call a function for each
element generated by an asynchronous generator expression. The results
of each call are discarded and the ``for/a`` expression returns
``None`` instead.

.. code-block:: clj

    ;; assuming that (side-effect) is a function that takes a single parameter
    (for/a [element (agen)] (side-effect element))

    ;; for/a can have an optional else block
    (for/a [element (agen)] (side-effect element)
         (else (side-effect-2)))


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

    => (setv collection (range 10))
    => (setv filtered (genexpr x [x collection] (even? x)))
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

``get`` is used to access single elements in collections. ``get`` takes at
least two parameters: the *data structure* and the *index* or *key* of the
item. It will then return the corresponding value from the collection. If
multiple *index* or *key* values are provided, they are used to access
successive elements in a nested structure. Example usage:

.. code-block:: clj

   => (do
   ...  (setv animals {"dog" "bark" "cat" "meow"}
   ...        numbers (, "zero" "one" "two" "three")
   ...        nested [0 1 ["a" "b" "c"] 3 4])
   ...  (print (get animals "dog"))
   ...  (print (get numbers 2))
   ...  (print (get nested 2 1)))

   bark
   two
   b

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
keyword, the second function would have raised a ``NameError``.

.. code-block:: clj

    (defn set-a [value]
      (global a)
      (setv a value))

    (defn print-a []
      (print a))

    (set-a 5)
    (print-a)

if / if* / if-not
-----------------

.. versionadded:: 0.10.0
   if-not

``if / if* / if-not`` respect Python *truthiness*, that is, a *test* fails if it
evaluates to a "zero" (including values of ``len`` zero, ``None``, and
``False``), and passes otherwise, but values with a ``__bool__`` method
(``__nonzero__`` in Python 2) can overrides this.

The ``if`` macro is for conditionally selecting an expression for evaluation.
The result of the selected expression becomes the result of the entire ``if``
form. ``if`` can select a group of expressions with the help of a ``do`` block.

``if`` takes any number of alternating *test* and *then* expressions, plus an
optional *else* expression at the end, which defaults to ``None``. ``if`` checks
each *test* in turn, and selects the *then* corresponding to the first passed
test. ``if`` does not evaluate any expressions following its selection, similar
to the ``if/elif/else`` control structure from Python. If no tests pass, ``if``
selects *else*.

The ``if*`` special form is restricted to 2 or 3 arguments, but otherwise works
exactly like ``if`` (which expands to nested ``if*`` forms), so there is
generally no reason to use it directly.

``if-not`` is similar to ``if*`` but the second expression will be executed
when the condition fails while the third and final expression is executed when
the test succeeds -- the opposite order of ``if*``. The final expression is
again optional and defaults to ``None``.

Example usage:

.. code-block:: clj

    (print (if (< n 0.0) "negative"
               (= n 0.0) "zero"
               (> n 0.0) "positive"
               "not a number"))

    (if* (money-left? account)
      (print "let's go shopping")
      (print "let's go and work"))

    (if-not (money-left? account)
      (print "let's go and work")
      (print "let's go shopping"))



lif and lif-not
---------------------------------------

.. versionadded:: 0.10.0

.. versionadded:: 0.11.0
   lif-not

For those that prefer a more Lispy ``if`` clause, we have
``lif``. This *only* considers ``None`` to be false! All other
"false-ish" Python values are considered true. Conversely, we have
``lif-not`` in parallel to ``if`` and ``if-not`` which
reverses the comparison.


.. code-block:: clj

    => (lif True "true" "false")
    "true"
    => (lif False "true" "false")
    "true"
    => (lif 0 "true" "false")
    "true"
    => (lif None "true" "false")
    "false"
    => (lif-not None "true" "false")
    "true"
    => (lif-not False "true" "false")
    "false"

.. _import:

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
    ;;
    ;; Python:
    ;; from tests.resources import kwtest, function_with_a_dash
    ;; from os.path import exists, isdir as is_dir, isfile as is_file
    ;; import sys as systest
    (import [tests.resources [kwtest function-with-a-dash]]
            [os.path [exists
	              isdir :as dir?
		      isfile :as file?]]
            [sys :as systest])

    ;; Import all module functions into current namespace
    ;;
    ;; Python: from sys import *
    (import [sys [*]])


fn
-----------

``fn``, like Python's ``lambda``, can be used to define an anonymous function.
Unlike Python's ``lambda``, the body of the function can comprise several
statements. The parameters are similar to ``defn``: the first parameter is
vector of parameters and the rest is the body of the function. ``fn`` returns a
new function. In the following example, an anonymous function is defined and
passed to another function for filtering output.

.. code-block:: clj

    => (setv people [{:name "Alice" :age 20}
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

fn/a
----

``fn/a`` is a variant of ``fn`` than defines an anonymous coroutine.
The parameters are similar to ``defn/a``: the first parameter is
vector of parameters and the rest is the body of the function. ``fn/a`` returns a
new coroutine.

last
-----------

.. versionadded:: 0.11.0

``last`` can be used for accessing the last element of a collection:

.. code-block:: clj

    => (last [2 4 6])
    6


list-comp
---------

``list-comp`` performs list comprehensions. It takes two or three parameters.
The first parameter is the expression controlling the return value, while
the second is used to select items from a list. The third and optional
parameter can be used to filter out some of the items in the list based on a
conditional expression. Some examples:

.. code-block:: clj

    => (setv collection (range 10))
    => (list-comp x [x collection])
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

    => (list-comp (* x 2) [x collection])
    [0, 2, 4, 6, 8, 10, 12, 14, 16, 18]

    => (list-comp (* x 2) [x collection] (< x 5))
    [0, 2, 4, 6, 8]


nonlocal
--------

.. versionadded:: 0.11.1

**PYTHON 3.0 AND UP ONLY!**

``nonlocal`` can be used to mark a symbol as not local to the current scope.
The parameters are the names of symbols to mark as nonlocal.  This is necessary
to modify variables through nested ``fn`` scopes:

.. code-block:: clj

    (defn some-function []
      (setv x 0)
      (register-some-callback
        (fn [stuff]
          (nonlocal x)
          (setv x stuff))))

Without the call to ``(nonlocal x)``, the inner function would redefine ``x`` to
``stuff`` inside its local scope instead of overwriting the ``x`` in the outer
function.

See `PEP3104 <https://www.python.org/dev/peps/pep-3104/>`_ for further
information.


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
    => x  ; variable x is set to unevaluated expression
    HyExpression([
      HySymbol('print'),
      HyString('Hello World')])
    => (eval x)
    Hello World


require
-------

``require`` is used to import macros from one or more given modules. It allows
parameters in all the same formats as ``import``. The ``require`` form itself
produces no code in the final program: its effect is purely at compile-time, for
the benefit of macro expansion. Specifically, ``require`` imports each named
module and then makes each requested macro available in the current module.

The following are all equivalent ways to call a macro named ``foo`` in the module ``mymodule``:

.. code-block:: clj

    (require mymodule)
    (mymodule.foo 1)

    (require [mymodule :as M])
    (M.foo 1)

    (require [mymodule [foo]])
    (foo 1)

    (require [mymodule [*]])
    (foo 1)

    (require [mymodule [foo :as bar]])
    (bar 1)

Macros that call macros
~~~~~~~~~~~~~~~~~~~~~~~

One aspect of ``require`` that may be surprising is what happens when one
macro's expansion calls another macro. Suppose ``mymodule.hy`` looks like this:

.. code-block:: clj

    (defmacro repexpr [n expr]
      ; Evaluate the expression n times
      ; and collect the results in a list.
      `(list (map (fn [_] ~expr) (range ~n))))

    (defmacro foo [n]
      `(repexpr ~n (input "Gimme some input: ")))

And then, in your main program, you write:

.. code-block:: clj

    (require [mymodule [foo]])

    (print (mymodule.foo 3))

Running this raises ``NameError: name 'repexpr' is not defined``, even though
writing ``(print (foo 3))`` in ``mymodule`` works fine. The trouble is that your
main program doesn't have the macro ``repexpr`` available, since it wasn't
imported (and imported under exactly that name, as opposed to a qualified name).
You could do ``(require [mymodule [*]])`` or ``(require [mymodule [foo
repexpr]])``, but a less error-prone approach is to change the definition of
``foo`` to require whatever sub-macros it needs:

.. code-block:: clj

    (defmacro foo [n]
      `(do
        (require mymodule)
        (mymodule.repexpr ~n (raw-input "Gimme some input: "))))

It's wise to use ``(require mymodule)`` here rather than ``(require [mymodule
[repexpr]])`` to avoid accidentally shadowing a function named ``repexpr`` in
the main program.

Qualified macro names
~~~~~~~~~~~~~~~~~~~~~

Note that in the current implementation, there's a trick in qualified macro
names, like ``mymodule.foo`` and ``M.foo`` in the above example. These names
aren't actually attributes of module objects; they're just identifiers with
periods in them. In fact, ``mymodule`` and ``M`` aren't defined by these
``require`` forms, even at compile-time. None of this will hurt you unless try
to do introspection of the current module's set of defined macros, which isn't
really supported anyway.

rest
----

``rest`` takes the given collection and returns an iterable of all but the
first element.

.. code-block:: clj

    => (list (rest (range 10)))
    [1, 2, 3, 4, 5, 6, 7, 8, 9]

Given an empty collection, it returns an empty iterable.

.. code-block:: clj

    => (list (rest []))
    []

return
-------

``return`` compiles to a :py:keyword:`return` statement. It exits the
current function, returning its argument if provided with one or
``None`` if not.

.. code-block:: hy

    => (defn f [x] (for [n (range 10)] (when (> n x) (return n))))
    => (f 3.9)
    4

Note that in Hy, ``return`` is necessary much less often than in Python,
since the last form of a function is returned automatically. Hence, an
explicit ``return`` is only necessary to exit a function early.

.. code-block:: hy

    => (defn f [x] (setv y 10) (+ x y))
    => (f 4)
    14

To get Python's behavior of returning ``None`` when execution reaches
the end of a function, put ``None`` there yourself.

.. code-block:: hy

    => (defn f [x] (setv y 10) (+ x y) None)
    => (print (f 4))
    None

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


cut
-----

``cut`` can be used to take a subset of a list and create a new list from it.
The form takes at least one parameter specifying the list to cut. Two
optional parameters can be used to give the start and end position of the
subset. If they are not supplied, the default value of ``None`` will be used
instead. The third optional parameter is used to control step between the elements.

``cut`` follows the same rules as its Python counterpart. Negative indices are
counted starting from the end of the list. Some example usage:

.. code-block:: clj

    => (setv collection (range 10))

    => (cut collection)
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]

    => (cut collection 5)
    [5, 6, 7, 8, 9]

    => (cut collection 2 8)
    [2, 3, 4, 5, 6, 7]

    => (cut collection 2 8 2)
    [2, 4, 6]

    => (cut collection -4 -2)
    [6, 7]


raise
-------------

The ``raise`` form can be used to raise an ``Exception`` at
runtime. Example usage:

.. code-block:: clj

    (raise)
    ; re-rase the last exception

    (raise IOError)
    ; raise an IOError

    (raise (IOError "foobar"))
    ; raise an IOError("foobar")


``raise`` can accept a single argument (an ``Exception`` class or instance)
or no arguments to re-raise the last ``Exception``.


try
---

The ``try`` form is used to catch exceptions (``except``) and run cleanup
actions (``finally``).

.. code-block:: clj

    (try
      (error-prone-function)
      (another-error-prone-function)
      (except [ZeroDivisionError]
        (print "Division by zero"))
      (except [[IndexError KeyboardInterrupt]]
        (print "Index error or Ctrl-C"))
      (except [e ValueError]
        (print "ValueError:" (repr e)))
      (except [e [TabError PermissionError ReferenceError]]
        (print "Some sort of error:" (repr e)))
      (else
        (print "No errors"))
      (finally
        (print "All done")))

The first argument of ``try`` is its body, which can contain one or more forms.
Then comes any number of ``except`` clauses, then optionally an ``else``
clause, then optionally a ``finally`` clause. If an exception is raised with a
matching ``except`` clause during the execution of the body, that ``except``
clause will be executed. If no exceptions are raised, the ``else`` clause is
executed. The ``finally`` clause will be executed last regardless of whether an
exception was raised.

The return value of ``try`` is the last form of the ``except`` clause that was
run, or the last form of ``else`` if no exception was raised, or the ``try``
body if there is no ``else`` clause.


unless
------

The ``unless`` macro is a shorthand for writing an ``if`` statement that checks if
the given conditional is ``False``. The following shows the expansion of this macro.

.. code-block:: clj

    (unless conditional statement)

    (if conditional
      None
      (do statement))


unpack-iterable, unpack-mapping
-------------------------------

``unpack-iterable`` and ``unpack-mapping`` allow an iterable or mapping
object (respectively) to provide positional or keywords arguments
(respectively) to a function.

.. code-block:: clj

    => (defn f [a b c d] [a b c d])
    => (f (unpack-iterable [1 2]) (unpack-mapping {"c" 3 "d" 4}))
    [1, 2, 3, 4]

``unpack-iterable`` is usually written with the shorthand ``#*``, and
``unpack-mapping`` with ``#**``.

.. code-block:: clj

    => (f #* [1 2] #** {"c" 3 "d" 4})
    [1, 2, 3, 4]

With Python 3, you can unpack in an assignment list (:pep:`3132`).

.. code-block:: clj

    => (setv [a #* b c] [1 2 3 4 5])
    => [a b c]
    [1, [2, 3, 4], 5]

With Python 3.5 or greater, unpacking is allowed in more contexts than just
function calls, and you can unpack more than once in the same expression
(:pep:`448`).

.. code-block:: clj

    => [#* [1 2] #* [3 4]]
    [1, 2, 3, 4]
    => {#** {1 2} #** {3 4}}
    {1: 2, 3: 4}
    => (f #* [1] #* [2] #** {"c" 3} #** {"d" 4})
    [1, 2, 3, 4]


unquote
-------

Within a quasiquoted form, ``unquote`` forces evaluation of a symbol. ``unquote``
is aliased to the tilde (``~``) symbol.

.. code-block:: clj

    => (setv nickname "Cuddles")
    => (quasiquote (= nickname (unquote nickname)))
    HyExpression([
      HySymbol('='),
      HySymbol('nickname'),
      'Cuddles'])
    => `(= nickname ~nickname)
    HyExpression([
      HySymbol('='),
      HySymbol('nickname'),
      'Cuddles'])


unquote-splice
--------------

``unquote-splice`` forces the evaluation of a symbol within a quasiquoted form,
much like ``unquote``. ``unquote-splice`` can be used when the symbol
being unquoted contains an iterable value, as it "splices" that iterable into
the quasiquoted form. ``unquote-splice`` can also be used when the value
evaluates to a false value such as ``None``, ``False``, or ``0``, in which
case the value is treated as an empty list and thus does not splice anything
into the form. ``unquote-splice`` is aliased to the ``~@`` syntax.

.. code-block:: clj

    => (setv nums [1 2 3 4])
    => (quasiquote (+ (unquote-splice nums)))
    HyExpression([
      HySymbol('+'),
      1,
      2,
      3,
      4])
    => `(+ ~@nums)
    HyExpression([
      HySymbol('+'),
      1,
      2,
      3,
      4])
    => `[1 2 ~@(if (neg? (first nums)) nums)]
    HyList([
      HyInteger(1),
      HyInteger(2)])

Here, the last example evaluates to ``('+' 1 2)``, since the condition
``(< (nth nums 0) 0)`` is ``False``, which makes this ``if`` expression
evaluate to ``None``, because the ``if`` expression here does not have an
else clause. ``unquote-splice`` then evaluates this as an empty value,
leaving no effects on the list it is enclosed in, therefore resulting in
``('+' 1 2)``.

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

``while`` compiles to a :py:keyword:`while` statement. It is used to execute a
set of forms as long as a condition is met. The first argument to ``while`` is
the condition, and any remaining forms constitute the body. The following
example will output "Hello world!" to the screen indefinitely:

.. code-block:: clj

    (while True (print "Hello world!"))

The last form of a ``while`` loop can be an ``else`` clause, which is executed
after the loop terminates, unless it exited abnormally (e.g., with ``break``). So,

.. code-block:: clj

    (setv x 2)
    (while x
       (print "In body")
       (-= x 1)
       (else
         (print "In else")))

prints

::

    In body
    In body
    In else

If you put a ``break`` or ``continue`` form in the condition of a ``while``
loop, it will apply to the very same loop rather than an outer loop, even if
execution is yet to ever reach the loop body. (Hy compiles a ``while`` loop
with statements in its condition by rewriting it so that the condition is
actually in the body.) So,

.. code-block:: clj

    (for [x [1]]
       (print "In outer loop")
       (while
         (do
           (print "In condition")
           (break)
           (print "This won't print.")
           True)
         (print "This won't print, either."))
       (print "At end of outer loop"))

prints

::

    In outer loop
    In condition
    At end of outer loop

with
----

``with`` is used to wrap the execution of a block within a context manager. The
context manager can then set up the local system and tear it down in a controlled
manner. The archetypical example of using ``with`` is when processing files.
``with`` can bind context to an argument or ignore it completely, as shown below:

.. code-block:: clj

    (with [arg (expr)] block)

    (with [(expr)] block)

    (with [arg (expr) (expr)] block)

The following example will open the ``NEWS`` file and print its content to the
screen. The file is automatically closed after it has been processed.

.. code-block:: clj

    (with [f (open "NEWS")] (print (.read f)))

``with`` returns the value of its last form, unless it suppresses an exception
(because the context manager's ``__exit__`` method returned true), in which
case it returns ``None``. So, the previous example could also be written

.. code-block:: clj

    (print (with [f (open "NEWS")] (.read f)))

with/a
------

``with/a`` behaves like ``with``, but is used to wrap the execution of
a block within an asynchronous context manager. The context manager can
then set up the local system and tear it down in a controlled manner
asynchronously.

.. code-block:: clj

    (with/a [arg (expr)] block)

    (with/a [(expr)] block)

    (with/a [arg (expr) (expr)] block)

``with/a`` returns the value of its last form, unless it suppresses an exception
(because the context manager's ``__aexit__`` method returned true), in which
case it returns ``None``.

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

#@
~~

.. versionadded:: 0.12.0

The tag macro ``#@`` can be used as a shorthand for ``with-decorator``. With
``#@``, the previous example becomes:

.. code-block:: clj

    => #@(inc-decorator (defn addition [a b] (+ a b)))
    => (addition 1 1)
    4
    => #@(inc2-decorator inc-decorator
    ...   (defn addition [a b] (+ a b)))
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

   (do
     (setv a (gensym)
           b (gensym)
           c (gensym))
     ...)

.. seealso::

   Section :ref:`using-gensym`


xor
---

.. versionadded:: 0.12.0

``xor`` performs the logical operation of exclusive OR. It takes two arguments.
If exactly one argument is true, that argument is returned. If neither is true,
the second argument is returned (which will necessarily be false). Otherwise,
when both arguments are true, the value ``False`` is returned.

.. code-block:: clj

    => [(xor 0 0) (xor 0 1) (xor 1 0) (xor 1 1)]
    [0, 1, 1, False]


yield
-----

``yield`` is used to create a generator object that returns one or more values.
The generator is iterable and therefore can be used in loops, list
comprehensions and other similar constructs.

The function ``random-numbers`` shows how generators can be used to generate
infinite series without consuming infinite amount of memory.

.. code-block:: clj

    => (defn multiply [bases coefficients]
    ...  (for [(, base coefficient) (zip bases coefficients)]
    ...   (yield (* base coefficient))))

    => (multiply (range 5) (range 5))
    <generator object multiply at 0x978d8ec>

    => (list-comp value [value (multiply (range 10) (range 10))])
    [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]

    => (import random)
    => (defn random-numbers [low high]
    ...  (while True (yield (.randint random low high))))
    => (list-comp x [x (take 15 (random-numbers 1 50))])
    [7, 41, 6, 22, 32, 17, 5, 38, 18, 38, 17, 14, 23, 23, 19]


yield-from
----------

.. versionadded:: 0.9.13

**PYTHON 3.3 AND UP ONLY!**

``yield-from`` is used to call a subgenerator.  This is useful if you
want your coroutine to be able to delegate its processes to another
coroutine, say, if using something fancy like
`asyncio <https://docs.python.org/3.4/library/asyncio.html>`_.
