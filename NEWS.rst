.. default-role:: code

0.20.0 (released 2021-01-25)
==============================

Removals
------------------------------
* Python 3.5 is no longer supported.

New Features
------------------------------
* `let` macro now supports extended iterable unpacking syntax.
* New contrib module `pprint`, a Hy equivalent of `python.pprint`.

Bug Fixes
------------------------------
* Fixed a bug that made `hy.eval` from Python fail on `require`.
* Fixed a bug that prevented pickling of keyword objects.
* Fixed a compiler crash from `setv` with an odd number of arguments in
  `defclass`.

0.19.0 (released 2020-07-16)
==============================

Breaking Changes
------------------------------
* `parse-args` is no longer implemented with `eval`; so e.g. you should
  now say `:type int` instead of `:type 'int`.

New Features
------------------------------
* Python 3.9 is now supported.

Bug Fixes
------------------------------
* Improved support for nesting anaphoric macros by only applying
  symbol replacement where absolutely necessary.
* Quoted f-strings are no longer evaluated prematurely.
* Fixed a regression in the production of error messages for empty
  expressions.
* Fixed a scoping bug for code executed with `hy -c`.
* Fixed a bug in the compilation of multiple `require`\s.
* Fixed various bugs in command-line option parsing.

0.18.0 (released 2020-02-02)
==============================

Removals
------------------------------
* Python 2 is no longer supported.
* Support for attribute lists in `defclass` has been removed. Use `setv`
  and `defn` instead.
* Literal keywords are no longer parsed differently in calls to functions
  with certain names.
* `hy.contrib.multi` has been removed. Use `cond` or the PyPI package
  `multipledispatch` instead.

Other Breaking Changes
------------------------------
* `HySequence` is now a subclass of `tuple` instead of `list`.
  Thus, a `HyList` will never be equal to a `list`, and you can't
  use `.append`, `.pop`, etc. on a `HyExpression` or `HyList`.

New Features
------------------------------
* Added special forms `py` to `pys` that allow Hy programs to include
  inline Python code.
* Added a special form `cmp` for chained comparisons.
* All augmented assignment operators (except `%=` and `^=`) now allow
  more than two arguments.
* Added support for function annotations (PEP 3107) and variable
  annotations (PEP 526).
* Added a function `parse-args` as a wrapper for Python's `argparse`.

Bug Fixes
------------------------------
* Statements in the second argument of `assert` are now executed.
* Fixed a bug that caused the condition of a `while` to be compiled
  twice.
* `in` and `not-in` now allow more than two arguments, as in Python.
* `hy2py` can now handle format strings.
* Fixed crashes from inaccessible history files.
* Removed an accidental import from the internal Python module `test`.
* Fixed a swarm of bugs in `hy.extra.anaphoric`.

Misc. Improvements
------------------------------
* Replaced the dependency `clint` with `colorama`.

0.17.0 (released 2019-05-20)
==============================

**Warning**: Hy 0.17.x will be the last Hy versions to support Python 2,
and we expect 0.17.0 to be the only release in this line. By the time
0.18.0 is released (in 2020, after CPython 2 has ceased being developed),
Hy will only support Python 3.

Removals
------------------------------
* Python 3.4 is no longer supported.

New Features
------------------------------
* Python 3.8 is now supported.
* Format strings with embedded Hy code (e.g., `f"The sum is {(+ x y)}"`)
  are now supported, even on Pythons earlier than 3.6.
* Added a special form `setx` to create Python 3.8 assignment expressions.
* Added new core functions `list?` and `tuple`.
* Gensyms now have a simpler format that's more concise when
  mangled (e.g., `_hyx_XsemicolonXfooXvertical_lineX1235` is now
  `_hyx_fooXUffffX1`).

Bug Fixes
------------------------------
* Fixed a crash caused by errors creating temporary files during
  bytecode compilation.

0.16.0 (released 2019-02-12)
==============================

Removals
------------------------------
* Empty expressions (`()`) are no longer legal at the top level.

New Features
------------------------------
* `eval` / `hy_eval` and `hy_compile` now accept an optional `compiler`
  argument that enables the use of an existing `HyASTCompiler` instance.
* Keyword objects (not just literal keywords) can be called, as
  shorthand for `(get obj :key)`, and they accept a default value
  as a second argument.
* Minimal macro expansion namespacing has been implemented. As a result,
  external macros no longer have to `require` their own macro
  dependencies.
* Macros and tags now reside in module-level `__macros__` and `__tags__`
  attributes.

Bug Fixes
------------------------------
* Cleaned up syntax and compiler errors.
* You can now call `defmain` with an empty lambda list.
* `require` now compiles to Python AST.
* Fixed circular `require`\s.
* Fixed module reloading.
* Fixed circular imports.
* Fixed errors from `from __future__ import ...` statements and missing
  Hy module docstrings caused by automatic importing of Hy builtins.
* Fixed `__main__` file execution.
* Fixed bugs in the handling of unpacking forms in method calls and
  attribute access.
* Fixed crashes on Windows when calling `hy-repr` on date and time
  objects.
* Fixed a crash in `mangle` for some pathological inputs.
* Fixed incorrect mangling of some characters at low code points.
* Fixed a crash on certain versions of Python 2 due to changes in the
  standard module `tokenize`.

0.15.0 (released 2018-07-21)
==============================

Removals
------------------------------
* Dotted lists, `HyCons`, `cons`, `cons?`, and `list*` have been
  removed. These were redundant with Python's built-in data structures
  and Hy's most common model types (`HyExpression`, `HyList`, etc.).
* `&key` is no longer special in lambda lists. Use `&optional` instead.
* Lambda lists can no longer unpack tuples.
* `ap-pipe` and `ap-compose` have been removed. Use threading macros and
  `comp` instead.
* `for/a` has been removed. Use `(for [:async ...] ...)` instead.
* `(except)` is no longer allowed. Use `(except [])` instead.
* `(import [foo])` is no longer allowed. Use `(import foo)` instead.

Other Breaking Changes
------------------------------
* `HyExpression`, `HyDict`, and `HySet` no longer inherit from `HyList`.
  This means you can no longer use alternative punctuation in place of
  square brackets in special forms (e.g. `(fn (x) ...)` instead of
  the standard `(fn [x] ...)`).
* Mangling rules have been overhauled; now, mangled names are
  always legal Python identifiers.
* `_` and `-` are now equivalent, even as single-character names.

  * The REPL history variable `_` is now `*1`.

* Non-shadow unary `=`, `is`, `<`, etc. now evaluate their argument
  instead of ignoring it.
* `list-comp`, `set-comp`, `dict-comp`, and `genexpr` have been replaced
  by `lfor`, `sfor`, `dfor`, and `gfor`, respectively, which use a new
  syntax and have additional features. All Python comprehensions can now
  be written in Hy.
* `&`-parameters in lambda lists must now appear in the same order that
  Python expects.
* Literal keywords now evaluate to themselves, and `HyKeyword` no longer
  inherits from a Python string type
* `HySymbol` no longer inherits from `HyString`.

New Features
------------------------------
* Python 3.7 is now supported.
* `while` and `for` are allowed to have empty bodies.
* `for` supports the various new clause types offered by `lfor`.
* `defclass` in Python 3 supports specifying metaclasses and other
  keyword arguments.
* Added `mangle` and `unmangle` as core functions.
* Added more REPL history variables: `*2` and `*3`.
* Added a REPL variable holding the last exception: `*e`.
* Added a command-line option `-E` per CPython.
* Added a new module `hy.model_patterns`.

Bug Fixes
------------------------------
* `hy2py` should now output legal Python code equivalent to the input Hy
  code in all cases.
* Fixed `(return)` so it can exit a Python 2 generator.
* Fixed a case where `->` and `->>` duplicated an argument.
* Fixed bugs that caused `defclass` to drop statements or crash.
* Fixed a REPL crash caused by illegal backslash escapes.
* `NaN` can no longer create an infinite loop during macro-expansion.
* Fixed a bug that caused `try` to drop expressions.
* The compiler now properly recognizes `unquote-splice`.
* Trying to import a dotted name is now a syntax error, as in Python.
* `defmacro!` now allows optional arguments.
* Fixed handling of variables that are bound multiple times in a single
  `let`.

Misc. Improvements
----------------------------
* `hy-repr` uses registered functions instead of methods.
* `hy-repr` supports more standard types.
* `macroexpand-all` will now expand macros introduced by a `require` in the body of a macro.

0.14.0 (released 2018-02-14)
==============================

Removals
------------------------------
* Python 3.3 is no longer supported
* `def` is gone; use `setv` instead
* `apply` is gone; use the new `#*` and `#**` syntax instead
* `yield-from` is no longer supported under Python 2
* Periods are no longer allowed in keywords
* Numeric literals can no longer begin with a comma or underscore
* Literal `Inf`\s and `NaN`\s must now be capitalized like that

Other Breaking Changes
------------------------------
* Single-character "sharp macros" are now "tag macros", which can have
  longer names
* `xi` from `hy.extra.anaphoric` is now a tag macro `#%`
* `eval` is now a function instead of a special form

New Features
------------------------------
* The compiler now automatically promotes values to Hy model objects
  as necessary, so you can write ``(eval `(+ 1 ~n))`` instead of
  ``(eval `(+ 1 ~(HyInteger n)))``
* `return` has been implemented as a special form
* Added a form of string literal called "bracket strings" delimited by
  `#[FOO[` and `]FOO]`, where `FOO` is customizable
* Added support for PEP 492 (`async` and `await`) with `fn/a`, `defn/a`,
  `with/a`, and `for/a`
* Added Python-style unpacking operators `#*` and  `#**` (e.g.,
  `(f #* args #** kwargs)`)
* Added a macro `comment`
* Added EDN `#_` syntax to discard the next term
* `while` loops may now contain an `else` clause, like `for` loops
* `#%` works on any expression and has a new `&kwargs` parameter `%**`
* Added a macro `doc` and a tag macro `#doc`
* `get` is available as a function
* `~@` (`unquote-splice`) form now accepts any false value as empty

Bug Fixes
------------------------------
* Relative imports (PEP 328) are now allowed
* Numeric literals are no longer parsed as symbols when followed by a dot
  and a symbol
* Hy now respects the environment variable `PYTHONDONTWRITEBYTECODE`
* String literals should no longer be interpreted as special forms or macros
* Tag macros (née sharp macros) whose names begin with `!` are no longer
  mistaken for shebang lines
* Fixed a bug where REPL history wasn't saved if you quit the REPL with
  `(quit)` or `(exit)`
* `exec` now works under Python 2
* No TypeError from multi-arity `defn` returning values evaluating to `None`
* `try` forms are now possible in `defmacro` and `deftag`
* Multiple expressions are now allowed in `try`
* Fixed a crash when `macroexpand`\ing a macro with a named import
* Fixed a crash when `with` suppresses an exception. `with` now returns
  `None` in this case.
* Fixed a crash when `--repl-output-fn` raises an exception
* Fixed a crash when `HyTypeError` was raised with objects that had no
  source position
* `assoc` now evaluates its arguments only once each
* Multiple expressions are now allowed in the `else` clause of
  a `for` loop
* `else` clauses in `for` and `while` are recognized more reliably
* Statements in the condition of a `while` loop are repeated properly
* Argument destructuring no longer interferes with function docstrings
* Nullary `yield-from` is now a syntax error
* `break` and `continue` now raise an error when given arguments
  instead of silently ignoring them

Misc. Improvements
------------------------------
* `read`, `read_str`, and `eval` are exposed and documented as top-level
  functions in the `hy` module
* An experimental `let` macro has been added to `hy.contrib.walk`

0.13.1 (released 2017-11-03)
==============================

Bug Fixes
------------------------------
* Changed setup.py to require astor 0.5, since 0.6 isn't
  backwards-compatible.

0.13.0 (released 2017-06-20)
==============================

Language Changes
------------------------------
* Pythons 2.6, 3.0, 3.1, and 3.2 are no longer supported
* `let` has been removed. Python's scoping rules do not make a proper
  implementation of it possible. Use `setv` instead.
* `lambda` has been removed, but `fn` now does exactly what `lambda` did
* `defreader` has been renamed to `defsharp`; what were previously called
  "reader macros", which were never true reader macros, are now called
  "sharp macros"
* `try` now enforces the usual Python order for its elements (`else` must
  follow all `except`\s, and `finally` must come last). This is only a
  syntactic change; the elements were already run in Python order even when
  defined out of order.
* `try` now requires an `except` or `finally` clause, as in Python
* Importing or executing a Hy file automatically byte-compiles it, or loads
  a byte-compiled version if it exists and is up to date. This brings big
  speed boosts, even for one-liners, because Hy no longer needs to recompile
  its standard library for every startup.
* Added bytestring literals, which create `bytes` objects under Python 3
  and `str` objects under Python 2
* Commas and underscores are allowed in numeric literals
* Many more operators (e.g., `**`, `//`, `not`, `in`) can be used
  as first-class functions
* The semantics of binary operators when applied to fewer or more
  than two arguments have been made more logical
* `(** a b c d)` is now equivalent to `(** a (** b (** c d)))`,
  not `(** (** (** a b) c) d)`
* `setv` always returns `None`
* When a `try` form executes an `else` clause, the return value for the
  `try` form is taken from `else` instead of the `try` body. For example,
  `(try 1 (except [ValueError] 2) (else 3))` returns `3`.
* `xor`: If exactly one argument is true, return it
* `hy.core.reserved` is now `hy.extra.reserved`
* `cond` now supports single argument branches

Bug Fixes
------------------------------
* All shadowed operators have the same arities as real operators
* Shadowed comparison operators now use `and` instead of `&`
  for chained comparisons
* `partition` no longer prematurely exhausts input iterators
* `read` and `read-str` no longer raise an error when the input
  parses to a false value (e.g., the empty string)
* A `yield` inside of a `with` statement will properly suppress implicit
  returns
* `setv` no longer unnecessarily tries to get attributes
* `loop` no longer replaces string literals equal to "recur"
* The REPL now prints the correct value of `do` and `try` forms
* Fixed a crash when tokenizing a single quote followed by whitespace

Misc. Improvements
------------------------------
* New contrib module `hy-repr`
* Added a command-line option `--repl-output-fn`

0.12.1 (released 2017-01-24)
==============================

Bug Fixes
------------------------------
* Allow installation without Git

0.12.0 (released 2017-01-17)
==============================

This release brings some quite significant changes on the language and as a
result very large portions of previously written Hy programs will require
changes. At the same time, documentation and error messages were improved,
hopefully making the language easier to use.

Language Changes
------------------------------
* New syntax for let, with and defclass
* defmacro will raise an error on &kwonly, &kwargs and &key arguments
* Keyword argument labels to functions are required to be strings
* slice replaced with cut to stop overloading the python built-in
* removed redundant throw, catch, progn, defun, lisp-if, lisp-if-not,
  filterfalse, true, false and nil
* global now takes multiple arguments
* Nonlocal keyword (Python 3 only)
* Set literals (#{1 2 3})
* Keyword-only arguments (Python 3 only)
* Setv can assign multiple variables at once
* Empty form allowed for setv, del and cond
* One-argument division, rationals and comparison operators (=, !=, <, >, <=, >=)
* partition form for chunking collection to n-sized tuples
* defn-alias and demacro-alias moved into hy.contrib.alias
* None is returned instead of the last form in --init--
* for and cond can take a multi-expression body
* Hex and octal support for integer literals
* Apply now mangles strings and keywords according to Hy mangling rules
* Variadic if
* defreader can use strings as macro names
* as-> macro added
* require syntax changed and now supports same features as import
* defmulti changed to work with dispatching function
* old defmulti renamed to defn
* Lazy sequences added to contrib
* defmacro! added for once-only evaluation for parameters
* comp, constantly, complement and juxt added
* keyword arguments allowed in method calls before the object

Bug Fixes
------------------------------
* Better error when for doesn't have body
* Better error detection with list comprehensions in Python 2.7
* Setting value to callable will raise an error
* defclass can have properties / methods with built-in names
* Better error messages on invalid macro arguments
* Better error messages with hy2py and hyc
* Cmdline error to string conversion.
* In python 3.3+, generator functions always return a value
* &rest can be used after &optional

Misc. Improvements
------------------------------
* Version information includes SHA1 of current commit
* Improved Python 3.5 support
* Allow specification of global table and module name for (eval ...)
* General documentation improvements
* Contrib.walk: Coerce non-list iterables into list form
* Flow macros (case and switch)
* ap-pipe and ap-compose macros
* #@ reader macro for with-decorator
* Type check `eval` parameters
* `and` and `or` short-circuit
* `and` and `or` accept zero or more arguments
* read-str for tokenizing a line
* botsbuildbots moved to contrib
* Trailing bangs on symbols are mangled
* xi forms (anonymous function literals)
* if form optimizations in some cases
* xor operator
* Overhauled macros to allow macros to ref the Compiler
* ap-if requires then branch
* Parameters for numeric operations (inc, dec, odd?, even?, etc.) aren't type checked
* import_file_to_globals added for use in emacs inferior lisp mode
* hy.core.reserved added for querying reserved words
* hy2py can use standard input instead of a file
* alias, curry, flow and meth removed from contrib
* contrib.anaphoric moved to hy.extra

Changes from 0.10.1
==============================

Language Changes
------------------------------
* new keyword-argument call syntax
* Function argument destructuring has been added.
* Macro expansion inside of class definitions is now supported.
* yield-from support for Python 2
* with-decorator can now be applied to classes.
* assert now accepts an optional assertion message.
* Comparison operators can now be used with map, filter, and reduce.
* new last function
* new drop-last function
* new lisp-if-not/lif-not macro
* new symbol? function
* butlast can now handle lazy sequences.
* Python 3.2 support has been dropped.
* Support for the @ matrix-multiplication operator (forthcoming in
  Python 3.5) has been added.

Bug Fixes
------------------------------
* Nested decorators now work correctly.
* Importing hy modules under Python >=3.3 has been fixed.
* Some bugs involving macro unquoting have been fixed.
* Misleading tracebacks when Hy programs raise IOError have been
  corrected.

Misc. Improvements
------------------------------
* attribute completion in REPL
* new -m command-line flag for running a module
* new -i command-line flag for running a file
* improved error messaging for attempted function definitions
  without argument lists
* Macro expansion error messages are no longer truncated.
* Error messaging when trying to bind to a non-list non-symbol in a
  let form has been improved.

Changes from 0.10.0
==============================

This release took some time (sorry, all my fault) but it's got a bunch of
really nice features. We hope you enjoy hacking with Hy as much as we enjoy
hacking on Hy.

In other news, we're Dockerized as an official library image!
<https://registry.hub.docker.com/_/hylang/>

$ docker run -it --rm hylang
hy 0.10.0 using CPython(default) 3.4.1 on Linux
=> ((lambda [] (print "Hello, World!")))
Hello, World!

 - Hy Society

Language Changes
------------------------------
* Implement raise :from, Python 3 only.
* defmain macro
* name & keyword functions added to core
* (read) added to core
* shadow added to core
* New functions interleave interpose zip_longest added to core
* nth returns default value when out of bounds
* merge-with added
* doto macro added
* keyword? to find out keywords
* setv no longer allows "." in names

Internals
------------------------------
* Builtins reimplemented in terms of python stdlib
* gensyms (defmacro/g!) handles non-string types better

Tools
------------------------------
* Added hy2py to installed scripts

Misc. Fixes
------------------------------
* Symbols like true, false, none can't be assigned
* Set sys.argv default to [''] like Python does
* REPL displays the python version and platform at startup
* Dockerfile added for https://registry.hub.docker.com/_/hylang/

Contrib changes
------------------------------
* Fix ap-first and ap-last for failure conditions


Changes from 0.9.12
==============================

0.10.0 - the "oh man I'm late for PyCon" release

Thanks to theanalyst (Abhi) for getting the release notes
together. You're the best!
- Hy Society

Breaking Changes
------------------------------

We're calling this release 0.10 because we broke
API. Sorry about that. We've removed kwapply in
favor of using `apply`. Please be sure to upgrade
all code to work with `apply`.

(apply function-call args kwargs)  ; is the signature

Thanks
------------------------------

 Major shoutout to Clinton Dreisbach for implementing loop/recur.
 As always, massive hugs to olasd for the constant reviews and for
 implementing HyCons cells. Thanks to @kenanb for redesigning the
 new Hy logo.

 Many thanks to algernon for working on adderall, which helped
 push Hy further this cycle. Adderall is an implementation of miniKanren
 in Hy. If you're interested in using Adderall, check out hydiomatic,
 which prettifies Hy source using Adderall rules.

 This release saw an increase of about 11 contributors for a point
 release, you guys rock!

  -Hy Society

Language Changes
------------------------------

* `for` revamped again (Last time, we hope!), this time using a saner
  itertools.product when nesting
* `lisp-if`/`lif` added for the lisp-like everything is true if, giving
  seasoned lispers a better if check (0 is a value, etc)
* Reader Macros are macros now!
* yield-from is now a proper yield from on Python 3. It also now breaks on
  Python 2.x.
* Added if-not macro
* We finally have a lisp like cons cells
* Generator expressions, set & dict comprehensions are now supported
* (.) is a mini DSL for attribute access
* `macroexpand` & `macroexpand-1` added to core
* `disassemble` added to core, which dumps the AST or equivalent python code
* `coll?` added to core to check for a collection
* `identity` function added to core

Misc. Fixes
------------------------------
* Lots of doc fixes. Reorganization as well as better docs on Hy internals
* Universal Wheel Support
* Pygments > 1.6 supports Hy now. All codeblocks in  docs have been changed
  from clojure to hy
* Hy REPL supports invoking with --spy & -i options [reword]
* `first` and `rest` are functions and not macros anymore
* "clean" target added to Makefile
* hy2py supports a bunch of commandline options to show AST, source etc.
* Sub-object mangling: every identifier is split along the dots & mangled
  separately

Bug Fixes
------------------------------
* Empty MacroExpansions work as expected
* Python 3.4 port. Sorry this wasn't in a 3.4 release time, we forgot to do
  a release. Whoops.
* eg/lxml/parse-tumblr.hy works with Python 3
* hy2py works on Windows
* Fixed unicode encoding issue in REPL during unicode exceptions
* Fixed handling of comments at end of input (#382)

Contrib changes
------------------------------
* Curry module added to contrib
* Loop/recur module added which provides TCO at tail position
* defmulti has been added - check out more in the docs -- thanks to Foxboron for this one!
* Walk module for walking the Hy AST, features a `macroexpand-all` as well


Changes from Hy 0.9.11
==============================

tl;dr:

0.9.12 comes with some massive changes,
We finally took the time to implement gensym, as well as a few
other bits that help macro writing. Check the changelog for
what exactly was added.

The biggest feature, Reader Macros, landed later
in the cycle, but were big enough to warrant a release on its
own. A huge thanks goes to Foxboron for implementing them
and a massive hug goes out to olasd for providing ongoing
reviews during the development.

Welcome to the new Hy contributors, Henrique Carvalho Alves,
Kevin Zita and Kenan Bölükbaşı. Thanks for your work so far,
folks!

Hope y'all enjoy the finest that 2013 has to offer, - Hy Society


* Special thanks goes to Willyfrog, Foxboron and theanalyst for writing
  0.9.12's NEWS. Thanks, y'all! (PT)


Language Changes
------------------------------
* Translate foo? -> is_foo, for better Python interop. (PT)
* Reader Macros!
* Operators + and * now can work without arguments
* Define kwapply as a macro
* Added apply as a function
* Instant symbol generation with gensym
* Allow macros to return None
* Add a method for casting into byte string or unicode depending on python version
* flatten function added to language
* Add a method for casting into byte string or unicode depending on python version
* Added type coercing to the right integer for the platform


Misc. Fixes
------------------------------
* Added information about core team members
* Documentation fixed and extended
* Add astor to install_requires to fix hy --spy failing on hy 0.9.11.
* Convert stdout and stderr to UTF-8 properly in the run_cmd helper.
* Update requirements.txt and setup.py to use rply upstream.
* tryhy link added in documentation and README
* Command line options documented
* Adding support for coverage tests at coveralls.io
* Added info about tox, so people can use it prior to a PR
* Added the start of hacking rules
* Halting Problem removed from example as it was nonfree
* Fixed PyPI is now behind a CDN. The --use-mirrors option is deprecated.
* Badges for pypi version and downloads.


Syntax Fixes
------------------------------
* get allows multiple arguments


Bug Fixes
------------------------------
* OSX: Fixes for readline Repl problem which caused HyREPL not allowing 'b'
* Fix REPL completions on OSX
* Make HyObject.replace more resilient to prevent compiler breakage.


Contrib changes
------------------------------
* Anaphoric macros added to contrib
* Modified eg/twisted to follow the newer hy syntax
* Added (experimental) profile module


Changes from Hy 0.9.10
==============================

* Many thanks to Guillermo Vayá (Willyfrog) for preparing this release's
  release notes. Major shout-out. (PT)

Misc. Fixes
------------------------------

* Many many many documentation fixes
* Change virtualenv name to be `hy`
* Rewrite language.hy not to require hy.core.macros
* Rewrite the bootstrap macros in hy
* Cleanup the hy.macros module
* Add comments to the functions and reorder them
* Translation of meth from Python to Hy
* PY3 should really check for Python >= 3
* Add hy._compat module to unify all Python 2 and 3 compatibility codes.
* Import future.print_statement in hy code
* Coerce the contents of unquote-splice'd things to a list
* Various setup.py enhancements.
* PEP8 fixes
* Use setuptools.find_packages()
* Update PyPI classifiers
* Update website URL
* Install the argparse module in Python 2.6 and before
* Delete the duplicate rply in install_requires. With the PyPI version,
  tests are failed.
* Finally fixed access to hy.core.macros here. have to explicitly require
  them.

Language Changes
------------------------------

* Slightly cleaner version of drop-while, could use yield-from when ready
* Added many native core functions
* Add zero? predicate to check if an object is zero
* Macro if-python2 for compile-time choice between Python 2 and Python 3
  code branches
* Added new travis make target to skip flake8 on pypy but run
  it on all others
* Add "spy mode" to REPL
* Add CL handling to hyc
* Add yield from via macro magic.
* Add some machinery to avoid importing hy in setup.py
* Add a rply-based parser and lexer
* Allow quoting lambda list keywords.
* Clarified rest / cdr, cleaned up require
* Make with return the last expression from its branch
* Fix yielding to not suck (#151)
* Make assoc accept multiple values, also added an even/odd check for
  checkargs
* Added ability to parse doc strings set in defclass declarations,
* Provide bin scripts for both Windows and \*nix
* Removes setf in favor of setv

Changes from Hy 0.9.9
==============================

Stupid Fixes
------------------------------

* I forgot to include hy.core.language in the sdist. (PT)

Changes from Hy 0.9.8
==============================

Syntax Fixes
------------------------------

* Macros are now module-specific, and must be required when used. (KH)
* Added a few more string escapes to the compiler (Thomas Ballinger)
* Keywords are pseudo-callable again, to get the value out of a dict. (PT)
* Empty expression is now the same as an empty vector. (Guillermo Vaya)

Language Changes
------------------------------

* HyDicts (quoted dicts or internal HST repr) are now lists
  that compiled down to dicts by the Compiler later on. (ND)
* Macros can be constants as well. (KH)
* Add eval-when-compile and eval-and-compile (KH)
* Add break and continue to Hy (Morten Linderud)
* Core language libraries added. As example, I've included `take` and
  `drop` in this release. More to come (PT)
* Importing a broken module's behavior now matches Python's more
  closely. (Morten Linderud)

Misc. Fixes
------------------------------

* Ensure compiler errors are always "user friendly" (JD)
* Hy REPL quitter repr adjusted to match Hy syntax (Morten Linderud)
* Windows will no longer break due to missing readline (Ralph Moritz)


Changes from Hy 0.9.7
==============================

Syntax Fixes
------------------------------

* Quasi-quoting now exists long with quoting. Macros will also not
  expand things in quotes.
* kwapply now works with symbols as well as raw dicts. (ND)
* Try / Except will now return properly again. (PT)
* Bare-names sprinkled around the AST won't show up anymore (ND)

Language Changes
------------------------------

* Added a new (require) form, to import macros for that module (PT)
* Native macros exist and work now! (ND)
* (fn) and (lambda) have been merged (ND)
* New (defclass) builtin for class definitions (JD)
* Add unquote-splicing (ND)

Errata
------------------------------

* Paul was an idiot and marked the j-related bug as a JD fix, it was
  actually ND. My bad.

Changes from Hy 0.9.6
==============================

Syntax Fixes
------------------------------

* UTF-8 encoded hy symbols are now `hy_`... rather than `__hy_`..., it's
  silly to prefex them as such. (PT)
* `j` is no longer always interpreted as a complex number; we use it much
  more as a symbol. (ND)
* (decorate-with) has been moved to (with-decorate) (JD)
* New (unless) macro (JD)
* New (when) macro (JD)
* New (take) macro (@eigenhombre)
* New (drop) macro (@eigenhombre)
* import-from and import-as finally removed. (GN)
* Allow bodyless functions (JD)
* Allow variable without value in `let` declaration (JD)
* new (global) builtin (@eal)
* new lambda-list syntax for function defs, for var-arity, kwargs. (JK)

Language Changes
------------------------------

* *HUGE* rewrite of the compiler. Massive thanks go to olasd
  and jd for making this happen. This solves just an insane number
  of bugs. (ND, PT, JD)
* Eval no longer sucks with statements (ND)
* New magic binary flags / mis fixes with the hy interpreter
  (WKG + @eigenhombre)


Changes from Hy 0.9.5
==============================

Syntax Fixes
------------------------------

* .pyc generation routines now work on Python 3. (Vladimir Gorbunov)
* Allow empty (do) forms (JD)
* The `else` form is now supported in `try` statements. (JD)
* Allow `(raise)`, which, like Python, will re-raise
  the last Exception. (JD)
* Strings, bools, symbols are now valid top-level entries. (Konrad Hinsen)
* UTF-8 strings will no longer get punycode encoded. (ND)
* bare (yield) is now valid. (PT)
* (try) now supports the (finally) form. (JD)
* Add in the missing operators and AugAssign operators. (JD)
* (foreach) now supports the (else) form. (JD)

WARNING: WARNING: READ ME: READ ME:
-----------------------------------

From here on out, we will only support "future division" as part of hy.
This is actually quite a pain for us, but it's going to be quite an
amazing feature.

This also normalizes behavior from Py 2 --> Py 3.

Thank you so much, Konrad Hinsen.

Language Changes
------------------------------

* (pass) has been removed from the language; it's a wart that comes from
  a need to create valid Python syntax without breaking the whitespace
  bits. (JD)
* We've moved to a new import style, (import-from) and (import-as) will
  be removed before 1.0. (GN)
* Prototypes for quoted forms (PT)
* Prototypes for eval (PT)
* Enhance tracebacks from language breakage coming from the compiler (JD)
* The REPL no longer bails out if the internals break (Konrad Hinsen)
* We now support float and complex numbers. (Konrad Hinsen)
* Keywords (such as :foo) are now valid and loved. (GN)

Changes from Hy 0.9.4
==============================

Syntax Fixes
------------------------------

* `try` now accepts `else`: (JD)

  `(try BODY (except [] BODY) (else BODY))`


Changes from Hy 0.9.4
==============================

Syntax Fixes
------------------------------

* Statements in the `fn` path early will not return anymore. (PT)
* Added "not" as the inline "not" operator. It's advised to still
  use "not-in" or "is-not" rather than nesting. (JD)
* `let` macro added (PT)
* Added "~" as the "invert" operator. (JD)
* `catch` now accepts a new format: (JD)
    (catch [] BODY)
    (catch [Exception] BODY)
    (catch [e Exception] BODY)
    (catch [e [Exception1 Exception2]] BODY)
* With's syntax was fixed to match the rest of the code. It's now: (PT)
    (with [name context-managed-fn] BODY)
    (with [context-managed-fn] BODY)

Language Changes
------------------------------

* Added `and` and `or` (GN)
* Added the tail threading macro (->>) (PT)
* UTF encoded symbols are allowed, but mangled. All Hy source is now
  presumed to be UTF-8. (JD + PT)
* Better builtin signature checking  (JD)
* If hoisting (for things like printing the return of an if statement)
  have been added. '(print (if true true true))' (PT)

Documentation
------------------------------

* Initial documentation added to the source tree. (PT)


Changes from Hy 0.9.3
==============================

Syntax Fixes
------------------------------

* Nested (do) expressions no longer break Hy (PT)
* `progn` is now a valid alias for `do` (PT)
* `defun` is now a valid alias for `defn` (PT)
* Added two new escapes for \ and " (PT)

Language Changes
------------------------------

* Show a traceback when a compile-error bubbles up in the Hy REPL (PT)
* `setf` / `setv` added, the behavior of `def` may change in the future.
* `print` no longer breaks in Python 3.x (PT)
* Added `list-comp` list comprehensions. (PT)
* Function hoisting (for things like inline invocation of functions,
  e.g. '((fn [] (print "hi!")))' has been added. (PT)
* `while` form added. (ND)
    (while [CONDITIONAL] BODY)

Documentation
------------------------------

* Initial docs added. (WKG + CW)


Changes from Hy 0.9.2
==============================

General Enhancements
------------------------------

* hy.__main__ added, `python -m hy` will now allow a hy shim into existing
  Python scripts. (PT)

Language Changes
------------------------------

* `import-as` added to allow for importing modules. (Amrut Joshi)
* `slice` added to slice up arrays. (PT)
* `with-as` added to allow for context managed bits. (PT)
* `%` added to do Modulo. (PT)
* Tuples added with the '(, foo bar)' syntax. (PT)
* `car` / `first` added. (PT)
* `cdr` / `rest` added. (PT)
* hy --> .pyc compiler added. (PT)
* Completer added for the REPL Readline autocompletion. (PT)
* Merge the `meth` macros into hy.contrib. (PT)
* Changed __repr__ to match Hy source conventions. (PT)
* 2.6 support restored. (PT)


Changes from Hy 0.9.1
==============================

General Enhancements
------------------------------

* Hy REPL added. (PT)
* Doc templates added. (PT)

Language Changes
------------------------------

* Add `pass` (PT)
* Add `yield` (PT)
* Moved `for` to a macro, and move `foreach` to old `for`. (PT)
* Add the threading macro (`->`). (PT)
* Add "earmufs" in. (tenach)
* Add comments in (PT)


Changes from Hy 0.9.0
==============================

Language Changes
------------------------------

* Add `throw` (PT)
* Add `try` (PT)
* add `catch` (PT)


Changes from Hy 0.8.2
==============================

Notes
------------------------------

* Complete rewrite of old-hy. (PT)
