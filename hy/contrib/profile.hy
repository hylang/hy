;;; Hy profiling macros
;; Copyright 2021 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

;;; These macros make debugging where bottlenecks exist easier.
"Hy Profiling macros

These macros make debugging where bottlenecks exist easier."


(defmacro profile/calls [#* body]
  "``profile/calls`` allows you to create a call graph visualization.
  **Note:** You must have `Graphviz <http://www.graphviz.org/>`_
  installed for this to work.

  Examples:
    ::

       => (require [hy.contrib.profile [profile/calls]])
       => (profile/calls (print \"hey there\"))
  "
  `(do
     (import [pycallgraph [PyCallGraph]]
             [pycallgraph.output [GraphvizOutput]])
     (with [(PyCallGraph :output (GraphvizOutput))]
           ~@body)))


(defmacro/g! profile/cpu [#* body]
  "Profile a bit of code

  Examples:
    ::

       => (require [hy.contrib.profile [profile/cpu]])
       => (profile/cpu (print \"hey there\"))

    .. code-block:: bash

      hey there
      <pstats.Stats instance at 0x14ff320>
                2 function calls in 0.000 seconds

        Random listing order was used

        ncalls  tottime  percall  cumtime  percall filename:lineno(function)        1    0.000    0.000    0.000    0.000 {method 'disable' of '_lsprof.Profiler' objects}
            1    0.000    0.000    0.000    0.000 {print}

  "
  `(do
     (import cProfile pstats)

     (import [io [StringIO]])

     (setv ~g!hy-pr (.Profile cProfile))
     (.enable ~g!hy-pr)
     (do ~@body)
     (.disable ~g!hy-pr)
     (setv ~g!hy-s (StringIO))
     (setv ~g!hy-ps
           (.sort-stats (pstats.Stats ~g!hy-pr :stream ~g!hy-s)))
     (.print-stats ~g!hy-ps)
     (print (.getvalue ~g!hy-s))))
