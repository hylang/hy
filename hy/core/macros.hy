;;; Hy core macros
;; Copyright 2021 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

;;; These macros form the hy language
;;; They are automatically required in every module, except inside hy.core

(import [hy.models [HyList HySymbol]])

(eval-and-compile
  (import [hy.core.language [*]]))

(require [hy.core.bootstrap [*]])


(defmacro as-> [head name #* rest]
  "Beginning with `head`, expand a sequence of assignments `rest` to `name`.

  .. versionadded:: 0.12.0

  Each assignment is passed to the subsequent form. Returns the final assignment,
  leaving the name bound to it in the local scope.

  This behaves similarly to other threading macros, but requires specifying
  the threading point per-form via the name, rather than fixing to the first
  or last argument.

  Examples:
    example how ``->`` and ``as->`` relate::

       => (as-> 0 it
       ...      (inc it)
       ...      (inc it))
       2

    ::

       => (-> 0 inc inc)
       2

    create data for our cuttlefish database::

       => (setv data [{:name \"hooded cuttlefish\"
       ...             :classification {:subgenus \"Acanthosepion\"
       ...                              :species \"Sepia prashadi\"}
       ...             :discovered {:year 1936
       ...                          :name \"Ronald Winckworth\"}}
       ...            {:name \"slender cuttlefish\"
       ...             :classification {:subgenus \"Doratosepion\"
       ...                              :species \"Sepia braggi\"}
       ...             :discovered {:year 1907
       ...                          :name \"Sir Joseph Cooke Verco\"}}])

    retrieve name of first entry::

       => (as-> (first data) it
       ...      (:name it))
       \"hooded cuttlefish\"

    retrieve species of first entry::

       => (as-> (first data) it
       ...      (:classification it)
       ...      (:species it))
       \"Sepia prashadi\"

    find out who discovered slender cuttlefish::

       => (as-> (filter (fn [entry] (= (:name entry)
       ...                           \"slender cuttlefish\")) data) it
       ...      (first it)
       ...      (:discovered it)
       ...      (:name it))
       \"Sir Joseph Cooke Verco\"

    more convoluted example to load web page and retrieve data from it::

       => (import [urllib.request [urlopen]])
       => (as-> (urlopen \"http://docs.hylang.org/en/stable/\") it
       ...      (.read it)
       ...      (.decode it \"utf-8\")
       ...      (drop (.index it \"Welcome\") it)
       ...      (take 30 it)
       ...      (list it)
       ...      (.join \"\" it))
       \"Welcome to Hy’s documentation!\"

  .. note::

    In these examples, the REPL will report a tuple (e.g. `('Sepia prashadi',
    'Sepia prashadi')`) as the result, but only a single value is actually
    returned.
  "
  `(do (setv
         ~name ~head
         ~@(interleave (repeat name) rest))
     ~name))


(defmacro assoc [coll k1 v1 #* other-kvs]
  "Associate key/index value pair(s) to a collection `coll` like a dict or list.

  ``assoc`` is used to associate a key with a value in a dictionary or to set an
  index of a list to a value. It takes at least three parameters: the *data
  structure* to be modified, a *key* or *index*, and a *value*. If more than
  three parameters are used, it will associate in pairs.

  Examples:
    ::

       => (do
       ...   (setv collection {})
       ...   (assoc collection \"Dog\" \"Bark\")
       ...   (print collection))
       {u'Dog': u'Bark'}

    ::

       => (do
       ...   (setv collection {})
       ...   (assoc collection \"Dog\" \"Bark\" \"Cat\" \"Meow\")
       ...   (print collection))
       {u'Cat': u'Meow', u'Dog': u'Bark'}

    ::

       => (do
       ...   (setv collection [1 2 3 4])
       ...   (assoc collection 2 None)
       ...   (print collection))
       [1, 2, None, 4]

  .. note:: ``assoc`` modifies the datastructure in place and returns ``None``.
  "
  (if (odd? (len other-kvs))
    (macro-error (last other-kvs)
                 "`assoc` takes an odd number of arguments"))
  (setv c (if other-kvs
            (gensym "c")
            coll))
  `(setv ~@(+ (if other-kvs
                [c coll]
                [])
              #* (gfor [k v] (partition (+ (, k1 v1)
                                           other-kvs))
                       [`(get ~c ~k) v]))))


(defn _with [node args body]
  (if
    (not args)
      `(do ~@body)
    (<= (len args) 2)
      `(~node [~@args] ~@body)
    True (do
      (setv [p1 p2 #* args] args)
      `(~node [~p1 ~p2] ~(_with node args body)))))


(defmacro with [args #* body]
  "Wrap execution of `body` within a context manager given as bracket `args`.

  ``with`` is used to wrap the execution of a block within a context manager. The
  context manager can then set up the local system and tear it down in a controlled
  manner. The archetypical example of using ``with`` is when processing files.
  ``with`` can bind context to an argument or ignore it completely, as shown below:

  Examples:
    ::

       => (with [arg (expr)] block)
       => (with [(expr)] block)
       => (with [arg (expr) (expr)] block)

    The following example will open the ``NEWS`` file and print its content to the
    screen. The file is automatically closed after it has been processed::

       => (with [f (open \"NEWS\")] (print (.read f)))

    ``with`` returns the value of its last form, unless it suppresses an exception
    (because the context manager's ``__exit__`` method returned true), in which
    case it returns ``None``. So, the previous example could also be written::

       => (print (with [f (open \"NEWS\")] (.read f)))


    Shorthand for nested ``with*`` loops::

       => (with [x foo y bar] baz)
       (with* [x foo]
         (with* [y bar]
           baz)).
  "
  (_with 'with* args body))


(defmacro with/a [args #* body]
  "Wrap execution of `body` with/ain a context manager given as bracket `args`.

  ``with/a`` behaves like ``with``, but is used to wrap the execution of
  a block within an asynchronous context manager. The context manager can
  then set up the local system and tear it down in a controlled manner
  asynchronously.

  Examples:
    ::

       => (with/a [arg (expr)] block
       => (with/a [(expr)] block
       => (with/a [arg (expr) (expr)] block

    Shorthand for nested ``with/a*`` loops::

       => (with/a [x foo y bar] baz)
       (with/a* [x foo]
         (with/a* [y bar]
           baz)).

  .. note::
    ``with/a`` returns the value of its last form, unless it suppresses an exception
    (because the context manager's ``__aexit__`` method returned true), in which
    case it returns ``None``."
  (_with 'with/a* args body))

(defmacro cond [#* branches]
  "Build a nested if clause with each `branch` a [cond result] bracket pair.

  Examples:
    ::

       => (cond [condition-1 result-1]
       ...      [condition-2 result-2])
       (if condition-1 result-1
         (if condition-2 result-2))

    If only the condition is given in a branch, then the condition is also used as
    the result. The expansion of this single argument version is demonstrated
    below::

       => (cond [condition-1]
       ...       [condition-2])
       (if condition-1 condition-1
         (if condition-2 condition-2))

    As shown below, only the first matching result block is executed::

       => (defn check-value [value]
       ...   (cond [(< value 5) (print \"value is smaller than 5\")]
       ...         [(= value 5) (print \"value is equal to 5\")]
       ...         [(> value 5) (print \"value is greater than 5\")]
       ...         [True (print \"value is something that it should not be\")]))

       => (check-value 6)
       \"value is greater than 5\"
"
  (or branches
    (return))

  `(if ~@(reduce + (gfor
    branch branches
    (if
      (not (and (is (type branch) hy.HyList) branch))
        (macro-error branch "each cond branch needs to be a nonempty list")
      (= (len branch) 1) (do
        (setv g (gensym))
        [`(do (setv ~g ~(first branch)) ~g) g])
      True
        [(first branch) `(do ~@(cut branch 1))])))))


(defmacro -> [head #* args]
  "Thread `head` first through the `rest` of the forms.

  ``->`` (or the *threading macro*) is used to avoid nesting of expressions. The
  threading macro inserts each expression into the next expression's first argument
  place. The following code demonstrates this:

  Examples:
    ::

       => (defn output [a b] (print a b))
       => (-> (+ 4 6) (output 5))
       10 5
  "
  (setv ret head)
  (for [node args]
    (setv ret (if (isinstance node HyExpression)
                  `(~(first node) ~ret ~@(rest node))
                  `(~node ~ret))))
  ret)


(defmacro doto [form #* expressions]
  "Perform possibly mutating `expressions` on `form`, returning resulting obj.

  .. versionadded:: 0.10.1

  ``doto`` is used to simplify a sequence of method calls to an object.

  Examples:
    ::

       => (doto [] (.append 1) (.append 2) .reverse)
       [2, 1]

    ::

       => (setv collection [])
       => (.append collection 1)
       => (.append collection 2)
       => (.reverse collection)
       => collection
       [2, 1]
  "
  (setv f (gensym))
  (defn build-form [expression]
    (if (isinstance expression HyExpression)
      `(~(first expression) ~f ~@(rest expression))
      `(~expression ~f)))
  `(do
     (setv ~f ~form)
     ~@(map build-form expressions)
     ~f))


(defmacro ->> [head #* args]
  "Thread `head` last through the `rest` of the forms.

  ``->>`` (or the *threading tail macro*) is similar to the *threading macro*, but
  instead of inserting each expression into the next expression's first argument,
  it appends it as the last argument. The following code demonstrates this:

  Examples:
    ::

       => (defn output [a b] (print a b))
       => (->> (+ 4 6) (output 5))
       5 10
  "
  (setv ret head)
  (for [node args]
    (setv ret (if (isinstance node HyExpression)
                  `(~@node ~ret)
                  `(~node ~ret))))
  ret)


(defmacro of [base #* args]
  "Shorthand for indexing for type annotations.

  If only one arguments are given, this expands to just that argument. If two arguments are
  given, it expands to indexing the first argument via the second. Otherwise, the first argument
  is indexed using a tuple of the rest.

  ``of`` has three forms:

  - ``(of T)`` will simply become ``T``.
  - ``(of T x)`` will become ``(get T x)``.
  - ``(of T x y ...)`` (where the ``...`` represents zero or more arguments) will become
    ``(get T (, x y ...))``.

  Examples:
    ::

       => (of str)
       str

    ::

       => (of List int)
       List[int]

    ::

       => (of Set int)
       Set[int]

    ::

       => (of Dict str str)
       Dict[str, str]

    ::

       => (of Tuple str int)
       Tuple[str, int]

    ::

       => (of Callable [int str] str)
       Callable[[int, str], str]
  "
  (if
    (empty? args) base
    (= (len args) 1) `(get ~base ~@args)
    `(get ~base (, ~@args))))


(defmacro if-not [test not-branch [yes-branch None]]
  "Like `if`, but execute the first branch when the test fails

  .. versionadded:: 0.10.0

  ``if-not`` is similar to ``if*`` but the second expression will be executed
  when the condition fails while the third and final expression is executed when
  the test succeeds -- the opposite order of ``if*``. The final expression is
  again optional and defaults to ``None``.

  Examples:
    ::

       => (if-not (money-left? account)
             (print \"let's go and work\")
             (print \"let's go shopping\"))
  "
  `(if* (not ~test) ~not-branch ~yes-branch))


(defmacro lif [#* args]
  "Like `if`, but anything that is not None is considered true.

  .. versionadded:: 0.10.0

  For those that prefer a more Lispy ``if`` clause, we have
  ``lif``. This *only* considers ``None`` to be false! All other
  \"false-ish\" Python values are considered true.

  Examples:
    ::

       => (lif True \"true\" \"false\")
       \"true\"

    ::

       => (lif False \"true\" \"false\")
       \"true\"

    ::

       => (lif 0 \"true\" \"false\")
       \"true\"

    ::

       => (lif None \"true\" \"false\")
       \"false\"
  "
  (setv n (len args))
  (if* n
       (if* (= n 1)
            (get args 0)
            `(if* (is-not ~(get args 0) None)
                  ~(get args 1)
                  (lif ~@(cut args 2))))))


(defmacro lif-not [test not-branch [yes-branch None]]
  "Like `if-not`, but anything that is not None is considered true.

  .. versionadded:: 0.11.0

  Examples:
    ::

       => (lif-not None \"true\" \"false\")
       \"true\"

    ::

       => (lif-not False \"true\" \"false\")
       \"false\"
"
  `(if* (is ~test None) ~not-branch ~yes-branch))


(defmacro when [test #* body]
  "Execute `body` when `test` is true

  ``when`` is similar to ``unless``, except it tests when the given conditional is
  ``True``. It is not possible to have an ``else`` block in a ``when`` macro. The
  following shows the expansion of the macro.

  Examples:
    ::

       => (when conditional statement)
       (if conditional (do statement))
  "
  `(if ~test (do ~@body)))


(defmacro unless [test #* body]
  "Execute `body` when `test` is false

  The ``unless`` macro is a shorthand for writing an ``if`` statement that checks if
  the given conditional is ``False``. The following shows the expansion of this macro.

  Examples:
    ::

       => (unless conditional statement)
       (if conditional
         None
         (do statement))"
  `(if-not ~test (do ~@body)))


(defn _do-n [count-form body]
  `(for [~(gensym) (range ~count-form)]
    ~@body))


(defmacro do-n [count-form #* body]
  "Execute `body` a number of times equal to `count-form` and return
  ``None``. (To collect return values, use :hy:macro:`list-n`
  instead.) Negative values of the count are treated as 0.

  This macro is implemented as a :hy:macro:`for` loop, so you can use
  :hy:macro:`break` and :hy:macro:`continue` in the body.

  ::

     => (do-n 3 (print \"hi\"))
     hi
     hi
     hi
  "
  (_do-n count-form body))


(defmacro list-n [count-form #* body]
  "Like :hy:macro:`do-n`, but the results are collected into a list.

  ::

    => (setv counter 0)
    => (list-n 5 (+= counter 1) counter)
    [1 2 3 4 5]
  "
  (setv l (gensym))
  `(do
    (setv ~l [])
    ~(_do-n count-form [`(.append ~l (do ~@body))])
    ~l))


(defmacro with-gensyms [args #* body]
  "Execute `body` with `args` as bracket of names to gensym for use in macros.

  .. versionadded:: 0.9.12

  ``with-gensym`` is used to generate a set of :hy:func:`gensym <hy.core.language.gensym>`
  for use in a macro. The following code:

  Examples:
    ::

       => (with-gensyms [a b c]
       ...   ...)

    expands to::

       => (do
       ...   (setv a (gensym)
       ...         b (gensym)
       ...         c (gensym))
       ...   ...)

  .. seealso::

     Section :ref:`using-gensym`
  "
  (setv syms [])
  (for [arg args]
    (.extend syms [arg `(gensym '~arg)]))
  `(do
    (setv ~@syms)
    ~@body))


(defmacro defmacro/g! [name args #* body]
  "Like `defmacro`, but symbols prefixed with 'g!' are gensymed.

  .. versionadded:: 0.9.12

  ``defmacro/g!`` is a special version of ``defmacro`` that is used to
  automatically generate :hy:func:`gensym <hy.core.language.gensym>` for
  any symbol that starts with
  ``g!``.

  For example, ``g!a`` would become ``(gensym \"a\")``.

  .. seealso::

    Section :ref:`using-gensym`
  "
  (setv syms (list
              (distinct
               (filter (fn [x]
                         (and (hasattr x "startswith")
                              (.startswith x "g!")))
                       (flatten body))))
        gensyms [])
  (for [sym syms]
    (.extend gensyms [sym `(gensym ~(cut sym 2))]))

  (setv [docstring body] (if (and (instance? str (first body))
                                  (> (len body) 1))
                             (, (first body) (tuple (rest body)))
                             (, None body)))

  `(defmacro ~name [~@args]
     ~docstring
     (setv ~@gensyms)
     ~@body))


(defmacro defmacro! [name args #* body]
  "Like `defmacro/g!`, with automatic once-only evaluation for 'o!' params.

  Such 'o!' params are available within `body` as the equivalent 'g!' symbol.

  Examples:
    ::

       => (defn expensive-get-number [] (print \"spam\") 14)
       => (defmacro triple-1 [n] `(+ ~n ~n ~n))
       => (triple-1 (expensive-get-number))  ; evals n three times
       spam
       spam
       spam
       42

    ::

       => (defmacro/g! triple-2 [n] `(do (setv ~g!n ~n) (+ ~g!n ~g!n ~g!n)))
       => (triple-2 (expensive-get-number))  ; avoid repeats with a gensym
       spam
       42

    ::

       => (defmacro! triple-3 [o!n] `(+ ~g!n ~g!n ~g!n))
       => (triple-3 (expensive-get-number))  ; easier with defmacro!
       spam
       42
  "
  (defn extract-o!-sym [arg]
    (cond [(and (symbol? arg) (.startswith arg "o!"))
           arg]
          [(and (instance? HyList arg) (.startswith (first arg) "o!"))
           (first arg)]))
  (setv os (list (filter identity (map extract-o!-sym args)))
        gs (lfor s os (HySymbol (+ "g!" (cut s 2)))))

  (setv [docstring body] (if (and (instance? str (first body))
                                  (> (len body) 1))
                             (, (first body) (tuple (rest body)))
                             (, None body)))

  `(defmacro/g! ~name ~args
     ~docstring
     `(do (setv ~@(interleave ~gs ~os))
          ~@~body)))


(defmacro defmain [args #* body]
  "Write a function named \"main\" and do the 'if __main__' dance.

  .. versionadded:: 0.10.1

  The ``defmain`` macro defines a main function that is immediately called
  with ``sys.argv`` as arguments if and only if this file is being executed
  as a script.  In other words, this:

  Examples:
    ::

       => (defmain [#* args]
       ...  (do-something-with args))

    is the equivalent of:

    .. code-block:: python

       => def main(*args):
       ...    do_something_with(args)
       ...    return 0
       ...
       ... if __name__ == \"__main__\":
       ...     import sys
       ...     retval = main(*sys.argv)
       ...
       ...     if isinstance(retval, int):
       ...         sys.exit(retval)

    Note that as you can see above, if you return an integer from this
    function, this will be used as the exit status for your script.
    (Python defaults to exit status 0 otherwise, which means everything's
    okay!) Since ``(sys.exit 0)`` is not run explicitly in the case of a
    non-integer return from ``defmain``, it's a good idea to put ``(defmain)``
    as the last piece of code in your file.

    If you want fancy command-line arguments, you can use the standard Python
    module ``argparse`` in the usual way::

       => (import argparse)
       => (defmain [#* _]
       ...   (setv parser (argparse.ArgumentParser))
       ...   (.add-argument parser \"STRING\"
       ...     :help \"string to replicate\")
       ...   (.add-argument parser \"-n\" :type int :default 3
       ...     :help \"number of copies\")
       ...   (setv args (parser.parse_args))
       ...   (print (* args.STRING args.n))
       ...   0)
"
  (setv retval (gensym)
        restval (gensym))
  `(when (= --name-- "__main__")
     (import sys)
     (setv ~retval ((fn [~@(or args `[#* ~restval])] ~@body) #* sys.argv))
     (if (integer? ~retval)
       (sys.exit ~retval))))


(defmacro "#@" [expr]
  "with-decorator tag macro"
  (if (empty? expr)
      (macro-error expr "missing function argument"))
  (setv decorators (cut expr None -1)
        fndef (get expr -1))
  `(with-decorator ~@decorators ~fndef))


(defmacro comment [#* body]
  "Ignores body and always expands to None

  The ``comment`` macro ignores its body and always expands to ``None``.
  Unlike linewise comments, the body of the ``comment`` macro must
  be grammatically valid Hy, so the compiler can tell where the comment ends.
  Besides the semicolon linewise comments,
  Hy also has the ``#_`` discard prefix syntax to discard the next form.
  This is completely discarded and doesn't expand to anything, not even ``None``.

  Examples:
    ::

        => (print (comment <h1>Surprise!</h1>
        ...                <p>You'd be surprised what's grammatically valid in Hy.</p>
        ...                <p>(Keep delimiters in balance, and you're mostly good to go.)</p>)
        ...        \"Hy\")
        None Hy

    ::

        => (print #_(comment <h1>Surprise!</h1>
        ...                  <p>You'd be surprised what's grammatically valid in Hy.</p>
        ...                  <p>(Keep delimiters in balance, and you're mostly good to go.)</p>))
        ...        \"Hy\")
        Hy"
  None)


(defmacro doc [symbol]
  "macro documentation

   Gets help for a macro function available in this module.
   Use ``require`` to make other macros available.

   Use ``(help foo)`` instead for help with runtime objects."
  `(help (.get __macros__ (mangle '~symbol) None)))


(defmacro cfor [f #* generator]
  #[[syntactic sugar for passing a ``generator`` expression to the callable ``f``

  Its syntax is the same as :ref:`generator expression <py:genexpr>`, but takes
  a function ``f`` that the generator will be immedietly passed to. Equivalent
  to ``(f (gfor ...))``.

  Examples:
  ::
     => (cfor tuple x (range 10) :if (odd? x) x)
     (, 1 3 5 7 9)

  The equivalent in python would be:

     >>> tuple(x for x in range(10) if is_odd(x))

  Some other common functions that take iterables::

     => (cfor all x [1 3 8 5] (< x 10))
     True

     => (with [f (open "AUTHORS")]
     ...  (cfor max
     ...        author (.splitlines (f.read))
     ...        :setv name (.group (re.match r"\* (.*?) <" author) 1)
     ...        :if (name.startswith "A")
     ...        (len name)))
     20 ;; The number of characters in the longest author's name that starts with 'A'
  ]]
  `(~f (gfor ~@generator)))
