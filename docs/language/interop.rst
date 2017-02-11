=====================
Hy <-> Python interop
=====================

   “Keep in mind we’re not Clojure. We’re not Common Lisp. We’re Homoiconic
   Python, with extra bits that make sense.” — Hy Style Guide

Despite being a Lisp, Hy aims to be fully compatible with Python. That means
every Python module or package can be imported in Hy code, and vice versa.

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

A quick note about mangling
--------

In Python, snake_case is used by convention. Lisp dialects tend to use dashes
instead of underscores, so Hy does some magic to give you more pleasant names.

In the same way, ``UPPERCASE_NAMES`` from Python can be used ``*with-earmuffs*``
instead.

You can use either the original names or the new ones.

Imagine ``example.py``::

    def function_with_a_long_name():
        print(42)

    FOO = "bar"

Then, in Hy:

.. code-block:: clj

    (import example)
    (.function-with-a-long-name example) ; prints "42"
    (.function_with_a_long_name example) ; also prints "42"

    (print (. example *foo*)) ; prints "bar"
    (print (. example FOO))   ; also prints "bar"

.. warning::
   Mangling isn’t that simple; there is more to discuss about it, yet it doesn’t
   belong in this section.
.. TODO: link to mangling section, when it is done


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
    (defn greet [name] (Print "hello from hy," name))

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



