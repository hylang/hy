=====================
Hy <-> Python interop
=====================

   “Keep in mind we’re not Clojure. We’re not Common Lisp. We’re Homoiconic
   Python, with extra bits that make sense.” — Hy Style Guide

Despite being a Lisp, Hy aims to be fully compatible with Python. That means
every Python module or package can be imported in Hy code, and vice versa.

:ref:`Mangling <mangling>` allows variable names to be spelled differently in
Hy and Python. For example, Python's ``str.format_map`` can be written
``str.format-map`` in Hy, and a Hy function named ``valid?`` would be called
``is_valid`` in Python. In Python, you can import Hy's core functions
``mangle`` and ``unmangle`` directly from the ``hy`` package.

Using Python from Hy
====================

Using Python from Hy is nice and easy, you just have to :ref:`import` it.

If you have the following in ``greetings.py`` in Python::

    def greet(name):
        print("hello," name)

You can use it in Hy:

.. code-block:: clj

    (import greetings)
    (.greet greetings "foo") ; prints "hello, foo"

You can also import ``.pyc`` bytecode files, of course.

Using Hy from Python
====================

Suppose you have written some useful utilities in Hy, and you want to use them in
regular Python, or to share them with others as a package. Or suppose you work
with somebody else, who doesn't like Hy (!), and only uses Python.

In any case, you need to know how to use Hy from Python. Fear not, for it is
easy.

If you save the following in ``greetings.hy``:

.. code-block:: clj

    (setv *this-will-be-in-caps-and-underscores* "See?")
    (defn greet [name] (print "hello from hy," name))

Then you can use it directly from Python, by importing Hy before importing
the module. In Python::

    import hy
    import greetings

    greetings.greet("Foo") # prints "Hello from hy, Foo"
    print(THIS_WILL_BE_IN_CAPS_AND_UNDERSCORES) # prints "See?"

If you create a package with Hy code, and you do the ``import hy`` in
``__init__.py``, you can then directly include the package. Of course, Hy still
has to be installed.

Compiled files
--------------

You can also compile a module with ``hyc``, which gives you a ``.pyc`` file. You
can import that file. Hy does not *really* need to be installed ; however, if in
your code, you use any symbol from :doc:`core`, a corresponding ``import``
statement will be generated, and Hy will have to be installed.

Even if you do not use a Hy builtin, but just another function or variable with
the name of a Hy builtin, the ``import`` will be generated. For example, the previous code
causes the import of ``name`` from ``hy.core.language``.

**Bottom line: in most cases, Hy has to be installed.**

Launching a Hy REPL from Python
-------------------------------

You can use the function ``run_repl()`` to launch the Hy REPL from Python::

    >>> import hy.cmdline
    >>> hy.cmdline.run_repl()
    hy 0.12.1 using CPython(default) 3.6.0 on Linux
    => (defn foo [] (print "bar"))
    => (test)
    bar

If you want to print the Python code Hy generates for you, use the ``spy``
argument::

    >>> import hy.cmdline
    >>> hy.cmdline.run_repl(spy=True)
    hy 0.12.1 using CPython(default) 3.6.0 on Linux
    => (defn test [] (print "bar"))
    def test():
        return print('bar')
    => (test)
    test()
    bar

Evaluating strings of Hy code from Python
-----------------------------------------

Evaluating a string (or ``file`` object) containing a Hy expression requires
two separate steps. First, use the ``read_str`` function (or ``read`` for a
``file`` object) to turn the expression into a Hy model::

    >>> import hy
    >>> expr = hy.read_str("(- (/ (+ 1 3 88) 2) 8)")

Then, use the ``eval`` function to evaluate it::

    >>> hy.eval(expr)
    38.0
