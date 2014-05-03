;;; Hy profiling macros
;;
;; Copyright (c) 2013 Paul R. Tagliamonte <tag@pault.ag>
;;
;; Permission is hereby granted, free of charge, to any person obtaining a
;; copy of this software and associated documentation files (the "Software"),
;; to deal in the Software without restriction, including without limitation
;; the rights to use, copy, modify, merge, publish, distribute, sublicense,
;; and/or sell copies of the Software, and to permit persons to whom the
;; Software is furnished to do so, subject to the following conditions:
;;
;; The above copyright notice and this permission notice shall be included in
;; all copies or substantial portions of the Software.
;;
;; THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
;; IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
;; FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
;; THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
;; LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
;; FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
;; DEALINGS IN THE SOFTWARE.
;;
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
