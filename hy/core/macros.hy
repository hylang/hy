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


(defmacro with [args &rest body]
  "shorthand for nested for* loops:
  (with [[x foo] [y bar]] baz) ->
  (with* [x foo]
    (with* [y bar]
      baz))"

  (if (not (empty? args))
    (let [[primary (.pop args 0)]]
      (if (isinstance primary HyList)
        ;;; OK. if we have a list, we can go ahead and unpack that
        ;;; as the argument to with.
        `(with* [~@primary] (with ~args ~@body))
        ;;; OK, let's just give it away. This may not be something we
        ;;; can do, but that's really the programmer's problem.
        `(with* [~primary] (with ~args ~@body))))
      `(do ~@body)))


(defmacro car [thing]
  "Get the first element of a list/cons"
  `(get ~thing 0))


(defmacro cdr [thing]
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

  (for* [branch branches]
    (setv cur-branch (check-branch branch))
    (.append latest-branch cur-branch)
    (setv latest-branch cur-branch))
  root)


(defmacro for [args &rest body]
  "shorthand for nested for loops:
  (for [x foo
        y bar]
    baz) ->
  (for* [x foo]
    (for* [y bar]
      baz))"
  (cond 
   [(odd? (len args))
    (macro-error args "`for' requires an even number of args.")]
   [(empty? body)
    (macro-error None "`for' requires a body to evaluate")]
   [(empty? args) `(do ~@body)]
   [(= (len args) 2)  `(for* [~@args] ~@body)]
   [true 
    (let [[alist (slice args 0 nil 2)]]
      `(for* [(, ~@alist) (genexpr (, ~@alist) [~@args])] ~@body))]))


(defmacro -> [head &rest rest]
  ;; TODO: fix the docstring by someone who understands this
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
  `(let [[~f ~form]]
     ~@(map build-form expressions)
     ~f))

(defmacro ->> [head &rest rest]
  ;; TODO: fix the docstring by someone who understands this
  (setv ret head)
  (for* [node rest]
    (if (not (isinstance node HyExpression))
      (setv node `(~node)))
    (.append node ret)
    (setv ret node))
  ret)


(defmacro if-not [test not-branch &optional [yes-branch nil]]
  "Like `if`, but execute the first branch when the test fails"
  (if (nil? yes-branch)
    `(if (not ~test) ~not-branch)
    `(if (not ~test) ~not-branch ~yes-branch)))


(defmacro-alias [lisp-if lif] [test &rest branches]
  "Like `if`, but anything that is not None/nil is considered true."
  `(if (is-not ~test nil) ~@branches))

(defmacro-alias [lisp-if-not lif-not] [test &rest branches]
  "Like `if-not`, but anything that is not None/nil is considered true."
  `(if (is ~test nil) ~@branches))


(defmacro when [test &rest body]
  "Execute `body` when `test` is true"
  `(if ~test (do ~@body)))


(defmacro unless [test &rest body]
  "Execute `body` when `test` is false"
  `(if-not ~test (do ~@body)))


(defmacro with-gensyms [args &rest body]
  `(let ~(HyList (map (fn [x] `[~x (gensym '~x)]) args))
    ~@body))

(defmacro defmacro/g! [name args &rest body]
  (let [[syms (list (distinct (filter (fn [x] (and (hasattr x "startswith") (.startswith x "g!"))) (flatten body))))]]
    `(defmacro ~name [~@args]
       (let ~(HyList (map (fn [x] `[~x (gensym (slice '~x 2))]) syms))
            ~@body))))


(if-python2
  (defmacro/g! yield-from [expr]
    `(do (import types)
         (setv ~g!iter (iter ~expr))
         (setv ~g!return nil)
         (setv ~g!message nil)
         (while true
           (try (if (isinstance ~g!iter types.GeneratorType)
                  (setv ~g!message (yield (.send ~g!iter ~g!message)))
                  (setv ~g!message (yield (next ~g!iter))))
           (catch [~g!e StopIteration]
             (do (setv ~g!return (if (hasattr ~g!e "value")
                                     (. ~g!e value)
                                     nil))
               (break)))))
           ~g!return))
  nil)


(defmacro defmain [args &rest body]
  "Write a function named \"main\" and do the if __main__ dance"
  (let [[retval (gensym)]]
    `(do
      (defn main [~@args]
        ~@body)

      (when (= --name-- "__main__")
        (import sys)
        (setv ~retval (apply main sys.argv))
        (if (integer? ~retval)
          (sys.exit ~retval))))))


(defmacro-alias [defn-alias defun-alias] [names lambda-list &rest body]
  "define one function with several names"
  (let [[main (first names)]
        [aliases (rest names)]]
    (setv ret `(do (defn ~main ~lambda-list ~@body)))
    (for* [name aliases]
          (.append ret
                   `(setv ~name ~main)))
    ret))

(defmacro Botsbuildbots []
  "Build bots, repeatedly.^W^W^WPrint the AUTHORS, forever."
  `(try
    (do
     (import [requests])

     (let [[r (requests.get
               "https://raw.githubusercontent.com/hylang/hy/master/AUTHORS")]]
       (repeat r.text)))
    (catch [e ImportError]
      (repeat "Botsbuildbots requires `requests' to function."))))
