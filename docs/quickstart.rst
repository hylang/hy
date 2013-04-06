==========
Quickstart
==========

I WANT TO BE DOING HY STUFF RIGHT NOW!

1. create a `Python virtual environment
   <https://pypi.python.org/pypi/virtualenv>`_
2. activate your Python virtual environment
3. ``pip install hy``
4. start a REPL with ``hy``
5. type stuff in the REPL::

       => (print "Hy!")
       Hy!
       => (defn salutationsnm [] (print (+ "Hy " name "!")))
       => (salutationsnm "YourName")
       Hy YourName!

       etc

6. hit CTRL-D when you're done

OMG! That's amazing! I want to write a hy program.

7. open up an elite programming editor
8. type::

       (print "hy is the BEST!")

9. save as ``test_program_of_awesome.hy``
10. run ``hy test_program_of_awesome.hy``
