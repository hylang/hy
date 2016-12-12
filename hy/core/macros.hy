;;; Hy core macros
;;
;; Copyright (c) 2013 Nicolas Dandrimont <nicolas.dandrimont@crans.org>
;; Copyright (c) 2013 Paul Tagliamonte <paultag@debian.org>
;; Copyright (c) 2013 Konrad Hinsen <konrad.hinsen@fastmail.net>
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
;;; These macros form the hy language
;;; They are automatically required in every module, except inside hy.core


(import [hy.models.list [HyList]]
        [hy.models.symbol [HySymbol]]
        [hy._compat [PY33 PY34]])

(defmacro as-> [head name &rest rest]
  "Expands to sequence of assignments to the provided name, starting with head.
  The previous result is thus available in the subsequent form. Returns the
  final result, and leaves the name bound to it in the local scope. This behaves
  much like the other threading macros, but requires you to specify the threading
  point per form via the name instead of always the first or last argument."
  `(do (setv
         ~name ~head
         ~@(interleave (repeat name) rest))
     ~name))

(defmacro with [args &rest body]
  "shorthand for nested with* loops:
  (with [x foo y bar] baz) ->
  (with* [x foo]
    (with* [y bar]
      baz))"

  (if (not (empty? args))
    (do
     (if (>= (len args) 2)
       (do
        (setv p1 (.pop args 0)
              p2 (.pop args 0)
              primary [p1 p2])
        `(with* [~@primary] (with ~args ~@body)))
       `(with* [~@args] ~@body)))
    `(do ~@body)))


(defmacro car [thing]
  "Get the first element of a list/cons"
  `(get ~thing 0))


(defmacro cdr [thing]
  "Get all the elements of a thing, except the first"
  `(cut ~thing 1))


(defmacro cond [&rest branches]
  "shorthand for nested ifs:
   (cond [foo bar] [baz quux]) ->
   (if foo
     bar
     (if baz
       quux))"
  (if (empty? branches)
    None
    (do
     (setv branches (iter branches))
     (setv branch (next branches))
     (defn check-branch [branch]
       "check `cond` branch for validity, return the corresponding `if` expr"
       (if (not (= (type branch) HyList))
         (macro-error branch "cond branches need to be a list"))
       (if (< (len branch) 2)
         (macro-error branch "cond branches need at least two items: a test and one or more code branches"))
       (setv test (car branch))
       (setv thebranch (cdr branch))
       `(if ~test (do ~@thebranch)))

     (setv root (check-branch branch))
     (setv latest-branch root)

     (for* [branch branches]
       (setv cur-branch (check-branch branch))
       (.append latest-branch cur-branch)
       (setv latest-branch cur-branch))
     root)))


(defmacro for [args &rest body]
  "shorthand for nested for loops:
  (for [x foo
        y bar]
    baz) ->
  (for* [x foo]
    (for* [y bar]
      baz))"
  (setv body (list body))
  (if (empty? body)
    (macro-error None "`for' requires a body to evaluate"))
  (setv lst (get body -1))
  (setv belse (if (and (isinstance lst HyExpression) (= (get lst 0) "else"))
                [(body.pop)]
                []))
  (cond
   [(odd? (len args))
    (macro-error args "`for' requires an even number of args.")]
   [(empty? body)
    (macro-error None "`for' requires a body to evaluate")]
   [(empty? args) `(do ~@body ~@belse)]
   [(= (len args) 2) `(for* [~@args] (do ~@body) ~@belse)]
   [True
    (let [alist (cut args 0 None 2)]
      `(for* [(, ~@alist) (genexpr (, ~@alist) [~@args])] (do ~@body) ~@belse))]))


(defmacro -> [head &rest rest]
  "Threads the head through the rest of the forms. Inserts
   head as the second item in the first form of rest. If
   there are more forms, inserts the first form as the
   second item in the second form of rest, etc."
  (setv ret head)
  (for* [node rest]
    (if (not (isinstance node HyExpression))
      (setv node `(~node)))
    (.insert node 1 ret)
    (setv ret node))
  ret)


(defmacro doto [form &rest expressions]
  "Performs a sequence of potentially mutating actions
   on an initial object, returning the resulting object"
  (setv f (gensym))
  (defn build-form [expression]
    (if (isinstance expression HyExpression)
      `(~(first expression) ~f ~@(rest expression))
      `(~expression ~f)))
  `(let [~f ~form]
     ~@(map build-form expressions)
     ~f))

(defmacro ->> [head &rest rest]
  "Threads the head through the rest of the forms. Inserts
   head as the last item in the first form of rest. If there
   are more forms, inserts the first form as the last item
   in the second form of rest, etc."
  (setv ret head)
  (for* [node rest]
    (if (not (isinstance node HyExpression))
      (setv node `(~node)))
    (.append node ret)
    (setv ret node))
  ret)


(defmacro if-not [test not-branch &optional yes-branch]
  "Like `if`, but execute the first branch when the test fails"
  `(if* (not ~test) ~not-branch ~yes-branch))


(defmacro lif [&rest args]
  "Like `if`, but anything that is not None is considered true."
  (setv n (len args))
  (if* n
       (if* (= n 1)
            (get args 0)
            `(if* (is-not ~(get args 0) None)
                  ~(get args 1)
                  (lif ~@(cut args 2))))))


(defmacro lif-not [test not-branch &optional yes-branch]
  "Like `if-not`, but anything that is not None is considered true."
  `(if* (is ~test None) ~not-branch ~yes-branch))


(defmacro when [test &rest body]
  "Execute `body` when `test` is true"
  `(if ~test (do ~@body)))


(defmacro unless [test &rest body]
  "Execute `body` when `test` is false"
  `(if-not ~test (do ~@body)))


(defmacro with-gensyms [args &rest body]
  (setv syms [])
  (for* [arg args]
    (.extend syms `[~arg (gensym '~arg)]))
  `(let ~syms
     ~@body))

(defmacro defmacro/g! [name args &rest body]
  (let [syms (list
              (distinct
               (filter (fn [x]
                         (and (hasattr x "startswith")
                              (.startswith x "g!")))
                       (flatten body))))
        gensyms []]
    (for* [sym syms]
      (.extend gensyms `[~sym (gensym (cut '~sym 2))]))
    `(defmacro ~name [~@args]
       (let ~gensyms
         ~@body))))

(defmacro defmacro! [name args &rest body]
  "Like defmacro/g! plus automatic once-only evaluation for o!
   parameters, which are available as the equivalent g! symbol."
  (setv os (list-comp s [s args] (.startswith s "o!"))
        gs (list-comp (HySymbol (+ "g!" (cut s 2))) [s os]))
  `(defmacro/g! ~name ~args
     `(do (setv ~@(interleave ~gs ~os))
          ~@~body)))

(if-python2
  (defmacro/g! yield-from [expr]
    `(do (import types)
         (setv ~g!iter (iter ~expr))
         (setv ~g!return None)
         (setv ~g!message None)
         (while True
           (try (if (isinstance ~g!iter types.GeneratorType)
                  (setv ~g!message (yield (.send ~g!iter ~g!message)))
                  (setv ~g!message (yield (next ~g!iter))))
           (except [~g!e StopIteration]
             (do (setv ~g!return (if (hasattr ~g!e "value")
                                     (. ~g!e value)
                                     None))
               (break)))))
           ~g!return))
  None)


(defmacro defmain [args &rest body]
  "Write a function named \"main\" and do the if __main__ dance"
  (let [retval (gensym)
        mainfn `(fn [~@args]
                  ~@body)]
    `(when (= --name-- "__main__")
       (import sys)
       (setv ~retval (apply ~mainfn sys.argv))
       (if (integer? ~retval)
         (sys.exit ~retval)))))


(defreader @ [expr]
  (let [decorators (cut expr None -1)
        fndef (get expr -1)]
    `(with-decorator ~@decorators ~fndef)))
