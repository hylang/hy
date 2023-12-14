======
Macros
======

Macros, and the metaprogramming they enable, are one of the characteristic features of Lisp, and one of the main advantages Hy offers over vanilla Python. Much of the material covered in this chapter will be familiar to veterans of other Lisps, but there are also a lot of Hyly specific details.

What are macros for?
--------------------

The gist of `metaprogramming
<https://en.wikipedia.org/wiki/Metaprogramming>`_ is that it allows you to program the programming language itself (hence the word). You can create new control structures, like :ref:`do-while <do-while>`, or other kinds of new syntax, like a concise literal notation for your favorite data structure. You can also modify how existing syntax is understood within a region of code, as by making identifiers that start with a capital letter implicitly imported from a certain module. Finally, metaprogramming can improve performance in some cases by effectively inlining functions, or by computing something once at compile-time rather than several times at run-time. With a Lisp-like macro system, you can metaprogram in a slicker and less error-prone way than generating code as text with conventional string formatting, or with lexer-level macros like those provided by the C preprocessor.

Types of macros
---------------

Hy offers two types of macros: regular macros and reader macros.

**Regular macros**, typically defined with :hy:func:`defmacro`, are the kind Lispers usually mean when they talk about "macros". Regular macros are called like a function, with an :ref:`expression <expressions>` whose head is the macro name: for example, ``(foo a b)`` could call a macro named ``foo``. A regular macro is called at compile-time, after the entire top-level form in which it appears is parsed, and receives parsed :ref:`models <models>` as arguments. Regular macros come in :ref:`three varieties, which vary in scope <macro-namespaces>`.

**Reader macros**, typically defined with :hy:func:`defreader`, are lower-level than regular macros. They're called with the hash sign ``#``; for example, ``#foo`` calls a reader macro named ``foo``. A reader macro is called at parse-time. It doesn't receive conventional arguments. Instead, it uses an implicitly available parser object to parse the subsequent source text. When it returns, the standard Hy parser picks up where it left off.

Related constructs
~~~~~~~~~~~~~~~~~~

There are three other constructs that perform compile-time processing much like macros, and hence are worth mentioning here.

- :hy:func:`do-mac` is essentially shorthand for defining and then immediately calling a regular macro with no arguments.
- :hy:func:`eval-when-compile` evaluates some code at compile-time, but contributes no code to the final program, like a macro that returns ``None`` in a context where the ``None`` doesn't do anything.
- :hy:func:`eval-and-compile` evaluates some code at compile-time, like :hy:func:`eval-when-compile`, but also leaves the same code to be re-evaluated at run-time.

When to use what
~~~~~~~~~~~~~~~~

The variety of options can be intimidating. In addition to all of Hy's features listed above, Python is a dynamic programming language that allows you to do a lot of things at run-time that other languages would blanch at. For example, you can dynamically define a new class by calling :class:`type`. So, watch out for cases where your first thought is to use a macro, but you don't actually need one.

When deciding what to use, a good rule of thumb is to use the least powerful option that suffices for the syntax, semantics, and performance that you want. So first, see if Python's dynamic features are enough. If they aren't, try a macro-like construct or a regular macro. If even those aren't enough, try a reader macro. Using the least powerful applicable option will help you avoid the :ref:`macro pitfalls described below <macro-pitfalls>`, as well as other headaches such as wanting to use a macro where a Python API needs a function. (For the sake of providing simpler examples, much of the below discussion will ignore this advice and consider macros that could easily be written as functions.)

The basics
----------

A regular macro can be defined with :hy:func:`defmacro` using a syntax similar to that of :hy:func:`defn`. Here's how you could define and call a trivial macro that takes no arguments and returns a constant::

    (defmacro seventeen []
      17)

    (print (seventeen))

To see that ``seventeen`` is expanded at compile-time, run ``hy2py`` on this script and notice that it ends with ``print(17)`` rather than ``print(seventeen())``. If you insert a ``print`` call inside the macro definition, you'll also see that the print happens when the file is compiled, but not when it's rerun (provided an up-to-date bytecode file exists).

A more useful macro returns code. You can construct a model the long way, like this::

    (defmacro addition []
      (hy.models.Expression [
        (hy.models.Symbol "+")
        (hy.models.Integer 1)
        (hy.models.Integer 1)]))

or more concisely with :hy:func:`quote`, like this::

    (defmacro addition []
      '(+ 1 1))

You don't need to always return a model because the compiler calls :hy:func:`hy.as-model` on everything before trying to compile it. Thus, the ``17`` above works fine in place of ``(hy.models.Integer 17)``. But trying to compile something that ``hy.as-model`` chokes on, like a function object, is an error.

Arguments are always passed in as models. You can use quasiquotation (see :hy:func:`quasiquote`) to concisely define a model with partly literal and partly evaluated components::

    (defmacro set-to-2 [variable]
     `(setv ~variable 2))
    (set-to-2 foobar)
    (print foobar)

Macros don't understand keyword arguments like functions do. Rather, the :ref:`keyword objects <keywords>` themselves are passed in literally. This gives you flexibility in how to handle them. Thus, ``#** kwargs`` and ``*`` aren't allowed in the parameter list of a macro, although ``#* args`` and ``/`` are.

On the inside, macros are functions, and obey the usual Python semantics for functions. For example, :hy:func:`setv` inside a macro will define or modify a variable local to the current macro call, and :hy:func:`return` ends macro execution and uses its argument as the expansion.

Macros from other modules can be brought into the current scope with :hy:func:`require`.

.. _macro-pitfalls:

Pitfalls
--------

Macros are powerful, but with great power comes great potential for anguish. There are a few characteristic issues you need to guard against to write macros well, and, to a lesser extent, even to use macros well.

Name games
~~~~~~~~~~

A lot of these issues are variations on the theme of names not referring to what you intend them to, or in other words, surprise shadowing. For example, the macro below was intended to define a new variable named ``x``, but it ends up modifying a preexisting variable. ::

   (defmacro upper-twice [arg]
     `(do
        (setv x (.upper ~arg))
        (+ x x)))
   (setv x "Okay guys, ")
   (setv salutation (upper-twice "bye"))
   (print (+ x salutation))
     ; Intended result: "Okay guys, BYEBYE"
     ; Actual result: "BYEBYEBYE"

If you avoid the assignment entirely, by using an argument more than once, you can cause a different problem: surprise multiple evaluation. ::

   (defmacro upper-twice [arg]
     `(+ (.upper ~arg) (.upper ~arg)))
   (setv items ["a" "b" "c"])
   (print (upper-twice (.pop items)))
     ; Intended result: "CC"
     ; Actual result: "CB"

A better approach is to use :hy:func:`hy.gensym` to choose your variable name::

   (defmacro upper-twice [arg]
     (setv g (hy.gensym))
     `(do
        (setv ~g (.upper ~arg))
        (+ ~g ~g)))

Hyrule provides some macros that make using gensyms more convenient, like :hy:func:`defmacro! <hyrule.macrotools.defmacro!>` and :hy:func:`with-gensyms <hyrule.macrotools.with-gensyms>`.

Macro subroutines
~~~~~~~~~~~~~~~~~

A case where you could want something to be in the scope of a macro's expansion, and then it turns out not to be, is when you want to call a function or another macro in the expansion::

    (defmacro hypotenuse [a b]
      (import math)
      `(math.sqrt (+ (** ~a 2) (** ~b 2))))
    (print (hypotenuse 3 4))
      ; NameError: name 'math' is not defined

The form ``(import math)`` here appears in the wrong context, in the macro call itself rather than the expansion. You could use ``import`` or ``require`` to bind the module name or one of its members to a gensym, but an often more convenient option is to use the one-shot import syntax :hy:class:`hy.I` or the one-shot require syntax :ref:`hy.R <hy.R>`::

    (defmacro hypotenuse [a b]
      `(hy.I.math.sqrt (+ (** ~a 2) (** ~b 2))))
    (hypotenuse 3 4)

A related but distinct issue is when you want to use a function (or other ordinary Python object) in a macro's code, but it isn't available soon enough::

    (defn subroutine [x]
      (hy.models.Symbol (.upper x)))
    (defmacro uppercase-symbol [x]
      (subroutine x))
    (setv (uppercase-symbol foo) 1)
      ; NameError: name 'subroutine' is not defined

Here, ``subroutine`` is only defined at run-time, so ``uppercase-symbol`` can't see it when it's expanding (unless you happen to be calling ``uppercase-symbol`` from a different module). This is easily worked around by wrapping ``(defn subroutine …)`` in :hy:func:`eval-and-compile` (or :hy:func:`eval-when-compile` if you want ``subroutine`` to be invisible at run-time).

By the way, despite the need for ``eval-and-compile``, extracting a lot of complex logic out of a macro into a function is often a good idea. Functions are typically easier to debug and to make use of in other macros.

The important take-home big fat WARNING
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Ultimately it's wisest to use only four kinds of names in macro expansions: gensyms, core macros, objects that Python puts in scope by default (like its built-in functions), and ``hy`` and its attributes. It's possible to rebind nearly all these names, so surprise shadowing is still theoretically possible. Unfortunately, the only way to prevent these pathological rebindings from coming about is… don't do that. Don't make a new macro named ``setv`` or name a function argument ``type`` unless you're ready for every macro you call to break, the same way you wouldn't monkey-patch a built-in Python module without thinking carefully. This kind of thing is the responsibility of the macro caller; the macro writer can't do much to defend against it. There is at least a pragma :ref:`warn-on-core-shadow <warn-on-core-shadow>`, enabled by default, that causes ``defmacro`` and ``require`` to warn you if you give your new macro the same name as a core macro.

.. _reader-macros:

Reader macros
-------------

Reader macros allow you to hook directly into Hy's parser to customize how text is parsed into models. They're defined with :hy:func:`defreader`, or, like regular macros, brought in from other modules with :hy:func:`require`. Rather than receiving function arguments, a reader macro has access to a :py:class:`HyReader <hy.reader.hy_reader.HyReader>` object named ``&reader``, which provides all the text-parsing logic that Hy uses to parse itself (see :py:class:`HyReader <hy.reader.hy_reader.HyReader>` and its base class :py:class:`Reader <hy.reader.reader.Reader>` for the available methods). A reader macro is called with the hash sign ``#``, and like a regular macro, it should return a model or something convertible to a model.

Here's a moderately complex example of a reader macro that couldn't be implemented as a regular macro. It reads in a list of lists in which the inner lists are newline-separated, but newlines are allowed inside elements. ::

    (defreader matrix
      (.slurp-space &reader)
      (setv start (.getc &reader))
      (assert (= start "["))
      (.slurp-space &reader)
      (setv out [[]])
      (while (not (.peek-and-getc &reader "]"))
        (cond
          (any (gfor  c " \t"  (.peek-and-getc &reader c)))
            None
          (.peek-and-getc &reader "\n")
            (.append out [])
          True
            (.append (get out -1) (.parse-one-form &reader))))
      (lfor  line out  :if line  line))

    (print (hy.repr #matrix [
        1 (+ 1 1) 3
        4 ["element" "containing"
              "a" "newline"]        6
        7 8 9]))
      ; => [[1 2 3] [4 ["element" "containing" "a" "newline"] 6] [7 8 9]]

Note that because reader macros are evaluated at parse-time, and top-level forms are completely parsed before any further compile-time execution occurs, you can't use a reader macro in the same top-level form that defines it::

   (do
     (defreader up
       (.slurp-space &reader)
       (.upper (.read-one-form &reader)))
     (print #up "hello?"))
       ; LexException: reader macro '#up' is not defined

.. _macro-namespaces:

Macro namespaces and operations on macros
-----------------------------------------

Macros don't share namespaces with ordinary Python objects. That's why something like ``(defmacro m []) (print m)`` fails with a ``NameError``, and how :hy:mod:`hy.pyops` can provide a function named ``+`` without hiding the core macro ``+``. 

There are three scoped varieties of regular macro. First are **core macros**, which are built into Hy; :ref:`the set of core macros <core-macros>` is fixed. They're available by default. You can inspect them in the dictionary ``bulitins._hy_macros``, which is attached to Python's usual :py:mod:`builtins` module. The keys are strings giving :ref:`mangled <mangling>` names and the values are the function objects implementing the macros.

**Global macros** are associated with modules, like Python global variables. They're defined when you call ``defmacro`` or ``require`` in a global scope. You can see them in the global variable ``_hy_macros`` associated with the same module. You can manipulate ``_hy_macros`` to list, add, delete, or get help on macros, but be sure to use :hy:func:`eval-and-compile` or :hy:func:`eval-when-compile` when you need the effect to happen at compile-time, which is often. (Modifying ``bulitins._hy_macros`` is of course a risky proposition.) Here's an example, which also demonstrates the core macro :hy:func:`get-macro <hy.core.macros.get-macro>`. ``get-macro`` provides syntactic sugar for getting all sorts of macros as objects. ::

    (defmacro m []
      "This is a docstring."
      `(print "Hello, world."))
    (print (in "m" _hy_macros))   ; => True
    (help (get-macro m))
    (m)                           ; => "Hello, world."
    (eval-and-compile
      (del (get _hy_macros "m")))
    (m)                           ; => NameError
    (eval-and-compile
      (setv (get _hy_macros (hy.mangle "new-mac")) (fn []
        '(print "Goodbye, world."))))
    (new-mac)                     ; => "Goodbye, world."

**Local macros** are associated with function, class, or comprehension scopes, like Python local variables. They come about when you call ``defmacro`` or ``require`` in an appropriate scope. You can call :hy:func:`local-macros <hy.core.macros.local-macros>` to view local macros, but adding or deleting elements is ineffective.

Finally, ``_hy_reader_macros`` is a per-module dictionary like ``_hy_macros`` for reader macros, but here, the keys aren't mangled. There are no local reader macros, and there's no official way to introspect on Hy's handful of core reader macros. So, of the three scoped varieties of regular macro, reader macros most resemble global macros.
