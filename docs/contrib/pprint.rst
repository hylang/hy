==================
Hy pretty printer
==================

``hy.contrib.pprint`` is a port of python's built-in ``pprint`` that can pretty
print objects using Hy syntax.

.. code-block:: hy

   => (pprint {:name "Adam" :favorite-foods #{:apple :pizza}
                :bio "something very important"}
        :width 20)
   {:name "Adam"
    :bio (+ "something "
            "very "
            "important")
    :favorite-foods #{:apple
                      :pizza}}

Hy ``pprint`` leverages ``hy-repr`` for much of it's pretty printing and
therefor can be exteneded to work with arbitrary types using
``hy-repr-register``. Like Python's ``pprint`` and ``hy-repr``, Hy ``pprint``
attempts to maintain round-trippability of it's input where possible. Unlike
Python, however, Hy does not have `string literal concatenation`_,
which is why strings and bytestrings are broken up using the form ``(+ ...)``.

.. _string literal concatenation: https://docs.python.org/3/reference/lexical_analysis.html#string-literal-concatenation

The API for Hy ``pprint`` is functionally identical to Python's ``pprint``
module, so be sure to reference the Python `pprint`_
docs for more on how to use the module's various methods and arguments.

.. _pprint: https://docs.python.org/3/library/pprint.html

The differences that do exist are as follows:

- ``isreadable`` becomes ``readable?``
- ``isrecursive`` becomes ``recursive?``
- Passing ``False`` to the ``PrettyPrinter`` arg ``sort-dicts`` in Python
  versions < 3.8 will raise a ``ValueError``
