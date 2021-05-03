==============
Hy Style Guide
==============

The Hy style guide intends to be a set of ground rules for the Hyve
(yes, the Hy community prides itself in appending Hy to everything)
to write idiomatic Hy code. Hy derives a lot from Clojure & Common
Lisp, while always maintaining Python interoperability.


Layout & Indentation
====================

The #1 complaint about Lisp?

  *It's too weird looking with all those parentheses! How do you even* **read** *that?*

And, they're right! Lisp was originally much too hard to read.
Then they figured out layout and indentation. And it was glorious.

The Three Laws
--------------

Here's the secret: *Real Lispers don't count the brackets.*
They fade into the background.
When reading Lisp, disregard the trailing closing brackets---those are for the computer, not the human.
As in Python, read the code structure by indentation.

Lisp code is made of trees---Abstract Syntax Trees---not strings.
S-expressions are very direct textual representation of AST.
That's the level of *homoiconicity*---the level Lisp macros operate on.
It's not like the C-preprocessor or Python's interpolated eval-string tricks that see code as just letters.
That's not how to think of Lisp code; think tree structure, not delimiters.

1. Closing brackets must NEVER be left alone, sad and lonesome on their own line.

.. code-block:: clj

    ;; PREFERRED
    (defn fib [n]
      (if (<= n 2)
          n
          (+ (fib (- n 1))
             (fib (- n 2)))))  ; Lots of Irritating Superfluous Parentheses
                                    ; L.I.S.P. ;))

    ;; How the experienced Lisper sees it. Indented trees. Like Python.
    (defn fib [n
      (if (<= n 2
          n
          (+ (fib (- n 1
             (fib (- n 2

    ;; BAD
    ;; We're trying to ignore them and you want to give them their own line?
    ;; Hysterically ridiculous.
    (defn fib [
        n
    ]  ; My eyes!
      (if (<= n 2)
        n
        (+ (fib (- n 1)) (fib (- n 2)))
      )
    )  ; GAH, BURN IT WITH FIRE!

2. New lines must ALWAYS be indented past their parent opening bracket.

.. code-block:: clj

    ;; PREFERRED
    (foo (, arg1
            arg2))

    ;; BAD. And evil.
    ;; Same bracket structure as above, but not enough indent.
    (foo (, arg1
      arg2))

    ;; PREFERRED. Same indent as above, but now it matches the brackets.
    (fn [arg]
      arg)

    ;; Remember, when reading Lisp, you ignore the trailing brackets.
    ;; Look at what happens if we remove them.
    ;; Can you tell where they should go by the indentation?

    (foo (, arg1
            arg2

    (foo (, arg1
      arg2

    (fn [arg
      arg

    ;; See how the structure of those last two became indistinguishable?

    ;; Reconstruction of the bad example by indent.
    ;; Not what we started with, is it?
    (foo (, arg1)
      arg2)

    ;; Beware of brackets with reader syntax.
    ;; You still have to indent past them.

    ;; BAD
    `#{(foo)
     ~@[(bar)
      1 2]}

    ;; Above, no trail.
    `#{(foo
     ~@[(bar
      1 2

    ;; Reconstruction. Is. Wrong.
    `#{(foo)}
     ~@[(bar)]
      1 2

    ;; PREFERRED
    `#{(foo)
       ~@[(bar)
          1
          2]}

    ;; OK
    ;; A string is an atom, not a Sequence.
    (foo "abc
      xyz")

    ;; Still readable without trailing brackets.
    (foo "abc
      xyz"  ; Double-quote isn't a closing bracket. Don't ignore it.

3. New lines must NEVER be indented past the previous element's opening bracket.

.. code-block:: clj

    ;; BAD
    ((get-fn q)
      x
      y)

    ;; The above with trailing brackets removed. See the problem?
    ((get-fn q
      x
      y

    ;; By indentation, this is where the brackets should go.
    ((get-fn q
      x
      y))

    ;; OK
    ((get-fn q) x
                y)

    ;; The above without trailing brackets. Still OK (for humans).
    ((get-fn q) x  ; The ) on this line isn't trailing!
                y

    ;; PREFERRED, since the ) should end the line.
    ((get-fn q)
     x
     y)

Limits
------

Follow PEP 8 rules for line limits, viz.

 + 72 columns max for text (docstrings and comments).
 + 79 columns max for other code, OR
 + 99 for other code if primarily maintained by a team that can agree to 99.

Whitespace
----------

AVOID trailing spaces. They suck!

AVOID tabs in code. Indent with spaces only.

PREFER the ``\t`` escape sequence to literal tab characters in one-line string literals.

 + Literal tabs are OK inside multiline strings if you also add a warning comment.
 + But ``\t`` is still PREFERRED in multiline strings.
 + The comment should PREFERABLY appear just before the string.
 + But a blanket warning at the top of a function, class, or file is OK.

Alignment
---------

Line up arguments to function calls when splitting over multiple lines.

 + The first argument PREFERABLY stays on the first line with the function name,
 + but may instead start on the next line indented one space past its parent bracket.

.. code-block:: clj

    ;; PREFERRED. All args aligned with first arg.
    (foofunction arg1
                 (barfunction bararg1
                              bararg2
                              bararg3)  ; Aligned with bararg1.
                 arg3)

    ;; BAD
    (foofunction arg1
                 (barfunction bararg1
                   bararg2  ; Wrong. Looks like a macro body.
                        bararg3)  ; Why?!
                 arg3)

    ;; PREFERRED. Args can all go on one line if it fits.
    (foofunction arg1
                 (barfunction bararg1 bararg2 bararg3)
                 arg3)

    ;; OK. Args not on first line, but still aligned.
    (foofunction
      arg1  ; Indented one column past parent (
      (barfunction
        bararg1  ; Indent again.
        bararg2  ; Aligned with bararg1.
        bararg3)
      arg3)  ; Aligned with arg1.

Hold it Open
------------

If you need to separate a bracket trail use a ``#_ /`` comment to hold it open.
This avoids violating law #1.

.. code-block:: clj

    ;; PREFERRED
    [(foo)
     (bar)
     (baz)]

    ;; OK, especially if the list is long. (Not that three is long.)
    ;; This is better for version control line diffs.
    [  ; Opening brackets can't be "trailing closing brackets" btw.
     (foo)
     (bar)
     (baz)
     #_ /]  ; Nothing to see here. Move along.

    ;; Examples of commenting out items at the end of a list follow.
    ;; As with typing things in the REPL, these cases are less important
    ;; if you're the only one that sees them. But even so, maintaining
    ;; good style can help prevent errors.

    ;; BAD and a syntax error. Lost a bracket.
    [(foo)
     ;; (bar)
     ;; (baz)]

    ;; BAD. Broke law #1.
    [(foo)
     ;; (bar)
     ;; (baz)
     ]

    ;; PREFERRED
    ;; The discard syntax respects code structure,
    ;; so it's less likely to cause errors.
    [(foo)
     #_(bar)
     #_(baz)]

    ;; OK. Adding a final discarded element makes line comments safer.
    [(foo)
     ;; (bar)
     ;; (baz)
     #_ /]

Snuggle
-------

Brackets like to snuggle, don't leave them out in the cold!

.. code-block:: clj

    ;; PREFERRED
    [1 2 3]
    (foo (bar 2))

    ;; BAD
    [ 1 2 3 ]
    ( foo ( bar 2 ) )

    ;; BAD. And ugly.
    [ 1 2 3]
    (foo( bar 2) )

Grouping
--------

Use whitespace to show implicit groups, but be consistent within a form.

.. code-block:: clj

    ;; Older Lisps would typically wrap such groups in even more parentheses.
    ;; (The Common Lisp LOOP macro was a notable exception.)
    ;; But Hy takes after Clojure, which has a lighter touch.

    ;; BAD. Can't tell key from value without counting
    {1 9 2 8 3 7 4 6 5 5}

    ;; PREFERRED. This can fit on one line. Clojure would have used commas
    ;; here, but those aren't whitespace in Hy. Use extra spaces instead.
    {1 9  2 8  3 7  4 6  5 5}

    ;; OK. And preferred if it couldn't fit on one line.
    {1 9
     2 8
     3 7
     4 6
     5 5}  ; Newlines show key-value pairs in dict.

    ;; BAD
    ;; This grouping makes no sense.
    #{1 2
      3 4}  ; It's a set, so why are there pairs?

    ;; BAD
    ;; This grouping also makes no sense. But, it could be OK in a macro or
    ;; something if this grouping was somehow meaningful there.
    [1
     1 2
     1 2 3]  ; wHy do you like random patterns? [sic pun, sorry]

    ;; Be consistent. Separate all groups the same way in a form.

    ;; BAD
    {1 9  2 8
     3 7  4 6  5 5}  ; Pick one or the other!

    ;; BAD
    {1 9  2 8 3 7  4 6  5 5}  ; You forgot something.

    ;; Groups of one must also be consistent.

    ;; PREFERRED
    (foo 1 2 3)  ; No need for extra spaces here.

    ;; OK, but you could have fit this on one line.
    (foo 1
         2
         3)

    ;; OK, but you still could have fit this on one line.
    [1
     2]

    ;; BAD
    (foo 1 2  ; This isn't a pair?
         3)  ; Lines or spaces--pick one or the other!

    ;; PREFERRRED
    (foofunction (make-arg)
                 (get-arg)
                 #tag(do-stuff)  ; Tags belong with what they tag.
                 #* args  ; #* goes with what it unpacks.
                 :foo spam
                 :bar eggs  ; Keyword args are also pairs. Group them.
                 #** kwargs)

    ;; PREFERRED. Spaces divide groups on one line.
    (quux :foo spam  :bar eggs  #* with-spam)
    {:foo spam  :bar eggs}

    ;; OK. The colon is still enough to indicate groups.
    (quux :foo spam :bar eggs #* with-spam)
    {:foo spam :bar eggs}
    ;; OK.
    ("foo" spam "bar" eggs}

    ;; BAD. Can't tell key from value.
    (quux :foo :spam :bar :eggs :baz :bacon)
    {:foo :spam :bar :eggs :baz :bacon}
    {"foo" "spam" "bar" "eggs" "baz" "bacon"}

    ;; PREFERRED
    (quux :foo :spam  :bar :eggs  :baz :bacon)
    {:foo :spam  :bar :eggs  :baz :bacon}
    {"foo" "spam"  "bar" "eggs"  "baz" "bacon"}

    ;; OK. Yep, those are pairs too.
    (setv x 1
          y 2)

    ;; PREFERRED. This fits on one line.
    (setv x 1  y 2)

    ;; BAD. Doesn't separate groups.
    (print (if (< n 0.0)
               "negative"
               (= n 0.0)
               "zero"
               (> n 0.0)
               "positive"
               "not a number"))

    ;; BAD. And evil. Broke law #3. Shows groups but args aren't aligned.
    (print (if (< n 0.0)
                   "negative"
               (= n 0.0)
                   "zero"
               (> n 0.0)
                   "positive"
               "not a number"))

    ;; BAD. Shows groups but args aren't aligned.
    ;; If the then-parts weren't atoms, this would break law #3.
    (print (if (< n 0.0)
             "negative"
               (= n 0.0)
             "zero"
               (> n 0.0)
             "positive"
               "not a number"))

    ;; OK. Redundant (do) forms allow extra indent to show groups
    ;; without violating law #3.
    (print (if (< n 0.0)
               (do
                 "negative")
               (= n 0.0)
               (do
                 "zero")
               (> n 0.0)
               (do
                 "positive")
               "not a number"))

Separate toplevel forms (including toplevel comments not about a particular form)
with a single blank line, rather than two as in Python.

 + This can be omitted for tightly associated forms.

Methods within a defclass need not be separated by blank line.

Special Arguments
-----------------

Macros and special forms are normally indented one space past the parent bracket,
but can also have "special" arguments that are indented like function arguments.

 + Macros with an ``#* body`` argument contain an implicit ``do``.
 + The body is never special, but the arguments before it are.

.. code-block:: clj

    ;; PREFERRED
    (assoc foo  ; foo is special
      "x" 1  ; remaining args are not special. Indent 2 spaces.
      "y" 2)

    ;; PREFERRED
    ;; The do form has no special args. Indent like a function call.
    (do (foo)
        (bar)
        (baz))

    ;; OK
    ;; No special args to distinguish. This is also valid function indent.
    (do
      (foo)
      (bar)
      (baz))

    ;; PREFERRED
    (defn fib [n]
      (if (<= n 2)
          n
          (+ (fib (- n 1))
             (fib (- n 2)))))

    ;; OK
    (defn fib
          [n]  ; name and argslist are special. Indent like function args.
      ;; The defn body is not special. Indent 1 space past parent bracket.
      (if (<= n 2)
          n
        (+ (fib (- n 1))  ; Emacs-style else indent.
           (fib (- n 2)))))

Removing Whitespace
-------------------

Removing whitespace can also make groups clearer.

.. code-block:: clj

    ;; lookups

    ;; OK
    (. foo ["bar"])

    ;; PREFERRED
    (. foo["bar"])

    ;; BAD. Doesn't show groups clearly.
    (import foo foo [spam :as sp eggs :as eg] bar bar [bacon])

    ;; OK. Extra spaces show groups.
    (import foo  foo [spam :as sp  eggs :as eg]  bar  bar [bacon])

    ;; PREFERRED. Removing spaces is even clearer.
    (import foo foo[spam :as sp  eggs :as eg] bar bar[bacon])

    ;; OK. Newlines show groups.
    (import foo
            foo [spam :as sp
                 eggs :as eg]
            bar
            bar [bacon])

    ;; PREFERRED, It's more consistent with the preferred one-line version.
    (import foo
            foo[spam :as sp
                eggs :as eg]
            bar
            bar[bacon])

    ;; Avoid whitespace after tags.

    ;; Note which shows groups better.

    ;; BAD
    (foofunction #tag "foo" #tag (foo) #* (get-args))

    ;; OK
    (foofunction #tag "foo"  #tag (foo)  #* (get-args))

    ;; PREFERRED
    (foofunction #tag"foo" #tag(foo) #*(get-args))

    ;; PREFERRED
    ;; Can't group these by removing whitespace. Use extra spaces instead.
    (foofunction #x foo  #x bar  #* args)

    ;; OK
    ;; Same idea, but this could have fit on one line.
    (foofunction #x foo
                 #x bar
                 #* args)

    ;; OK, but you don't need to separate function name from first arg.
    (foofunction  #x foo  #x bar  #* args)

    ;; OK. But same idea.
    ;; No need to separate the first group from the function name.
    (foofunction
      #x foo
      #x bar
      #* args)

    ;; PREFERRED. It's still clear what this is tagging.
    ;; And you don't have to re-indent.
    #_
    (def foo []
      stuff)

    ;; OK, but more work.
    #_(def foo []
        stuff)

    ;; BAD, you messed up the indent and broke law #2.
    #_(def foo []
      stuff)

    ;; BAD, keep the tag grouped with its argument.
    #_

    (def foo []
      stuff)

Close Bracket, Close Line
-------------------------

A *single* closing bracket SHOULD end the line,
unless it's in the middle of an implicit group.

 + If the forms are small and simple you can maybe leave them on one line.

A *train* of closing brackets MUST end the line.

.. code-block:: clj

    ;; One-liners are overrated.
    ;; Maybe OK if you're just typing into the REPL.
    ;; But even then, maintaining good style can help prevent errors.

    ;; BAD. One-liner is too hard to read.
    (defn fib [n] (if (<= n 2) n (+ (fib (- n 1)) (fib (- n 2)))))

    ;; BAD. Getting better, but the first line is still too complex.
    (defn fib [n] (if (<= n 2) n (+ (fib (- n 1))
                                    (fib (- n 2)))))
    ;; OK. Barely.
    (defn fib [n]
      (if (<= n 2) n (+ (fib (- n 1))  ; This line is pushing it.
                        (fib (- n 2)))))

    ;; OK
    (defn fib [n]  ; Saw a "]", newline.
      (if (<= n 2)  ; OK to break here, since there's only one pair.
          n
        (+ (fib (- n 1))  ; Whitespace separation (Emacs else-indent).
           (fib (- n 2)))))

    ;; OK
    (defn fib [n]  ; Saw a "]", end line. (Margin comments don't count.)
      (if (<= n 2) n  ; Saw a ")", but it's in a pair starting in this line.
          (+ (fib (- n 1))  ; Saw a "))" MUST end line.
             (fib (- n 2)))))

    ;; OK. Pairs.
    (print (if (< n 0.0) "negative"  ; Single ) inside group. No break.
               (= n 0.0) "zero"
               (> n 0.0) "positive"
               :else "not a number"))  ; :else is not magic; True works too.

    ;; OK. Avoided line breaks at single ) to show pairs.
    (print (if (< n 0.0) "negative"
               (= n 0.0) "zero"
               (> n 0.0) (do (do-foo)  ; Single ) inside group. No break.
                             (do-bar)
                             "positive")
               "not a number"))  ; Implicit else is PREFERRED.

    ;; BAD
    (print (if (< n 0.0) "negative"
               (= n 0.0) "zero"
               (and (even? n)
                    (> n 0.0)) "even-positive"  ; Bad. "))" must break.
               (> n 0.0) "positive"
               "not a number"))

    ;; BAD
    (print (if (< n 0.0) "negative"
               (= n 0.0) "zero"
               (and (even? n)
                    (> n 0.0)) (do (do-foo)  ; Y U no break?
                                   (do-bar)
                                   "even-positive")
               (> n 0.0) "positive"
               "not a number"))

    ;; OK. Blank line separates multiline groups.
    (print (if (< n 0.0) "negative"

               (= n 0.0) "zero"

               (and (even? n)
                    (> n 0.0))
               (do (do-foo)
                   (do-bar)
                    "even-positive")

               (> n 0.0) "positive"

               "not a number"))

    ;; BAD. Groups are not separated consistently.
    (print (if (< n 0.0) "negative"
               (= n 0.0) "zero"

               (> n 0.0)
               (do (do-foo)
                   "positive")

               "not a number"))

    ;; OK. Single )'s and forms are simple enough.
    (with [f (open "names.txt")]
      (-> (.read f) .strip (.replace "\"" "") (.split ",") sorted)))

    ;; PREFERRED. Even so, this version is much clearer.
    (with [f (open "names.txt")]
      (-> (.read f)
          .strip
          (.replace "\"" "")
          (.split ",")
          sorted)))

Comments
--------

Prefer docstrings to comments where applicable---in ``fn``, ``defclass``,
at the top of the module, and in any other macros derived from these that can take a docstring
(e.g. ``defmacro/g!``, ``defn``).

Docstrings contents follow the same conventions as Python.

The ``(comment)`` macro is still subject to the three laws.
If you're tempted to violate them, consider discarding a string instead with ``#_``.

Semicolon comments always have one space between the semicolon and the start of the comment.
Also, try to not comment the obvious.

Comments with more than a single word should start with a capital letter and use punctuation.

Separate sentences with a single space.

.. code-block:: clj

    ;; This commentary is not about a particular form.
    ;; These can span multiple lines. Limit them to column 72, per PEP 8.
    ;; Separate them from the next form or form comment with a blank line.

    ;; PREFERRED.
    (setv ind (dec x))  ; Indexing starts from 0,
                                    ; margin comment continues on new line.

    ;; OK
    ;; Style-compliant but just states the obvious.
    (setv ind (dec x))  ; Sets index to x-1.

    ;; BAD
    (setv ind (dec x));typing words for fun

    ;; Comment about the whole foofunction call.
    ;; These can also span multiple lines.
    (foofunction ;; Form comment about (get-arg1). Not a margin comment!
                 (get-arg1)
                 ;; Form comment about arg2. The indent matches.
                 arg2)

Indent form comments at the same level as the form they're commenting about;
they must always start with exactly two semicolons ``;;``.
Form comments appear directly above what they're commenting on, never below.

General toplevel commentary is not indented;
these must always start with exactly two semicolons ``;;``
and be separated from the next form with a blank line.
For long commentary, consider using a ``#_`` applied to a string for this purpose instead.

Margin comments start two spaces from the end of the code; they
must always start with a single semicolon ``;``.
Margin comments may be continued on the next line.

When commenting out entire forms, prefer the ``#_`` syntax.
But if you do need line comments, use the more general double-colon form.

Coding Style
============

Pythonic Names
--------------

Use Python's naming conventions where still applicable to Hy.

 + The first parameter of a method is ``self``,
 + of a classmethod is ``cls``.

Threading Macros
----------------

PREFER the threading macro or the threading tail macros when encountering
deeply nested s-expressions. However, be judicious when using them. Do
use them when clarity and readability improves; do not construct
convoluted, hard to understand expressions.

.. code-block:: clj

    ;; BAD. Not wrong, but could be much clearer with a threading macro.
    (setv NAMES
      (with [f (open "names.txt")]
        (sorted (.split (.replace (.strip (.read f))
                                  "\""
                                  "")
                        ","))))

    ;; PREFERRED. This compiles exactly the same way as the above.
    (setv NAMES
      (with [f (open "names.txt")]
        (-> (.read f)
            .strip
            (.replace "\"" "")
            (.split ",")
            sorted)))

    ;; BAD. Probably. The macro makes it less clear in this case.
    (defn square? [x]
      (->> 2
           (pow (int (sqrt x)))
           (= x)))

    ;; OK. Much clearer than the previous example above.
    (defn square? [x]
      (-> x
          sqrt
          int
          (pow 2)
          (= x))

    ;; PREFERRED. Judicious use.
    ;; You don't have to thread everything if it improves clarity.
    (defn square? [x]
      (= x (-> x sqrt int (pow 2))))

    ;; OK. Still clear enough with no threading macro this time.
    (defn square? [x]
      (= x (pow (int (sqrt x))  ; saw a "))", break.
                2))  ; aligned with first arg to pow


Method Calls
------------

Clojure-style dot notation is PREFERRED over the direct call of
the object's method, though both will continue to be supported.

.. code-block:: clj

     ;; PREFERRED
     (with [fd (open "/etc/passwd")]
       (print (.readlines fd)))

     ;; OK
     (with [fd (open "/etc/passwd")]
       (print (fd.readlines)))

Use More Arguments
------------------

PREFER using multiple arguments to multiple forms.
But judicious use of redundant forms can clarify intent.
AVOID the separating blank line for toplevel forms in this case.

.. code-block:: clj

    ;; BAD
    (setv x 1)
    (setv y 2)
    (setv z 3)
    (setv foo 9)
    (setv bar 10)

    ;; OK
    (setv x 1
          y 2
          z 3
          foo 9
          bar 10)

    ;; PREFERRED
    (setv x 1
          y 2
          z 3)
    (setv foo 9
          bar 10)

Imports
-------

As in Python, group imports.

 + Standard library imports (including Hy's) first.
 + Then third-party modules,
 + and finally internal modules.

PREFER one import form for each group.

PREFER alphabetical order within groups.

Require macros before any imports and group them the same way.

But sometimes imports are conditional or must be ordered a certain way for programmatic reasons, which is OK.

.. code-block:: clj

    ;; PREFERRED
    (require hy.extra.anaphoric [%])
    (require thirdparty [some-macro])
    (require mymacros [my-macro])

    (import json re)
    (import numpy :as np
            pandas :as pd)
    (import mymodule1)

Underscores
-----------

Prefer hyphens when separating words.

+ PREFERRED ``foo-bar``
+ BAD ``foo_bar``

Don't use leading hyphens, except for "operators" or symbols meant to be read as including one,
e.g. ``-Inf``, ``->foo``.

Prefix private names with an underscore, not a dash.
to avoid confusion with negated literals like ``-Inf``, ``-42`` or ``-4/2``.

+ PREFERRED ``_x``
+ BAD ``-x``

Write Python's magic "dunder" names the same as in Python.
Like ``__init__``, not ``--init--`` or otherwise,
to be consistent with the private names rule above.

Private names should still separate words using dashes instead of underscores,
to be consistent with non-private parameter names and such that need the same name sans prefix,
like ``foo-bar``, not ``foo_bar``.

+ PREFERRED ``_foo-bar``
+ BAD ``_foo_bar``


.. code-block:: clj

    ;; BAD
    ;; What are you doing?
    (_= spam 2)  ; Throwing it away?
    (_ 100 7)  ; i18n?

    ;; PREFERRED
    ;; Clearly subtraction.
    (-= spam 2)
    (- 100 7)

    ;; BAD
    ;; This looks weird.
    (_>> foo bar baz)

    ;; PREFERRED
    ;; OH, it's an arrow!
    (->> foo bar baz)

    ;; Negative x?
    (setv -x 100)  ; BAD. Unless you really meant that?

    ;; PREFERRED
    ;; Oh, it's just a module private.
    (setv _x 100)

    ;; BAD
    (class Foo []
      (defn __init-- [self] ...))

    ;; OK
    (class Foo []
      ;; Less weird?
      (defn --init-- [self] ...))

    ;; PREFERRED
    (class Foo []
      (defn __init__ [self] ...))

    ;; OK, but would be module private. (No import *)
    (def ->dict [#* pairs]
      (dict (partition pairs)))

Thanks
======

+ This guide is heavily inspired from `@paultag`_ 's blog post `Hy Survival Guide`_
+ The `Clojure Style Guide`_
+ `Parinfer`_ and `Parlinter`_ (the three laws)
+ The Community Scheme Wiki `scheme-style`_ (ending bracket ends the line)
+ `Riastradh's Lisp Style Rules`_ (Lisp programmers do not ... Azathoth forbid, count brackets)

.. _`Hy Survival Guide`: https://notes.pault.ag/hy-survival-guide/
.. _`Clojure Style Guide`: https://github.com/bbatsov/clojure-style-guide
.. _`@paultag`: https://github.com/paultag
.. _`Parinfer`: https://shaunlebron.github.io/parinfer/
.. _`Parlinter`: https://github.com/shaunlebron/parlinter
.. _`scheme-style`: http://community.schemewiki.org/?scheme-style
.. _`Comment-Tips`: https://www.gnu.org/software/emacs/manual/html_node/elisp/Comment-Tips.html
.. _`Riastradh's Lisp Style Rules`: http://mumble.net/~campbell/scheme/style.txt
