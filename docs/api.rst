API
===


Core Macros
-----------

The following macros are automatically imported into all Hy modules as their
base names, such that ``hy.core.macros.foo`` can be called as just ``foo``.

.. hy:function:: (annotate [value type])

   ``annotate`` and its shorthand form ``#^`` are used to denote annotations,
   including type hints, in three different contexts:

   - Standalone variable annotations (:pep:`526`)
   - Variable annotations in a :hy:func:`setv` call
   - Function-parameter annotations (:pep:`3107`)

   The difference between ``annotate`` and ``#^`` is that ``annotate`` requires
   parentheses and takes the name to be annotated first (like Python), whereas
   ``#^`` doesn't require parentheses (it only applies to the next two forms)
   and takes the type second::

      (setv (annotate x int) 1)
      (setv #^int x 1)

   The order difference is not merely visual: ``#^`` actually evaluates the
   type first.

   Here are examples with ``#^`` for all the places you can use annotations::

      ; Annotate the variable `x` as an `int` (equivalent to `x: int`).
      #^int x
      ; You can annotate with expressions (equivalent to `y: f(x)`).
      #^(f x) y

      ; Annotations with an assignment: each annotation `(int, str)`
      ; covers the term that immediately follows.
      ; Equivalent to `x: int = 1; y = 2; z: str = 3`
      (setv  #^int x 1  y 2  #^str z 3)

      ; Annotate `a` as an `int`, `c` as an `int`, and `b` as a `str`.
      ; Equivalent to `def func(a: int, b: str = None, c: int = 1): ...`
      (defn func [#^int a  #^str  [b None] #^int  [c 1]] ...)

      ; Function return annotations come before the function name (if
      ; it exists).
      (defn #^int add1 [#^int x] (+ x 1))
      (fn #^int [#^int y] (+ y 2))

   For annotating items with generic types, the :hy:func:`of <hyrule.misc.of>`
   macro will likely be of use.

   An issue with type annotations is that, as of this writing, we know of no Python type-checker that can work with :py:mod:`ast` objects or bytecode files. They all need Python source text. So you'll have to translate your Hy with ``hy2py`` in order to actually check the types.

.. _dot:

.. hy:data:: .

   ``.`` is used to perform attribute access on objects. It uses a small DSL
   to allow quick access to attributes and items in a nested data structure.

   :strong:`Examples`

   ::

       (. foo (bar "qux")  baz [(+ 1 2)] frob)

   Compiles down to:

   .. code-block:: python

       foo.bar("qux").baz[1 + 2].frob

   ``.`` compiles its first argument (in the example, *foo*) as the object on
   which to do the attribute dereference. It uses bare symbols as attributes
   to access (in the example, *baz*, *frob*), Expressions as method calls (as in *bar*),
   and compiles the contents of lists (in the example, ``[(+ 1 2)]``) for indexation.
   Other arguments raise a compilation error.

   Access to unknown attributes raises an :exc:`AttributeError`. Access to
   unknown keys raises an :exc:`IndexError` (on lists and tuples) or a
   :exc:`KeyError` (on dictionaries).

.. hy:function:: (fn [args])

   As :hy:func:`defn`, but no name for the new function is required (or
   allowed), and the newly created function object is returned. Decorators
   aren't allowed, either. However, the function body is understood identically
   to that of :hy:func:`defn`, without any of the restrictions of Python's
   :py:keyword:`lambda`. See :hy:func:`fn/a` for the asynchronous equivalent.

.. hy:function:: (fn/a [name #* args])

   As :hy:func:`fn`, but the created function object will be a :ref:`coroutine
   <py:async def>`.

.. hy:function:: (defn [name #* args])

   ``defn`` compiles to a :ref:`function definition <py:function>` (or possibly
   to an assignment of a :ref:`lambda expression <py:lambda>`). It always
   returns ``None``. It requires two arguments: a name (given as a symbol; see
   :hy:func:`fn` for anonymous functions) and a "lambda list", or list of
   parameters (also given as symbols). Any further arguments constitute the
   body of the function::

       (defn name [params] bodyform1 bodyform2…)

   An empty body is implicitly ``(return None)``. If there are at least two body
   forms, and the first of them is a string literal, this string becomes the
   :term:`py:docstring` of the function. The final body form is implicitly
   returned; thus, ``(defn f [] 5)`` is equivalent to ``(defn f [] (return
   5))``.

   ``defn`` accepts two additional, optional arguments: a bracketed list of
   :term:`decorators <py:decorator>` and an annotation (see :hy:func:`annotate`) for
   the return value. These are placed before the function name (in that order,
   if both are present)::

       (defn [decorator1 decorator2] ^annotation name [params] …)

   To define asynchronous functions, see :hy:func:`defn/a` and :hy:func:`fn/a`.

   ``defn`` lambda lists support all the same features as Python parameter
   lists and hence are complex in their full generality. The simplest case is a
   (possibly empty) list of symbols, indicating that all parameters are
   required, and can be set by position, as in ``(f value)``, or by name, as in
   ``(f :argument value)``. To set a default value for a parameter, replace the
   parameter with the bracketed list ``[pname value]``, where ``pname`` is the
   parameter name as a symbol and ``value`` is an arbitrary form. Beware that,
   per Python, ``value`` is evaluated when the function is defined, not when
   it's called, and if the resulting object is mutated, all calls will see the
   changes.

   Further special lambda-list syntax includes:

   ``/``
        If the symbol ``/`` is given in place of a parameter, it means that all
        the preceding parameters can only be set positionally.

   ``*``
        If the symbol ``*`` is given in place of a parameter, it means that all
        the following parameters can only be set by name.

   ``#* args``
        If the parameter list contains ``#* args`` or ``(unpack-iterable
        args)``, then ``args`` is set to a tuple containing all otherwise
        unmatched positional arguments. The name ``args`` is merely cherished
        Python tradition; you can use any symbol.

   ``#** kwargs``
        ``#** kwargs`` (a.k.a. ``(unpack-mapping kwargs)``) is like ``#*
        args``, but collects unmatched keyword arguments into a dictionary.

   Each of these special constructs is allowed only once, and has the same
   restrictions as in Python; e.g., ``#* args`` must precede ``#** kwargs`` if
   both are present. Here's an example with a complex lambda list::

    (defn f [a / b [c 3] * d e #** kwargs]
      [a b c d e kwargs])
    (print (hy.repr (f 1 2 :d 4 :e 5 :f 6)))
      ; => [1 2 3 4 5 {"f" 6}]

.. hy:function:: (defn/a [name lambda-list #* body])

   As :hy:func:`defn`, but defines a :ref:`coroutine <py:async def>` like
   Python's ``async def``.

.. hy:function:: (defmacro [name lambda-list #* body])

   ``defmacro`` is used to define macros. The general format is
   ``(defmacro name [parameters] expr)``.

   The following example defines a macro that can be used to swap order of elements
   in code, allowing the user to write code in infix notation, where operator is in
   between the operands.

   :strong:`Examples`
   ::

      => (defmacro infix [code]
      ...  (quasiquote (
      ...    (unquote (get code 1))
      ...    (unquote (get code 0))
      ...    (unquote (get code 2)))))

   ::

      => (infix (1 + 1))
      2

   .. note:: because all values are passed to macros unevaluated, ``defmacro``
             cannot use keyword arguments, or kwargs. All arguments are passed
             in positionally. Parameters can still be given default values
             however::

                => (defmacro a-macro [a [b 1]]
                ...  `[~a ~b])
                => (a-macro 2)
                [2 1]
                => (a-macro 2 3)
                [2 3]
                => (a-macro :b 3)
                [:b 3]

.. hy:function:: (if [test then else])

   ``if`` compiles to an :py:keyword:`if` expression (or compound ``if`` statement). The form ``test`` is evaluated and categorized as true or false according to :py:class:`bool`. If the result is true, ``then`` is evaluated and returned. Othewise, ``else`` is evaluated and returned.
   ::

     (if (has-money-left account)
       (print "Let's go shopping!")
       (print "Back to work."))

   See also:

   - :hy:func:`do`, to execute several forms as part of any of ``if``'s three arguments.
   - :hy:func:`when <hy.core.macros.when>`, for shorthand for ``(if condition (do …) None)``.
   - :hy:func:`cond <hy.core.macros.cond>`, for shorthand for nested ``if`` forms.

.. hy:function:: (await [obj])

   ``await`` creates an :ref:`await expression <py:await>`. It takes exactly one
   argument: the object to wait for. ::

       (import asyncio)
       (defn/a main []
         (print "hello")
         (await (asyncio.sleep 1))
         (print "world"))
       (asyncio.run (main))

.. hy:function:: break

   ``break`` compiles to a :py:keyword:`break` statement, which terminates the
   enclosing loop. The following example has an infinite ``while`` loop that
   ends when the user enters "k"::

       (while True
         (if (= (input "> ") "k")
           (break)
           (print "Try again")))

   In a loop with multiple iteration clauses, such as ``(for [x xs y ys] …)``,
   ``break`` only breaks out of the innermost iteration, not the whole form. To
   jump out of the whole form, enclose it in a :hy:func:`block
   <hyrule.control.block>` and use ``block-ret`` instead of ``break``. In
   the case of :hy:func:`for`, but not :hy:func:`lfor` and the other
   comprehension forms, you may also enclose it in a function and use
   :hy:func:`return`.

.. hy:function:: (chainc [#* args])

   ``chainc`` creates a :ref:`comparison expression <py:comparisons>`. It isn't
   required for unchained comparisons, which have only one comparison operator,
   nor for chains of the same operator. For those cases, you can use the
   comparison operators directly with Hy's usual prefix syntax, as in ``(= x 1)``
   or ``(< 1 2 3)``. The use of ``chainc`` is to construct chains of
   heterogeneous operators, such as ``x <= y < z``. It uses an infix syntax with
   the general form

   ::

       (chainc ARG OP ARG OP ARG…)

   Hence, ``(chainc x <= y < z)`` is equivalent to ``(and (<= x y) (< y z))``,
   including short-circuiting, except that ``y`` is only evaluated once.

   Each ``ARG`` is an arbitrary form, which does not itself use infix syntax. Use
   :hy:func:`py <py>` if you want fully Python-style operator syntax. You can
   also nest ``chainc`` forms, although this is rarely useful. Each ``OP`` is a
   literal comparison operator; other forms that resolve to a comparison operator
   are not allowed.

   At least two ``ARG``\ s and one ``OP`` are required, and every ``OP`` must be
   followed by an ``ARG``.

   As elsewhere in Hy, the equality operator is spelled ``=``, not ``==`` as in
   Python.


.. hy:function:: continue

   ``continue`` compiles to a :py:keyword:`continue` statement, which returns
   execution to the start of a loop. In the following example, ``(.append
   output x)`` is executed on each iteration, whereas ``(.append evens x)`` is
   only executed for even numbers.

   ::

       (setv  output []  evens [])
       (for [x (range 10)]
         (.append output x)
         (when (% x 2)
           (continue))
         (.append evens x))

   In a loop with multiple iteration clauses, such as ``(for [x xs y ys] …)``,
   ``continue`` applies to the innermost iteration, not the whole form. To jump
   to the next step of an outer iteration, try rewriting your loop as multiple
   nested loops and interposing a :hy:func:`block <hyrule.control.block>`, as
   in ``(for [x xs] (block (for [y ys] …)))``. You can then use ``block-ret``
   in place of ``continue``.

.. hy:function:: (do [#* body])

   ``do`` (called ``progn`` in some Lisps) takes any number of forms,
   evaluates them, and returns the value of the last one, or ``None`` if no
   forms were provided. ::

       (+ 1 (do (setv x (+ 1 1)) x))  ; => 3

.. hy:function:: (for [#* args])

   ``for`` compiles to one or more :py:keyword:`for` statements, which
   execute code repeatedly for each element of an iterable object.
   The return values of the forms are discarded and the ``for`` form
   returns ``None``.

   ::

       => (for [x [1 2 3]]
       ...  (print "iterating")
       ...  (print x))
       iterating
       1
       iterating
       2
       iterating
       3

   The first argument of ``for``, in square brackets, specifies how to loop. A simple and common case is ``[variable values]``, where ``values`` is a form that evaluates to an iterable object (such as a list) and ``variable`` is a symbol specifiying the name to assign each element to. Subsequent arguments to ``for`` are body forms to be evaluated for each iteration of the loop.

   More generally, the first argument of ``for`` allows the same types of
   clauses as :hy:func:`lfor`::

     => (for [x [1 2 3]  :if (!= x 2)  y [7 8]]
     ...  (print x y))
     1 7
     1 8
     3 7
     3 8

   The last argument of ``for`` can be an ``(else …)`` form.
   This form is executed after the last iteration of the ``for``\'s
   outermost iteration clause, but only if that outermost loop terminates
   normally. If it's jumped out of with e.g. ``break``, the ``else`` is
   ignored.

   ::

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

.. hy:function:: (assert [condition [label None]])

   ``assert`` compiles to an :py:keyword:`assert` statement, which checks
   whether a condition is true. The first argument, specifying the condition to
   check, is mandatory, whereas the second, which will be passed to
   :py:class:`AssertionError`, is optional. The whole form is only evaluated
   when :py:data:`__debug__` is true, and the second argument is only evaluated
   when :py:data:`__debug__` is true and the condition fails. ``assert`` always
   returns ``None``. ::

     (assert (= 1 2) "one should equal two")
       ; AssertionError: one should equal two

.. hy:function:: (global [sym #* syms])

   ``global`` compiles to a :py:keyword:`global` statement, which declares one
   or more names as referring to global (i.e., module-level) variables. The
   arguments are symbols; at least one is required. The return value is always
   ``None``. ::

       (setv  a 1  b 10)
       (print a b)  ; => 1 10
       (defn f []
         (global a)
         (setv  a 2  b 20))
       (f)
       (print a b)  ; => 2 10


.. hy:function:: (import [#* forms])

   ``import`` compiles to an :py:keyword:`import` statement, which makes objects
   in a different module available in the current module. It always returns
   ``None``. Hy's syntax for the various kinds of import looks like this::

       ;; Import each of these modules
       ;; Python: import sys, os.path
       (import sys os.path)

       ;; Import several names from a single module
       ;; Python: from os.path import exists, isdir as is_dir, isfile
       (import os.path [exists  isdir :as dir?  isfile])

       ;; Import with an alias
       ;; Python: import sys as systest
       (import sys :as systest)

       ;; You can list as many imports as you like of different types.
       ;; Python:
       ;;     from tests.resources import kwtest, function_with_a_dash
       ;;     from os.path import exists, isdir as is_dir, isfile as is_file
       ;;     import sys as systest
       (import tests.resources [kwtest function-with-a-dash]
               os.path [exists
                        isdir :as dir?
                        isfile :as file?]
               sys :as systest)

       ;; Import all module functions into current namespace
       ;; Python: from sys import *
       (import sys *)

   ``__all__`` can be set to control what's imported by ``import *``, as in
   Python, but beware that all names in ``__all__`` must be :ref:`mangled
   <mangling>`. The macro :hy:func:`export <hy.core.macros.export>` is a handy
   way to set ``__all__`` in a Hy program.

.. hy:function:: (eval-and-compile [#* body])

   ``eval-and-compile`` takes any number of forms as arguments. The input forms are evaluated as soon as the ``eval-and-compile`` form is compiled, instead of being deferred until run-time. The input forms are also left in the program so they can be executed at run-time as usual. So, if you compile and immediately execute a program (as calling ``hy foo.hy`` does when ``foo.hy`` doesn't have an up-to-date byte-compiled version), ``eval-and-compile`` forms will be evaluated twice. The return value is the final argument, as in ``do``.

   One possible use of ``eval-and-compile`` is to make a function available both at compile-time (so a macro can call it while expanding) and run-time (so it can be called like any other function)::

       (eval-and-compile
         (defn add [x y]
           (+ x y)))

       (defmacro m [x]
         (add x 2))

       (print (m 3))     ; prints 5
       (print (add 3 6)) ; prints 9

   Had the ``defn`` not been wrapped in ``eval-and-compile``, ``m`` wouldn't be able to call ``add``, because when the compiler was expanding ``(m 3)``, ``add`` wouldn't exist yet.

.. hy:function:: (eval-when-compile [#* body])

   As ``eval-and-compile``, but the code isn't executed at run-time, and ``None`` is returned. Hence, ``eval-when-compile`` doesn't directly contribute any code to the final program, although it can still change Hy's state while compiling (e.g., by defining a function). ::

       (eval-when-compile
         (defn add [x y]
           (+ x y)))

       (defmacro m [x]
         (add x 2))

       (print (m 3))     ; prints 5
       (print (add 3 6)) ; raises NameError: name 'add' is not defined

.. hy:function:: (lfor [#* args])

   The comprehension forms ``lfor``, :hy:func:`sfor`, :hy:func:`dfor`, :hy:func:`gfor`, and :hy:func:`for`
   are used to produce various kinds of loops, including Python-style
   :ref:`comprehensions <py:comprehensions>`. ``lfor`` in particular
   can create a list comprehension. A simple use of ``lfor`` is::

       (lfor  x (range 5)  (* 2 x))  ; => [0 2 4 6 8]

   ``x`` is the name of a new variable, which is bound to each element of
   ``(range 5)``. Each such element in turn is used to evaluate the value
   form ``(* 2 x)``, and the results are accumulated into a list.

   Here's a more complex example::

       (lfor
         x (range 3)
         y (range 3)
         :if (!= x y)
         :setv total (+ x y)
         [x y total])
       ; => [[0 1 1] [0 2 2] [1 0 1] [1 2 3] [2 0 2] [2 1 3]]

   When there are several iteration clauses (here, the pairs of forms ``x
   (range 3)`` and ``y (range 3)``), the result works like a nested loop or
   Cartesian product: all combinations are considered in lexicographic
   order.

   The general form of ``lfor`` is::

       (lfor CLAUSES VALUE)

   where the ``VALUE`` is an arbitrary form that is evaluated to produce
   each element of the result list, and ``CLAUSES`` is any number of
   clauses. There are several types of clauses:

   - Iteration clauses, which look like ``LVALUE ITERABLE``. The ``LVALUE``
     is usually just a symbol, but could be something more complicated,
     like ``[x y]``.
   - ``:async LVALUE ITERABLE``, which is an
     :ref:`asynchronous <py:async for>` form of iteration clause.
   - ``:do FORM``, which simply evaluates the ``FORM``. If you use
     ``(continue)`` or ``(break)`` here, they will apply to the innermost
     iteration clause before the ``:do``.
   - ``:setv LVALUE RVALUE``, which is equivalent to ``:do (setv LVALUE
     RVALUE)``.
   - ``:if CONDITION``, which is equivalent to ``:do (when (not CONDITION)
     (continue))``.

   For ``lfor``, ``sfor``, ``gfor``, and ``dfor``,  variables defined by
   an iteration clause or ``:setv`` are not visible outside the form.
   However, variables defined within the body, as with a ``setx``
   expression, will be visible outside the form.
   In ``for``, by contrast, iteration and ``:setv`` clauses share the
   caller's scope and are visible outside the form.

.. hy:function:: (dfor [#* args])

    ``dfor`` creates a :ref:`dictionary comprehension <py:dict>`. Its syntax
    is the same as that of :hy:func:`lfor` except that it takes two trailing
    arguments. The first is a form producing the key of each dictionary
    element, and the second produces the value. Thus::

        => (dfor  x (range 5)  x (* x 10))
        {0 0  1 10  2 20  3 30  4 40}


.. hy:function:: (gfor [#* args])

   ``gfor`` creates a :ref:`generator expression <py:genexpr>`. Its syntax
   is the same as that of :hy:func:`lfor`. The difference is that ``gfor`` returns
   an iterator, which evaluates and yields values one at a time::

       => (import itertools [count take-while])
       => (setv accum [])
       => (list (take-while
       ...  (fn [x] (< x 5))
       ...  (gfor x (count) :do (.append accum x) x)))
       [0 1 2 3 4]
       => accum
       [0 1 2 3 4 5]

.. hy:function:: (sfor [#* args])

   ``sfor`` creates a :ref:`set comprehension <py:set>`. ``(sfor CLAUSES VALUE)`` is
   equivalent to ``(set (lfor CLAUSES VALUE))``. See :hy:func:`lfor`.

.. hy:function:: (setv [#* args])

   ``setv`` compiles to an :ref:`assignment statement <py:assignment>` (see :hy:func:`setx` for assignment expressions), which sets the value of a variable or some other assignable expression. It requires an even number of arguments, and always returns ``None``. The most common case is two arguments, where the first is a symbol::

       (setv websites 103)
       (print websites)  ; => 103

   Additional pairs of arguments are equivalent to several two-argument ``setv`` calls, in the given order. Thus, the semantics are like Common Lisp's ``setf`` rather than ``psetf``. ::

       (setv  x 1  y x  x 2)
       (print x y)  ; => 2 1

   All the same kinds of complex assignment targets are allowed as in Python. So, you can use list assignment to assign in parallel. (As in Python, tuple and list syntax are equivalent for this purpose; Hy differs from Python merely in that its list syntax is shorter than its tuple syntax.) ::

       (setv [x y] [y x])  ; Swaps the values of `x` and `y`

   Unpacking assignment looks like this (see :hy:func:`unpack-iterable`)::

       (setv [letter1 letter2 #* others] "abcdefg")
       (print letter1 letter2 (hy.repr others))
         ; => a b ["c" "d" "e" "f" "g"]

   See :hy:func:`let` to simulate more traditionally Lispy block-level scoping.

.. hy:function:: (setx [target value])

   ``setx`` compiles to an assignment expression. Thus, unlike :hy:func:`setv`, it returns the assigned value. It takes exactly two arguments, and the target must be a bare symbol. Python 3.8 or later is required. ::

     (when (> (setx x (+ 1 2)) 0)
       (print x "is greater than 0"))
         ; => 3 is greater than 0

.. hy:function:: (let [bindings #* body])

   ``let`` creates lexically-scoped names for local variables. This form takes a
   list of binding pairs followed by a *body* which gets executed. A let-bound
   name ceases to refer to that local outside the ``let`` form, but arguments in
   nested functions and bindings in nested ``let`` forms can shadow these names.


   :strong:`Examples`

   ::

       => (let [x 5   ; creates new local bound names 'x and 'y
                y 6]
       ...  (print x y)
       ...  (let [x 7]  ; new local and name binding that shadows 'x
       ...    (print x y))
       ...  (print x y))  ; 'x refers to the first local again
       5 6
       7 6
       5 6

   ``let`` can also bind names using
   Python's `extended iterable unpacking`_ syntax to destructure iterables::

       => (let [[head #* tail] #(0 1 2)]
       ...   [head tail])
       [0 [1 2]]

   Basic assignments (e.g. ``setv``, ``+=``) will update the local
   variable named by a let binding when they assign to a let-bound name.
   But assignments via ``import`` are always hoisted to normal Python
   scope, and likewise, ``defn`` or ``defclass`` will assign the
   function or class in the Python scope, even if it shares the name of
   a let binding. To avoid this hoisting, use
   ``importlib.import_module``, ``fn``, or ``type`` (or whatever
   metaclass) instead.

   If ``lfor``, ``sfor``, ``dfor``, or ``gfor`` (but not ``for``) is in
   the body of a ``let``, assignments in iteration clauses and ``:setv``
   clauses will create a new variable in the comprehenion form's own
   scope, without touching any outer let-bound variable of the same
   name.

   Like the ``let*`` of many other Lisps, ``let`` executes the variable
   assignments one-by-one, in the order written::

       => (let [x 5
       ...       y (+ x 1)]
       ...   (print x y))
       5 6

       => (let [x 1
       ...      x (fn [] x)]
       ...   (x))
       1

   Note that let-bound variables continue to exist in the surrounding
   Python scope. As such, ``let``-bound objects may not be eligible for
   garbage collection as soon as the ``let`` ends. To ensure there are
   no references to ``let``-bound objects as soon as possible, use
   ``del`` at the end of the ``let``, or wrap the ``let`` in a function.

   .. _extended iterable unpacking: https://www.python.org/dev/peps/pep-3132/#specification


.. hy:function:: (match [subject #* cases])

   The ``match`` form creates a :ref:`match statement <py3_10:match>`. It
   requires Python 3.10 or later. The first argument should be the subject,
   and any remaining arguments should be pairs of patterns and results. The
   ``match`` form returns the value of the corresponding result, or
   ``None`` if no case matched. ::

       (match (+ 1 1)
         1 "one"
         2 "two"
         3 "three")
       ; => "two"

   You can use :hy:func:`do` to build a complex result form. Patterns, as
   in Python match statements, are interpreted specially and can't be
   arbitrary forms. Use ``(| …)`` for OR patterns, ``PATTERN :as NAME`` for
   AS patterns, and syntax like the usual Hy syntax for literal, capture,
   value, sequence, mapping, and class patterns. Guards are specified
   with ``:if FORM``. Here's a more complex example::

       (match #(100 200)
         [100 300]               "Case 1"
         [100 200] :if flag      "Case 2"
         [900   y]               f"Case 3, y: {y}"
         [100 (| 100 200) :as y] f"Case 4, y: {y}"
         _                       "Case 5, I match anything!")

   This will match case 2 if ``flag`` is true and case 4 otherwise.

   ``match`` can also match against class instances by keyword (or
   positionally if its ``__match_args__`` attribute is defined; see :pep:`636`)::

      (import  dataclasses [dataclass])
      (defclass [dataclass] Point []
        #^int x
        #^int y)
      (match (Point 1 2)
        (Point 1 x) :if (= (% x 2) 0) x)  ; => 2

   It's worth emphasizing that ``match`` is a pattern-matching construct
   rather than a generic `switch
   <https://en.wikipedia.org/wiki/Switch_statement>`_ construct, and
   retains all of Python's limitations on match patterns. For example, you
   can't match against the value of a variable. For more flexible branching
   constructs, see Hyrule's :hy:func:`branch <hyrule.control.branch>` and
   :hy:func:`case <hyrule.control.case>`, or simply use :hy:func:`cond
   <hy.core.macros.cond>`.

.. hy:function:: (defclass [arg1 #* args])

   ``defclass`` compiles to a :py:keyword:`class` statement, which creates a
   new class. It always returns ``None``. Only one argument, specifying the
   name of the new class as a symbol, is required. A list of :term:`decorators
   <py:decorator>` may be provided before the class name. After the name comes
   a list of superclasses (use the empty list ``[]`` for the typical case of no
   superclasses) and any number of body forms, the first of which may be a
   :term:`py:docstring`. ::

      (defclass [decorator1 decorator2] MyClass [SuperClass1 SuperClass2]
        "A class that does things at times."

        (setv
          attribute1 value1
          attribute2 value2)

        (defn method1 [self arg1 arg2]
          …)

        (defn method2 [self arg1 arg2]
          …))

.. hy:function:: (del [#* args])

   ``del`` compiles to a :py:keyword:`del` statement, which deletes variables
   or other assignable expressions. It always returns ``None``. ::

     (del  foo  (get mydict "mykey")  myobj.myattr)

.. hy:function:: (nonlocal [sym #* syms])

   As :hy:func:`global`, but the result is a :py:keyword:`nonlocal` statement.

.. hy:function:: (py [string])

   ``py`` parses the given Python code at compile-time and inserts the result into
   the generated abstract syntax tree. Thus, you can mix Python code into a Hy
   program. Only a Python expression is allowed, not statements; use
   :hy:func:`pys <pys>` if you want to use Python statements. The value of the
   expression is returned from the ``py`` form. ::

       (print "A result from Python:" (py "'hello' + 'world'"))

   The code must be given as a single string literal, but you can still use
   macros, :hy:func:`hy.eval <hy.eval>`, and related tools to construct the ``py`` form. If
   having to backslash-escape internal double quotes is getting you down, try a
   :ref:`bracket string <bracket-strings>`. If you want to evaluate some Python
   code that's only defined at run-time, try the standard Python function
   :func:`eval`.

   Python code need not syntactically round-trip if you use ``hy2py`` on a Hy
   program that uses ``py`` or ``pys``. For example, comments will be removed.


   .. _pys-specialform:

.. hy:function:: (pys [string])

   As :hy:func:`py <py>`, but the code can consist of zero or more statements,
   including compound statements such as ``for`` and ``def``. ``pys`` always
   returns ``None``. ::

       (pys "myvar = 5")
       (print "myvar is" myvar)

   The code string is dedented with :func:`textwrap.dedent` before parsing,
   which allows you to indent the code to match the surrounding Hy code when
   Python would otherwise forbid this, but beware that significant leading
   whitespace in embedded string literals will be removed.

.. hy:function:: (quasiquote [form])

   ``quasiquote`` allows you to quote a form, but also selectively evaluate
   expressions. Expressions inside a ``quasiquote`` can be selectively evaluated
   using ``unquote`` (``~``). The evaluated form can also be spliced using
   ``unquote-splice`` (``~@``). Quasiquote can be also written using the backquote
   (`````) symbol.

   :strong:`Examples`

   ::

       ;; let `qux' be a variable with value (bar baz)
       `(foo ~qux)
       ; equivalent to '(foo (bar baz))
       `(foo ~@qux)
       ; equivalent to '(foo bar baz)


.. hy:function:: (quote [form])

   ``quote`` returns the form passed to it without evaluating it. ``quote`` can
   alternatively be written using the apostrophe (``'``) symbol.

   :strong:`Examples`

   ::

       => (setv x '(print "Hello World"))
       => x  ; variable x is set to unevaluated expression
       hy.models.Expression([
         hy.models.Symbol('print'),
         hy.models.String('Hello World')])
       => (hy.eval x)
       Hello World


.. hy:function:: (require [#* args])

   ``require`` is used to import macros and reader macros from one or more given
   modules. It allows parameters in all the same formats as ``import``.
   ``require`` imports each named module and then makes each requested macro
   available in the current module.

   The following are all equivalent ways to call a macro named ``foo`` in the
   module ``mymodule``.

   :strong:`Examples`

   ::

       (require mymodule)
       (mymodule.foo 1)

       (require mymodule :as M)
       (M.foo 1)

       (require mymodule [foo])
       (foo 1)

       (require mymodule *)
       (foo 1)

       (require mymodule [foo :as bar])
       (bar 1)

   Reader macros are required using ``:readers [...]``.
   The ``:macros`` kwarg can be optionally added for readability::

       => (require mymodule :readers *)
       => (require mymodule :readers [!])
       => (require mymodule [foo] :readers [!])
       => (require mymodule :readers [!] [foo])
       => (require mymodule :macros [foo] :readers [!])

   Do note however, that requiring ``:readers``, but not specifying any regular
   macros, will not bring that module's macros in under their absolute paths::

       => (require mymodule :readers [!])
       => (mymodule.foo)
       Traceback (most recent call last):
         File "stdin-cd49eaaabebc174c87ebe6bf15f2f8a28660feba", line 1, in <module>
           (mymodule.foo)
       NameError: name 'mymodule' is not defined

   Unlike requiring regular macros, reader macros cannot be renamed
   with ``:as``, and are not made available under their absolute paths
   to their source module::

      => (require mymodule :readers [!])
      HySyntaxError: ...

      => (require mymodule :readers [! :as &])
      HySyntaxError: ...

      => (require mymodule)
      => mymodule.! x
      NameError: name 'mymodule' is not defined

   To define which macros are collected by ``(require mymodule *)``, set the
   variable ``_hy_export_macros`` (analogous to Python's ``__all__``) to a list
   of :ref:`mangled <mangling>` macro names, which is accomplished most
   conveniently with :hy:func:`export <hy.core.macros.export>`. The default
   behavior is to collect all macros other than those whose mangled names begin
   with an ASCII underscore (``_``).

   When requiring reader macros, ``(require mymodule :readers *)`` will collect
   all reader macros both defined and required within ``mymodule``.

   :strong:`Macros that call macros`

   One aspect of ``require`` that may be surprising is what happens when one
   macro's expansion calls another macro. Suppose ``mymodule.hy`` looks like this:

   ::

       (defmacro repexpr [n expr]
         ; Evaluate the expression n times
         ; and collect the results in a list.
         `(list (map (fn [_] ~expr) (range ~n))))

       (defmacro foo [n]
         `(repexpr ~n (input "Gimme some input: ")))

   And then, in your main program, you write:

   ::

       (require mymodule [foo])

       (print (mymodule.foo 3))

   Running this raises ``NameError: name 'repexpr' is not defined``, even though
   writing ``(print (foo 3))`` in ``mymodule`` works fine. The trouble is that your
   main program doesn't have the macro ``repexpr`` available, since it wasn't
   imported (and imported under exactly that name, as opposed to a qualified name).
   You could do ``(require mymodule *)`` or ``(require mymodule [foo repexpr])``,
   but a less error-prone approach is to change the definition of
   ``foo`` to require whatever sub-macros it needs:

   ::

       (defmacro foo [n]
         `(do
           (require mymodule)
           (mymodule.repexpr ~n (input "Gimme some input: "))))

   It's wise to use ``(require mymodule)`` here rather than ``(require mymodule
   [repexpr])`` to avoid accidentally shadowing a function named ``repexpr`` in
   the main program.

   .. note::

      :strong:`Qualified macro names`

      Note that in the current implementation, there's a trick in qualified macro
      names, like ``mymodule.foo`` and ``M.foo`` in the above example. These names
      aren't actually attributes of module objects; they're just identifiers with
      periods in them. In fact, ``mymodule`` and ``M`` aren't defined by these
      ``require`` forms, even at compile-time. None of this will hurt you unless try
      to do introspection of the current module's set of defined macros, which isn't
      really supported anyway.

.. hy:function:: (return [object])

   ``return`` compiles to a :py:keyword:`return` statement. It exits the
   current function, returning its argument if provided with one, or
   ``None`` if not. ::

       (defn f [x]
         (for [n (range 10)]
           (when (> n x)
             (return n))))
       (f 3.9)  ; => 4

   Note that in Hy, ``return`` is necessary much less often than in Python,
   since the last form of a function is returned automatically. Hence, an
   explicit ``return`` is only necessary to exit a function early. To force
   Python's behavior of returning ``None`` when execution reaches the end of a
   function, you can put ``None`` there yourself::

       (defn f [x]
         (setv y 10)
         (print (+ x y))
         None)
       (print (f 4))  ; Prints "14" and then "None"

.. hy:function:: (cut [coll [start None] [stop None] [step None])

   ``cut`` can be used to take a subset of a list and create a new list from it.
   The form takes at least one parameter specifying the list to cut. Two
   optional parameters can be used to give the start and end position of the
   subset. If only one is given, it is taken as the ``stop`` value.
   The third optional parameter is used to control the step stride between the elements.

   ``cut`` follows the same rules as its Python counterpart. Negative indices are
   counted starting from the end of the list. Some example usage:

   :strong:`Examples`

   ::

       => (setv collection (range 10))
       => (cut collection)
       [0 1 2 3 4 5 6 7 8 9]

       => (cut collection 5)
       [0 1 2 3 4]

       => (cut collection 2 8)
       [2 3 4 5 6 7]

       => (cut collection 2 8 2)
       [2 4 6]

       => (cut collection -4 -2)
       [6 7]

.. hy:function:: (raise [[exception None]])

   The ``raise`` form can be used to raise an ``Exception`` at
   runtime. Example usage:

   :strong:`Examples`

   ::

       (raise)
       ; re-rase the last exception

       (raise IOError)
       ; raise an IOError

       (raise (IOError "foobar"))
       ; raise an IOError("foobar")


   ``raise`` can accept a single argument (an ``Exception`` class or instance)
   or no arguments to re-raise the last ``Exception``.


.. hy:function:: (try [#* body])

   ``try`` compiles to a :py:keyword:`try` statement, which can catch
   exceptions and run cleanup actions. It begins with any number of body forms.
   Then follows any number of ``except`` or ``except*`` (:pep:`654`) forms,
   which are expressions that begin with the symbol in question, followed by a
   list of exception types, followed by more body forms. Finally there are an
   optional ``else`` form and an optional ``finally`` form, which again are
   expressions that begin with the symbol in question and then comprise body
   forms. As in Python, at least one of ``except``, ``except*``, or ``finally``
   is required; ``else`` is only allowed if at least one ``except`` or
   ``except*`` is provided; ``except*`` requires Python 3.11; and ``except``
   and ``except*`` may not both be used in the same ``try``.

   Here's an example of several of the allowed kinds of child forms::

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

   Exception lists can be in any of several formats:

   - ``[]`` to catch any subtype of ``Exception``, like Python's ``except:``
   - ``[ETYPE]`` to catch only the single type ``ETYPE``, like Python's
     ```except ETYPE:``
   - ``[[ETYPE1 ETYPE2 …]]`` to catch any of the named types, like Python's
     ``except ETYPE1, ETYPE2, …:``
   - ``[VAR ETYPE]`` to catch ``ETYPE`` and bind it to ``VAR``, like Python's
     ``except ETYPE as VAR:``
   - ``[VAR [ETYPE1 ETYPE2 …]]`` to catch any of the named types and bind it to
     ``VAR``, like Python's ``except ETYPE1, ETYPE2, … as VAR:``

   The return value of ``try`` is the last form evaluated among the main body,
   ``except`` forms, ``except*`` forms, and ``else``.

.. hy:function:: (unpack-iterable)
.. hy:function:: (unpack-mapping)

   (Also known as the splat operator, star operator, argument expansion, argument
   explosion, argument gathering, and varargs, among others...)

   ``unpack-iterable`` and ``unpack-mapping`` allow an iterable or mapping
   object (respectively) to provide positional or keywords arguments
   (respectively) to a function.

   ::

       => (defn f [a b c d] [a b c d])
       => (f (unpack-iterable [1 2]) (unpack-mapping {"c" 3 "d" 4}))
       [1 2 3 4]

   ``unpack-iterable`` is usually written with the shorthand ``#*``, and
   ``unpack-mapping`` with ``#**``.

   ::

       => (f #* [1 2] #** {"c" 3 "d" 4})
       [1 2 3 4]

   Unpacking is allowed in a variety of contexts, and you can unpack
   more than once in one expression (:pep:`3132`, :pep:`448`).

   ::

       => (setv [a #* b c] [1 2 3 4 5])
       => [a b c]
       [1 [2 3 4] 5]
       => [#* [1 2] #* [3 4]]
       [1 2 3 4]
       => {#** {1 2} #** {3 4}}
       {1 2  3 4}
       => (f #* [1] #* [2] #** {"c" 3} #** {"d" 4})
       [1 2  3 4]

.. hy:function:: (unquote [symbol])

   Within a quasiquoted form, ``unquote`` forces evaluation of a symbol. ``unquote``
   is aliased to the tilde (``~``) symbol.

   ::

       => (setv nickname "Cuddles")
       => (quasiquote (= nickname (unquote nickname)))
       '(= nickname "Cuddles")
       => `(= nickname ~nickname)
       '(= nickname "Cuddles")


.. hy:function:: (unquote-splice [symbol])

   ``unquote-splice`` forces the evaluation of a symbol within a quasiquoted form,
   much like ``unquote``. ``unquote-splice`` can be used when the symbol
   being unquoted contains an iterable value, as it "splices" that iterable into
   the quasiquoted form. ``unquote-splice`` can also be used when the value
   evaluates to a false value such as ``None``, ``False``, or ``0``, in which
   case the value is treated as an empty list and thus does not splice anything
   into the form. ``unquote-splice`` is aliased to the ``~@`` syntax.

   ::

       => (setv nums [1 2 3 4])
       => (quasiquote (+ (unquote-splice nums)))
       '(+ 1 2 3 4)
       => `(+ ~@nums)
       '(+ 1 2 3 4)
       => `[1 2 ~@(when (< (get nums 0) 0) nums)]
       '[1 2]

   Here, the last example evaluates to ``('+' 1 2)``, since the condition
   ``(< (nth nums 0) 0)`` is ``False``, which makes this ``if`` expression
   evaluate to ``None``, because the ``if`` expression here does not have an
   else clause. ``unquote-splice`` then evaluates this as an empty value,
   leaving no effects on the list it is enclosed in, therefore resulting in
   ``('+' 1 2)``.

   A symbol name can begin with ``@`` in Hy, but ``~@`` takes precedence in the
   parser. So, if you want to unquote the symbol ``@foo`` with ``~``, you must
   use whitespace to separate ``~`` and ``@``, as in ``~ @foo``.

.. hy:function:: (while [condition #* body])

   ``while`` compiles to a :py:keyword:`while` statement. It is used to execute a
   set of forms as long as a condition is met. The first argument to ``while`` is
   the condition, and any remaining forms constitute the body. The following
   example will output "Hello world!" to the screen indefinitely:

   ::

       (while True (print "Hello world!"))

   The last form of a ``while`` loop can be an ``else`` clause, which is executed
   after the loop terminates, unless it exited abnormally (e.g., with ``break``). So,

   ::

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

   ::

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

.. hy:function:: (with [#* args])

  Wrap execution of `body` within a context manager given as bracket `args`.
  ``with`` is used to wrap the execution of a block within a context manager. The
  context manager can then set up the local system and tear it down in a controlled
  manner. The archetypical example of using ``with`` is when processing files.
  If only a single expression is supplied, or the argument is `_`, then no
  variable is bound to the expression, as shown below.

  Examples:
    ::

       => (with [arg (expr)] block)
       => (with [(expr)] block)
       => (with [arg1 (expr1)  _ (expr2)  arg3 (expr3)] block)

  The following example will open the ``NEWS`` file and print its content to the
  screen. The file is automatically closed after it has been processed::

       => (with [f (open \"NEWS\")] (print (.read f)))

  ``with`` returns the value of its last form, unless it suppresses an exception
  (because the context manager's ``__exit__`` method returned true), in which
  case it returns ``None``. So, the previous example could also be written::

       => (print (with [f (open \"NEWS\")] (.read f)))

.. hy:function:: (with/a [#* args])

  Wrap execution of `body` within a context manager given as bracket `args`.
  ``with/a`` behaves like ``with``, but is used to wrap the execution of a block
  within an asynchronous context manager. The context manager can then set up
  the local system and tear it down in a controlled manner asynchronously.
  Examples:

    ::
       => (with/a [arg (expr)] block)
       => (with/a [(expr)] block)
       => (with/a [_ (expr)  arg (expr)  _ (expr)] block)

  .. note::
    ``with/a`` returns the value of its last form, unless it suppresses an exception
    (because the context manager's ``__aexit__`` method returned true), in which
    case it returns ``None``.

.. hy:function:: (yield [object])

   ``yield`` is used to create a generator object that returns one or more values.
   The generator is iterable and therefore can be used in loops, list
   comprehensions and other similar constructs.

   The function ``random-numbers`` shows how generators can be used to generate
   infinite series without consuming infinite amount of memory.

   :strong:`Examples`

   ::

       => (defn multiply [bases coefficients]
       ...  (for [#(base coefficient) (zip bases coefficients)]
       ...   (yield (* base coefficient))))

       => (multiply (range 5) (range 5))
       <generator object multiply at 0x978d8ec>

       => (list (multiply (range 10) (range 10)))
       [0 1 4 9 16 25 36 49 64 81]

       => (import random)
       => (defn random-numbers [low high]
       ...  (while True (yield (.randint random low high))))
       => (list (take 15 (random-numbers 1 50)))
       [7 41 6 22 32 17 5 38 18 38 17 14 23 23 19]


.. hy:function:: (yield-from [object])

   ``yield-from`` is used to call a subgenerator.  This is useful if you
   want your coroutine to be able to delegate its processes to another
   coroutine, say, if using something fancy like
   `asyncio <https://docs.python.org/3.4/library/asyncio.html>`_.

.. hy:function:: (pragma)

  ``pragma`` is reserved as a core macro name for future use, especially for
  allowing backwards-compatible addition of new features after the release of Hy
  1.0. Currently, trying to use ``pragma`` is an error.

.. hy:automodule:: hy.core.macros
   :members:
   :macros:
   :tags:

Placeholder macros
~~~~~~~~~~~~~~~~~~

There are a few core macros that are unusual in that all they do, when
expanded, is crash, regardless of their arguments:

- ``else``
- ``except``
- ``except*``
- ``finally``
- ``unpack-mapping``
- ``unquote``
- ``unquote-splice``

The purpose of these macros is merely to reserve their names. Each
symbol is interpreted specially by one or more other core macros
(e.g., ``else`` in ``while``) and thus, in these contexts, any
definition of these names as a function or macro would be ignored. If
you really want to, you can override these names like any others, but
beware that, for example, trying to call your new ``else`` inside
``while`` may not work.

Hy
---

The ``hy`` module is auto imported into every Hy module and provides convient access to
the following methods

.. hy:autofunction:: hy.read

.. hy:autofunction:: hy.read_many

.. hy:autofunction:: hy.eval

.. hy:autofunction:: hy.repr

.. hy:autofunction:: hy.repr-register

.. hy:autofunction:: hy.mangle

.. hy:autofunction:: hy.unmangle

.. hy:autofunction:: hy.disassemble

.. hy:autofunction:: hy.macroexpand

.. hy:autofunction:: hy.macroexpand-1

.. hy:autofunction:: hy.gensym

.. hy:autofunction:: hy.as-model

.. hy:data:: hy.errors.COLORED

   This variable is initially :py:data:`False`. If it's set to a true value, Hy
   will color its error messages with ``colorama``.

.. _reader-macros:

Reader Macros
-------------

Like regular macros, reader macros should return a Hy form that will then be
passed to the compiler for execution. Reader macros access the Hy reader using
the ``&reader`` name. It gives access to all of the text- and form-parsing logic
that Hy uses to parse itself. See :py:class:`HyReader <hy.reader.hy_reader.HyReader>` and
its base class :py:class:`Reader <hy.reader.reader.Reader>` for details regarding
the available processing methods.

.. autoclass:: hy.reader.hy_reader.HyReader
   :members: parse, parse_one_form, parse_forms_until, read_default, fill_pos

.. autoclass:: hy.reader.reader.Reader
   :members:

Python Operators
----------------

.. hy:automodule:: hy.pyops
   :members:

Reserved
--------

.. hy:automodule:: hy.reserved
   :members:
