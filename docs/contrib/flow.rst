==========
Flow
==========

.. versionadded:: 0.10.2

The ``flow`` macros allow a programmer to direct the flow of his program with
greater ease.
   
   
Macros
======

.. _guard:
.. _switch:

guard
-----

``guard`` allows you to guard against a condition.


Usage: `(guard (cond1) (body1) (cond2) (body2) ...)`

Example:

.. code-block:: hy

    (require hy.contrib.flow)
                
    (defn army-greeter [age height]
        (guard
            (< age 18) (print "You are too young!")
            (< height 170) (print "You are too small!")
            True        (print "Welcome aboard!")))

    
switch
-----

``switch`` allows you to run code based on the value of a variable.
A final extra body allows for a default case.


Usage: `(switch var (cond1) (body1) (cond2) (body2) ... )`

Example:

.. code-block:: hy

    (require hy.contrib.flow)
                
    (defn bmi-commenter [bmi]
        (switch bmi
            (<= 18.5) (print "you are underweight!")
            (<= 25.0) (print "apparently normal")
            (<= 30) (print "a little too heavy, but ok")
                     (print  "You are a whale!")))
    
