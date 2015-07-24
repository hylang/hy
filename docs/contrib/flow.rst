==========
Flow
==========

.. versionadded:: 0.10.1

The ``flow`` macros allow directing the flow of a program with greater ease.


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

    (defn temp-commenter [temp]
        (case temp
            -10 (print "It's freezing. Turn up the thermostat!")
            15 (print "Sounds about average.")
            45 (print "Holy smokes. It's hot in here!")
               (print  "I don't even know.")))


switch
-----

``switch`` allows you to run code based on the value of a variable.
A final extra body allows for a default case.


Usage: `(switch var (cond1) (body1) (cond2) (body2) ... )`

Example:

.. code-block:: hy

    (require hy.contrib.flow)

    (defn temp-commenter [temp]
        (switch temp
            (<= 10.0) (print "Better wear a jacket!")
            (<= 25.0) (print "Brace yourselves. Summer is coming!")
            (<= 30.0) (print "Time to get some ice cream.")
                      (print "Sounds like a heat wave")))
