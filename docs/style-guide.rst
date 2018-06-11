==============
Hy Style Guide
==============

   “You know, Minister, I disagree with Dumbledore on many counts…but
   you cannot deny he’s got style…”
   — Phineas Nigellus Black, *Harry Potter and the Order of the Phoenix*

The Hy style guide intends to be a set of ground rules for the Hyve
(yes, the Hy community prides itself in appending Hy to everything)
to write idiomatic Hy code. Hy derives a lot from Clojure & Common
Lisp, while always maintaining Python interoperability.


Prelude
=======

The Tao of Hy
-------------

.. code-block:: none

   Ummon asked the head monk, "What sutra are you lecturing on?"
   "The Nirvana Sutra."
   "The Nirvana Sutra has the Four Virtues, hasn't it?"
   "It has."
   Ummon asked, picking up a cup, "How many virtues has this?"
   "None at all," said the monk.
   "But ancient people said it had, didn't they?" said Ummon.
   "What do you think of what they said?"
   Ummon struck the cup and asked, "You understand?"
   "No," said the monk.
   "Then," said Ummon, "You'd better go on with your lectures on the sutra."
   — the (koan) macro

The following illustrates a brief list of design decisions that went
into the making of Hy.

+ Look like a Lisp; DTRT with it (e.g. dashes turn to underscores).
+ We're still Python. Most of the internals translate 1:1 to Python internals.
+ Use Unicode everywhere.
+ Fix the bad decisions in Python 2 when we can (see ``true_division``).
+ When in doubt, defer to Python.
+ If you're still unsure, defer to Clojure.
+ If you're even more unsure, defer to Common Lisp.
+ Keep in mind we're not Clojure. We're not Common Lisp. We're
  Homoiconic Python, with extra bits that make sense.


Layout & Indentation
====================

The #1 complaint about Lisp?
"It's too weird looking with all those parentheses! How do you even *read* that?"
And they're right! Lisp was originally much too hard to read.
Then they figured out indentation. And it was glorious.

The Three Laws
--------------

Here's the secret: *Real Lispers don't count the brackets.*
When reading Lisp, disregard the trailing brackets--those are for the computer, not the human.
As in Python, read the code structure by indentation.
These are the three laws that make this possible.

1. Brackets must *never* be left alone, sad and lonesome on their own line.

   .. code-block:: clj

    ;; Good (and preferred)
    (defn fib [n]
      (if (<= n 2)
          n
          (+ (fib (- n 1))
             (fib (- n 2)))))

    ;; Hysterically ridiculous
    (defn fib [
        n
    ]  ; my eyes!
      (if (<= n 2)
        n
        (+ (fib (- n 1)) (fib (- n 2)))
      )
    )  ; GAH, BURN IT WITH FIRE

2. New lines must *always* be indented past their parent opening bracket.

   .. code-block:: clj

    ;; Acceptable
    (foo (, arg1
            arg2))

    ;; Unacceptable
    (foo (, arg1
      arg2))  ; Doesn't go far enough.

    ;; Look at what happens if we remove the trailing brackets from the above examples.
    ;; Can you tell where they go?

    (foo (, arg1
            arg2

    (foo (, arg1
      arg2

    ;; Judging by indentation, this is where the brackets should go.

    (foo (, arg1
            arg2))

    (foo (, arg1)  ; not what we started with, is it?
      arg2)

    ;; No, it's not at all obvious it should have gone the other way.

    (fn [arg
      arg

    (fn [arg]
      arg)

    ;; Beware of brackets with reader syntax. You still have to indent past them.

    ;; NO!
    `#{(foo)
     ~@[(bar)
      1 2]}

    ;; Good.
    `#{(foo)
       ~@[(bar)
          1
          2]}

3. New lines must *never* be indented past the previous element's opening bracket.

   .. code-block:: clj

    ;; BAD.
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

    ;; acceptable
    ((get-fn q) x  ; the ")" on this line isn't trailing.
                y)

    ;; preferred, since the ) should end the line.
    ((get-fn q)
     x
     y)

Furthermore
-----------

+ Avoid trailing spaces. They suck!

+ Limit lines to 100 characters.

+ Line up arguments to function calls when splitting over multiple lines.

  .. code-block:: clj

    (foofunction arg1
                 (barfunction bararg1
                              bararg2
                              bararg3)  ; aligned with bararg1
                 arg3)

    (foofunction arg1
                 (barfunction bararg1
                   bararg2)  ; Wrong. Looks like a macro body.
                 arg3)

    (foofunction arg1
                 (barfunction bararg1 bararg2 bararg3)  ; acceptable.
                 arg3)

    ;; indenting one space past the parent bracket is acceptable for long lines
    (foofunction
      arg1  ; acceptable, but better to keep it on the same line as foofunction
      (barfunction
        bararg1  ; indent again
        bararg2
        bararg3)
      arg3)  ; aligned with arg1

+ If you need to separate a bracket trail use a ``#_ /`` comment to hold it open.
  (This avoids violating law #1.)

  .. code-block:: clj

    ;; There are basically two reasons to do this--long lists under version control,
    ;; and when commenting out the final element during testing.
    ;; (Common Lisp might use #+(or) for this.)

    ;; preferred
    [(foo)
     (bar)
     (baz)]

    ;; Acceptable if the list is long. (Three isn't that long though.)
    ;; This is better for version control line diffs.
    [
     (foo)
     (bar)
     (baz)
     #_ /]

    ;; Unacceptable and an syntax error. Lost a bracket.
    [(foo)
     ;; (bar)
     ;; (baz)]

    ;; Unacceptable. Broke law #1.
    [(foo)
     ;; (bar)
     ;; (baz)
     ]

    ;; preferred
    [(foo)
     #_(bar)
     #_(baz)]

    ;; acceptable
    [(foo)
     #_
     (bar)
     #_
     (baz)]

    ;; acceptable
    [(foo)
     ;; (bar)
     ;; (baz)
     #_ /]

+ Brackets like to snuggle, don't leave them out in the cold!

  .. code-block:: clj

    ;;; Good
    [1 2 3]
    (foo (bar 2))

    ;;; Bad
    [ 1 2 3 ]
    ( foo ( bar 2 ) )

    ;;; Ugly
    [ 1 2 3]
    (foo( bar 2) )

+ Use whitespace to show implicit groups, but be consistent within a form.

  .. code-block:: clj

    ;; Older Lisps would always wrap such groups in even more parentheses.
    ;; But Hy takes after Clojure, which has a lighter touch.

    {1 9
     2 8
     3 7
     4 6
     5 5}  ; newlines show key-value pairs in dict

    ;; This grouping makes no sense.
    #{1 2
      3 4}  ; It's a set, so why are there pairs?

    ;; This grouping also makes no sense.
    [1
     1 2
     1 2 3]  ; wHy do you like random patterns? [sic pun, sorry]

    ;; BAD. Can't tell key from value without counting
    {1 9 2 8 3 7 4 6 5 5}

    ;; Good. Extra spaces can work too, if it fits on one line.
    {1 9  2 8  3 7  4 6  5 5}

    ;; Be consistent. Separate all groups the same way in a form.

    {1 9  2 8
     3 7  4 6  5 5}  ; Pick one or the other!
    {1 9  2 8 3 7  4 6  5 5}  ; You forgot something.

    ;; Groups of one must also be consistent.

    (foo 1 2 3}  ; No need for extra spaces here.
    (foo 1
         2
         3}  ; Also acceptable, but you could have fit this on one line.
    [1
     2]  ; same
    (foo 1 2  ; This isn't a pair?
         3)  ; Lines or spaces--pick one or the other!

    (foofunction (make-arg)
                 (get-arg)
                 #tag(do-stuff)  ; Tags belong with what they tag.
                 #* args  ; #* goes with what it unpacks.
                 #** kwargs)

    ;; Yep, those are pairs too.
    (setv x 1
          y 2)

+ Macros and special forms can have "special" arguments that are indented like function arguments.

+ Indent the non-special arguments (usually the body) one space past the parent bracket.

  .. code-block:: clj

    (assoc foo  ; foo is special
      "x" 1  ; remaining args are not special. Indent 2 spaces.
      "y" 2)

    ;; The do form has no special args. Indent like a function call.
    (do (foo)
        (bar)
        (baz))

    ;; No special args to distinguish, so this is also valid function indent.
    (do
      (foo)
      (bar)
      (baz))

     ;; Preferred.
     (defn fib [n]
       (if (<= n 2)
           n
           (+ (fib (- n 1))  ; else clause is not special, but aligning it is OK.
              (fib (- n 2)))))

     (defn fib
           [n]  ; name and argslist are special. Indent like function args.
       ;; defn body is not special. Indent 1 space past parent bracket.
       (if (<= n 2)
           n  ; elif pairs are special, indent like function args
         (+ (fib (- n 1))  ; else clause is not special. Indent 1 space past parent bracket.
            (fib (- n 2)))))


+ Removing whitespace can also make groups clearer.

  .. code-block:: clj

    ;;; lookups
    ;; acceptable
    (. foo ["bar"])
    ;; preferred
    (. foo["bar"])

    ;; Bad. Doesn't show groups clearly
    (import foo foo [spam :as sp eggs :as eg] bar bar [bacon])

    ;; Acceptable. Extra spaces show groups.
    (import foo  foo [spam :as sp  eggs :as eg]  bar  bar [bacon])
    ;; Preferred. Removing spaces is even clearer.
    (import foo foo[spam :as sp  eggs :as eg] bar bar[bacon])

    ;; Acceptable. Newlines show groups.
    (import foo
            foo [spam :as sp
                 eggs :as eg]
            bar
            bar [bacon])
    ;; Preferred, since it's more consistent with the preferred one-line version.
    (import foo
            foo[spam :as sp
                eggs :as eg]
            bar
            bar[bacon])

    ;;; avoid whitespace after tags

    ;; Note which shows groups better.

    (foofunction #tag "foo" #tag (foo) #* (get-args))

    (foofunction #tag"foo" #tag(foo) #*(get-args))

    ;; Can't group these by removing whitespace, so use extra spaces instead.
    (foofunction #x foo  #x bar  #* args)

    ;; Same idea.
    (foofunction #x foo
                 #x bar
                 #* args)

    ;; Acceptable, but you don't need to separate function name from first arg.
    (foofunction  #x foo  #x bar  #* args)

    ;; Same idea. Keeping the first group on the same line as the function name is preferable.
    (foofunction
      #x foo
      #x bar
      #* args)

    ;; OK. It's still clear what this is tagging. And you don't have to re-indent.
    #_
    (def foo []
      stuff)

    ;; also OK, but more work.
    #_(def foo []
        stuff)

    ;; Not OK, you messed up the indent and broke law #2.
    #_(def foo []
      stuff)

    ;; Not OK, keep the tag grouped with its argument.
    #_

    (def foo []
      stuff)

+ Any closing bracket(s) (of any kind) must end the line,
  unless it's in the middle of an implicit group that started on the line.

  .. code-block:: clj

    ;; One-liners are overrated.
    ;; Maybe OK if you're just typing into the REPL.
    (defn fib [n] (if (<= n 2) n (+ (fib (- n 1)) (fib (- n 2)))))  ; too hard to read!

    ;; getting better.
    (defn fib [n]
      (if (<= n 2)
          n
          (+ (fib (- n 1)) (fib (- n 2)))))  ; still too hard on this line

    ;; How to do it.
    (defn fib [n]  ; Saw a "]", newline.
      (if (<= n 2) n  ; Saw a ")", but leave it since it's in a semantic pair starting in this line.
          (+ (fib (- n 1))  ; Saw a "))" line break.
             (fib (- n 2)))))

    ;; Acceptable. Pairs.
    (print (if (< n 0.0) "negative"
               (= n 0.0) "zero"
               (> n 0.0) "positive"
               :else "not a number"))  ; :else is not magic; True would work also.

    ;; Bad. Doesn't separate groups.
    (print (if (< n 0.0)
               "negative"
               (= n 0.0)
               "zero"
               (> n 0.0)
               "positive"
               "not a number"))

    ;; This is also acceptable.
    (print (if (< n 0.0) "negative"
               (= n 0.0) "zero"
               (> n 0.0) (do (do-foo)  ; Group started this line, so didn't break.
                             (do-bar)
                             "positive")
               "not a number"))  ; :else is implied for the last one.

    ;; Bad.
    (print (if (< n 0.0) "negative"
               (= n 0.0) "zero"
               (and (even? n)
                    (> n 0.0)) "even-positive"  ; Group not started this line! Should break on "))"
               (> n 0.0) "positive"
               "not a number"))

    ;; Worse.
    (print (if (< n 0.0) "negative"
               (= n 0.0) "zero"
               (and (even? n)
                    (> n 0.0)) (do (do-foo)  ; Group not started this line.
                                   (do-bar)
                                   "even-positive")
               (> n 0.0) "positive"
               "not a number"))

    ;; Good. Blank line separates groups.
    (print (if (< n 0.0) "negative"

               (= n 0.0) "zero"

               (and (even? n)
                    (> n 0.0))
               (do (do-foo)
                   (do-bar)
                    "even-positive")

               (> n 0.0) "positive"

               "not a number"))

    ;; Not so good, groups are not separated consistently.
    (print (if (< n 0.0) "negative"
               (= n 0.0) "zero"

               (> n 0.0)
               (do (do-foo)
                   "positive")

               "not a number"))

    ;; Acceptable. All groups are separated the same way, with a blank like.
    (print (if (< n 0.0) "negative"

               (= n 0.0) "zero"

               (> n 0.0)
               (do (do-foo)
                   "positive")

               "not a number"))

    (defn fib [n]  ; saw a "]", newline.
      (if (<= n 2)  ; OK to break here. Since there's only one pair, we don't have to separate them.
          n
        (+ (fib (- n 1))  ; non-special indent is another whitespace separation technique.
           (fib (- n 2)))))

Comments
--------

Prefer docstrings to comments where applicable--in ``defn``, ``defclass``, and at the top of the module.

The ``(comment)`` macro is still subject to the three laws.
If you're tempted to violate them, consider discarding a string instead with ``#_``.

Semicolon comments shall start with some number of semicolons
and have a space between the semicolons and the start of the comment.
Also, try to not comment the obvious.

.. code-block:: clj

    ;;;; Major Header Labeling a Major Section
    ;; Headers should only be one line.
    ;; This is non-header commentary, but not about a particular form.
    ;; These can span multiple lines.
    ;; These are separated from the next form or form comment by a blank line.

    ;; Good.
    (setv ind (dec x))  ; indexing starts from 0
                                            ; margin comment continues on the next line.

    ;; Style-compliant but just states the obvious.
    (setv ind (dec x))  ; sets index to x-1

    ;; Bad.
    (setv ind (dec x));typing words for fun

    ;;; Minor Header Comment Labeling a Minor Section

    ;; Comment about the whole foofunction call.
    ;; These can also span mulitple lines.
    (foofunction ;; Form comment about (get-arg1). Not a margin comment!
                 (get-arg1)
                 ;; Form comment about arg2. The indent matches.
                 arg2)

    ;;;; Footer


Header comments shall not be indented, and shall appear only at the toplevel outside of any form.
They must always begin with at least three semicolons--usually ``;;;`` for minor and ``;;;;`` for major headings.
(Emacs recognizes these as headers.)

Form comments shall be indented at the same level as the form they're commenting about;
they must always start with exactly two semicolons ``;;``.
Form comments appear directly above what they're commenting on, never below.

General toplevel commentary shall not be indented;
they must always start with exactly two semicolons ``;;``
and be separated from the next form with a blank line.
For long commentary, consider using a ``#_`` applied to a string for this purpose instead.

Margin comments shall be two spaces from the end of the code; they
must always start with a single semicolon ``;``.
Margin comments may be continued on the next line.

When commenting out entire forms, prefer the ``#_`` syntax.
But if you do need line comments, use the more general double-colon form,
since they're not headers that should appear in the outline,
nor are they margin comment continuations that should be indented automatically.


Coding Style
============

+ Use the threading macro or the threading tail macros when encountering
  deeply nested s-expressions. However, be judicious when using them. Do
  use them when clarity and readability improves; do not construct
  convoluted, hard to understand expressions.

  .. code-block:: clj

    ;; Not so good.
    (setv *names*
      (with [f (open "names.txt")]
        (sorted (.split (.replace (.strip (.read f))
                                  "\""
                                  "")
                        ","))))

    ;; Preferred.
    (setv *names*
      (with [f (open "names.txt")]
        (-> (.read f)
            .strip
            (.replace "\"" "")
            (.split ",")
            sorted)))

    ;; Probably not a good idea.
    (setv square? [x]
      (->> 2
           (pow (int (sqrt x)))
           (= x)))

    ;; better
    (setv square? [x]
      (-> x
          sqrt
          int
          (pow 2)
          (= x))

    ;; good
    (setv square? [x]
      (= x (-> x sqrt int (pow 2))))

    ;; still OK
    (setv square? [x]
      (= x (pow (int (sqrt x))
                2))


+ Clojure-style dot notation is preferred over the direct call of
  the object's method, though both will continue to be supported.

  .. code-block:: clj

     ;; Good.
     (with [fd (open "/etc/passwd")]
       (print (.readlines fd)))

     ;; Not so good.
     (with [fd (open "/etc/passwd")]
       (print (fd.readlines)))

+ Prefer hyphens when separating words. ``foo-bar``, not ``foo_bar``.

+ Don't use leading hyphens, except for "operators".

  .. code-block:: clj

    ;; Clearly subtraction.
    (-= spam 2)
    (- 100 7)

    ;; What are you doing?
    (_= spam 2)
    (_ 100 7)

    ;; This looks weird.
    (_>> foo bar baz)

    ;; OH, it's an arrow!
    (->> foo bar baz)

    ;; Negative spam???
    (setv -spam 100)

    ;; Oh, it's just a module private.
    (setv _spam 100)

    (class Foo []
      ;; Also weird.
      (defn __init-- [self] ...))

    (class Foo []
      ;; Less weird?
      (defn --init-- [self] ...))

    (class Foo []
      ;; Preferred!
      (defn __init__ [self] ...))

    ;; This kind of name is OK, but would be module private. (No import *)
    (def ->dict [&rest pairs]
      (dict (partition pairs)))

Conclusion
==========

   “Fashions fade, style is eternal”
   —Yves Saint Laurent


This guide is just a set of community guidelines, and obviously, community
guidelines do not make sense without an active community. Contributions are
welcome. Join us at #hy in freenode, blog about it, tweet about it, and most
importantly, have fun with Hy.


Thanks
======

+ This guide is heavily inspired from `@paultag`_ 's blog post `Hy Survival Guide`_
+ The `Clojure Style Guide`_
+ `Parinfer`_ and `Parlinter`_ (the three laws)
+ The Community Scheme Wiki `scheme-style`_ (ending bracket ends the line)
+ GNU Emacs Lisp Reference Manual `Comment-Tips`_ (how many semicolons?)
+ `Riastradh's Lisp Style Rules`_

.. _`Hy Survival Guide`: https://notes.pault.ag/hy-survival-guide/
.. _`Clojure Style Guide`: https://github.com/bbatsov/clojure-style-guide
.. _`@paultag`: https://github.com/paultag
.. _`Parinfer`: https://shaunlebron.github.io/parinfer/
.. _`Parlinter`: https://github.com/shaunlebron/parlinter
.. _`scheme-style`: http://community.schemewiki.org/?scheme-style
.. _`Comment-Tips`: https://www.gnu.org/software/emacs/manual/html_node/elisp/Comment-Tips.html
.. _`Riastradh's Lisp Style Rules`: http://mumble.net/~campbell/scheme/style.txt
