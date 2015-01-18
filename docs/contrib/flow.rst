==========
Flow
==========

.. versionadded:: 0.10.1

The ``flow`` macros allow a programmer to direct the flow of his program with
greater ease.
   
   
Macros
======

.. _case:
.. _switch:

case
-----

``case`` allows you to decide based on the value of a variable.


Usage: `(case variable val1 (body1) val2 (body2) ...)`

Example:

.. code-block:: hy

    (require hy.contrib.flow)
                
    (defn bmi-commenter [bmi]
        (case bmi
            10 (print "The bmi was 10, wow.")
            20 (print "20? Really?")
            30 (print "Was it 30? Ok...")
               (print  "I don't even know.")))

    
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
            (<= 30.0) (print "a little too heavy, but ok")
                      (print  "You are a whale!")))
    
