==========
Profile
==========

.. versionadded:: 0.10.0

The ``profile`` macros make it easier to find bottlenecks.


Macros
======

.. _profile/calls:
.. _profile/cpu:

profile/calls
--------------

``profile/calls`` allows you to create a call graph visualization. 
**Note:** You must have `Graphviz <http://www.graphviz.org/Home.php>`_
installed for this to work.


Usage: `(profile/calls (body))` 

Example:

.. code-block:: hy

   (require [hy.contrib.profile [profile/calls]])
   (profile/calls (print "hey there"))


profile/cpu
------------

``profile/cpu`` allows you to profile a bit of code.

Usage: `(profile/cpu (body))`

Example:

.. code-block:: hy

    (require [hy.contrib.profile [profile/cpu]])
    (profile/cpu (print "hey there"))

.. code-block:: bash

   hey there
   <pstats.Stats instance at 0x14ff320>
            2 function calls in 0.000 seconds
   
    Random listing order was used
    
    ncalls  tottime  percall  cumtime  percall filename:lineno(function)        1    0.000    0.000    0.000    0.000 {method 'disable' of '_lsprof.Profiler' objects}
        1    0.000    0.000    0.000    0.000 {print}
