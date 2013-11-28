;;; Hy core macros
;;
;; Copyright (c) 2013 Nicolas Dandrimont <nicolas.dandrimont@crans.org>
;; Copyright (c) 2013 Paul Tagliamonte <paultag@debian.org>
;; Copyright (c) 2013 Konrad Hinsen <konrad.hinsen@fastmail.net>
;; Copyright (c) 2013 James King <james@agentultra.com>
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


(defmacro for [args &rest body]
  "shorthand for nested foreach loops:
  (for [x foo y bar] baz) ->
  (foreach [x foo]
    (foreach [y bar]
      baz))"
  ;; TODO: that signature sucks.
  ;; (for [[x foo] [y bar]] baz) would be more consistent
  (if (% (len args) 2)
    (macro-error args "for needs an even number of elements in its first argument"))
  (if args
    `(foreach [~(.pop args 0) ~(.pop args 0)] (for ~args ~@body))
    `(do ~@body)))


(defmacro-alias [car first] [thing]
  "Get the first element of a list/cons"
  `(get ~thing 0))


(defmacro-alias [cdr rest] [thing]
  "Get all the elements of a thing, except the first"
  `(slice ~thing 1))


(defmacro cond [&rest branches]
  "shorthand for nested ifs:
   (cond [foo bar] [baz quux]) ->
   (if foo
     bar
     (if baz
       quux))"
  (setv branches (iter branches))
  (setv branch (next branches))
  (defn check-branch [branch]
    "check `cond` branch for validity, return the corresponding `if` expr"
    (if (not (= (type branch) HyList))
      (macro-error branch "cond branches need to be a list"))
    (if (!= (len branch) 2)
      (macro-error branch "cond branches need two items: a test and a code branch"))
    (setv (, test thebranch) branch)
    `(if ~test ~thebranch))

  (setv root (check-branch branch))
  (setv latest-branch root)

  (foreach [branch branches]
    (setv cur-branch (check-branch branch))
    (.append latest-branch cur-branch)
    (setv latest-branch cur-branch))
  root)


(defmacro -> [head &rest rest]
  ;; TODO: fix the docstring by someone who understands this
  (setv ret head)
  (foreach [node rest]
    (if (not (isinstance node HyExpression))
      (setv node `(~node)))
    (.insert node 1 ret)
    (setv ret node))
  ret)


(defmacro ->> [head &rest rest]
  ;; TODO: fix the docstring by someone who understands this
  (setv ret head)
  (foreach [node rest]
    (if (not (isinstance node HyExpression))
      (setv node `(~node)))
    (.append node ret)
    (setv ret node))
  ret)


(defmacro when [test &rest body]
  "Execute `body` when `test` is true"
  `(if ~test (do ~@body)))


(defmacro unless [test &rest body]
  "Execute `body` when `test` is false"
  `(if ~test None (do ~@body)))


(defmacro yield-from [iterable]
  "Yield all the items from iterable"
  ;; TODO: this needs some gensym love
  `(foreach [_hy_yield_from_x ~iterable]
     (yield _hy_yield_from_x)))


(defmacro --each [lst &rest body]
  `(foreach [it ~list] ~@body))


(defmacro --each-while [lst pred &rest body]
  `(let [[p (lambda [it] ~pred)]]
     (foreach [it ~lst]
       (if (p it)
         ~@body
         (break)))))


(defmacro --map [form lst]
  `(let [[f (lambda [it] ~form)]]
     (foreach [v ~lst]
       (yield (f v)))))


(defmacro --map-when [pred rep lst]
  `(let [[p (lambda [it] ~pred)]
         [f (lambda [it] ~rep)]]
     (foreach [v ~lst]
       (if (p v)
         (yield (r v))
         (yield v)))))


(defmacro --filter [form lst]
  `(let [[pred (lambda [it] ~form)]]
     (foreach [val ~lst]
       (if (pred val)
         (yield val)))))
