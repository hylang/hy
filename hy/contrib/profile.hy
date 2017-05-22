;;; Hy profiling macros
;;; These macros make debugging where bottlenecks exist easier.


(defmacro profile/calls [&rest body]
  `(do
     (import [pycallgraph [PyCallGraph]]
             [pycallgraph.output [GraphvizOutput]])
     (with* [(apply PyCallGraph [] {"output" (GraphvizOutput)})]
           ~@body)))


(defmacro/g! profile/cpu [&rest body]
  " Profile a bit of code "
  `(do
     (import cProfile pstats)

     (if-python2
       (import [StringIO [StringIO]])
       (import [io [StringIO]]))

     (setv ~g!hy-pr (.Profile cProfile))
     (.enable ~g!hy-pr)
     (do ~@body)
     (.disable ~g!hy-pr)
     (setv ~g!hy-s (StringIO))
     (setv ~g!hy-ps
           (.sort-stats (apply pstats.Stats [~g!hy-pr] {"stream" ~g!hy-s})))
     (.print-stats ~g!hy-ps)
     (print (.getvalue ~g!hy-s))))
