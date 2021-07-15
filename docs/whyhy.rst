=======
Why Hy?
=======

Hy is a multi-paradigm general-purpose programming language in the `Lisp family
<https://en.wikipedia.org/wiki/Lisp_(programming_language)>`_. It's implemented
as a kind of alternative syntax for Python. Compared to Python, Hy offers a
variety of extra features, generalizations, and syntactic simplifications, as
would be expected of a Lisp. Compared to other Lisps, Hy provides direct access
to Python's built-ins and third-party Python libraries, while allowing you to
freely mix imperative, functional, and object-oriented styles of programming.


Hy versus Python
----------------

The first thing a Python programmer will notice about Hy is that it has Lisp's
traditional parenthesis-heavy prefix syntax in place of Python's C-like infix
syntax. For example, ``print("The answer is", 2 + object.method(arg))`` could
be written ``(print "The answer is" (+ 2 (.method object arg)))`` in Hy.
Consequently, Hy is free-form: structure is indicated by parentheses rather
than whitespace, making it convenient for command-line use.

As in other Lisps, the value of a simplistic syntax is that it facilitates
Lisp's signature feature: `metaprogramming
<https://en.wikipedia.org/wiki/Metaprogramming>`_ through macros, which are
functions that manipulate code objects at compile time to produce new code
objects, which are then executed as if they had been part of the original code.
In fact, Hy allows arbitrary computation at compile-time. For example, here's a
simple macro that implements a C-style do-while loop, which executes its body
for as long as the condition is true, but at least once.

.. _do-while:

::

    (defmacro do-while [condition #* body]
      `(do
        ~body
        (while ~condition
          ~body)))

    (setv x 0)
    (do-while x
      (print "This line is executed once."))

Hy also removes Python's restrictions on mixing expressions and statements,
allowing for more direct and functional code. For example, Python doesn't allow
:ref:`with <py:with>` blocks, which close a resource once you're done using it,
to return values. They can only execute a set of statements:

.. code-block:: python

    with open("foo") as o:
       f1 = o.read()
    with open("bar") as o:
       f2 = o.read()
    print(len(f1) + len(f2))

In Hy, :ref:`with` returns the value of its last body form, so you can use it
like an ordinary function call::

   (print (+
     (len (with [o (open "foo")] (.read o)))
     (len (with [o (open "bar")] (.read o)))))

To be even more concise, you can put a ``with`` form in a :hy:func:`gfor <gfor>`::

   (print (sum (gfor
     filename ["foo" "bar"]
     (len (with [o (open filename)] (.read o))))))

Finally, Hy offers several generalizations to Python's binary operators.
Operators can be given more than two arguments (e.g., ``(+ 1 2 3)``), including
augmented assignment operators (e.g., ``(+= x 1 2 3)``). They are also provided
as ordinary first-class functions of the same name, allowing them to be passed
to higher-order functions: ``(sum xs)`` could be written ``(reduce + xs)``,
after importing the function ``+`` from the module ``hy.pyops``.

The Hy compiler works by reading Hy source code into Hy model objects and
compiling the Hy model objects into Python abstract syntax tree (:py:mod:`ast`)
objects. Python AST objects can then be compiled and run by Python itself,
byte-compiled for faster execution later, or rendered into Python source code.
You can even :ref:`mix Python and Hy code in the same project, or even the same
file,<interop>` which can be a good way to get your feet wet in Hy.


Hy versus other Lisps
---------------------

At run-time, Hy is essentially Python code. Thus, while Hy's design owes a lot
to `Clojure <https://clojure.org>`_, it is more tightly coupled to Python than
Clojure is to Java; a better analogy is `CoffeeScript's
<https://coffeescript.org>`_ relationship to JavaScript. Python's built-in
:ref:`functions <py:built-in-funcs>` and :ref:`data structures
<py:bltin-types>` are directly available::

    (print (int "deadbeef" :base 16))  ; 3735928559
    (print (len [1 10 100]))           ; 3

The same goes for third-party Python libraries from `PyPI <https://pypi.org>`_
and elsewhere. Here's a tiny `CherryPy <https://cherrypy.org>`_ web application
in Hy::

    (import cherrypy)

    (defclass HelloWorld []
      #@(cherrypy.expose (defn index [self]
        "Hello World!")))

    (cherrypy.quickstart (HelloWorld))

You can even run Hy on `PyPy <https://pypy.org>`_ for a particularly speedy
Lisp.

Like all Lisps, Hy is `homoiconic
<https://en.wikipedia.org/wiki/Homoiconicity>`_. Its syntax is represented not
with cons cells or with Python's basic data structures, but with simple
subclasses of Python's basic data structures called :ref:`models <models>`.
Using models in place of plain ``list``\s, ``set``\s, and so on has two
purposes: models can keep track of their line and column numbers for the
benefit of error messages, and models can represent syntactic features that the
corresponding primitive type can't, such as the order in which elements appear
in a set literal. However, models can be concatenated and indexed just like
plain lists, and you can return ordinary Python types from a macro or give them
to ``hy.eval`` and Hy will automatically promote them to models.

Hy takes much of its semantics from Python. For example, Hy is a Lisp-1 because
Python functions use the same namespace as objects that aren't functions. In
general, any Python code should be possible to literally translate to Hy. At
the same time, Hy goes to some lengths to allow you to do typical Lisp things
that aren't straightforward in Python. For example, Hy provides the
aforementioned mixing of statements and expressions, :ref:`name mangling
<mangling>` that transparently converts symbols with names like ``valid?`` to
Python-legal identifiers, and a :hy:func:`let <hy.contrib.walk.let>` macro to provide block-level scoping
in place of Python's usual function-level scoping.

Overall, Hy, like Common Lisp, is intended to be an unopinionated big-tent
language that lets you do what you want. If you're interested in a more
small-and-beautiful approach to Lisp, in the style of Scheme, check out
`Hissp <https://github.com/gilch/hissp>`_, another Lisp embedded in Python
that was created by a Hy developer.
