==========
Quickstart
==========

.. image:: _static/cuddles-transparent-small.png
   :alt: Karen Rustard's Cuddles

(Thanks to Karen Rustad for Cuddles!)


**HOW TO GET HY REAL FAST**:

1. Create a `Virtual Python Environment
   <https://pypi.python.org/pypi/virtualenv>`_.
2. Activate your Virtual Python Environment.
3. Install `hy from GitHub <https://github.com/hylang/hy>`_ with ``$ pip install git+https://github.com/hylang/hy.git``.
4. Start a REPL with ``hy``.
5. Type stuff in the REPL::

       => (print "Hy!")
       Hy!
       => (defn salutationsnm [name] (print (+ "Hy " name "!")))
       => (salutationsnm "YourName")
       Hy YourName!

       etc

6. Hit CTRL-D when you're done.

*OMG! That's amazing! I want to write a Hy program.*

7. Open up an elite programming editor and type::

       #! /usr/bin/env hy
       (print "I was going to code in Python syntax, but then I got Hy.")

8. Save as ``awesome.hy``.
9. Make it executable::

        chmod +x awesome.hy

10. And run your first Hy program::

        ./awesome.hy

11. Take a deep breath so as to not hyperventilate.
12. Smile villainously and sneak off to your hydeaway and do
    unspeakable things.
