==============
Hy Style Guide
==============

   “You know, Minister, I disagree with Dumbledore on many counts…but
   you cannot deny he’s got style…”
   — Phineas Nigellus Black, *Harry Potter and the Order of the Phoenix*

The Hy style guide intends to be a set of ground rules for the Hyve
(yes, the Hy community prides itself in appending Hy to everything)
to write idiomatic Hy code. Hy derives a lot from Clojure & Common
Lisp, while always maintaining Python interopability.


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

+ Look like a Lisp; DTRT with it (e.g. dashes turn to underscores, earmuffs
  turn to all-caps).
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

+ Avoid trailing spaces. They suck!

+ Indentation shall be 2 spaces (no hard tabs), except when matching
  the indentation of the previous line.

  .. code-block:: clj

     ;; Good (and preferred)
     (defn fib [n]
       (if (<= n 2)
         n
         (+ (fib (- n 1)) (fib (- n 2)))))

     ;; Still okay
     (defn fib [n]
       (if (<= n 2) n (+ (fib (- n 1)) (fib (- n 2)))))

     ;; Still okay
     (defn fib [n]
       (if (<= n 2)
         n
         (+ (fib (- n 1)) (fib (- n 2)))))

     ;; Hysterically ridiculous
     (defn fib [n]
         (if (<= n 2)
                 n ;; yes, I love randomly hitting the space key
           (+ (fib (- n 1)) (fib (- n 2)))))


+ Parentheses must *never* be left alone, sad and lonesome on their own
  line.

  .. code-block:: clj

    ;; Good (and preferred)
    (defn fib [n]
      (if (<= n 2)
        n
        (+ (fib (- n 1)) (fib (- n 2)))))

    ;; Hysterically ridiculous
    (defn fib [n]
      (if (<= n 2)
        n
        (+ (fib (- n 1)) (fib (- n 2)))
      )
    )  ; GAH, BURN IT WITH FIRE


+ Vertically align ``let`` blocks.

  .. code-block:: clj

     (let [[foo (bar)]
           [qux (baz)]]
        (foo qux))


+ Inline comments shall be two spaces from the end of the code; they
  must always have a space between the comment character and the start
  of the comment. Also, try to not comment the obvious.

.. code-block:: clj

   ;; Good
   (setv ind (dec x))  ; indexing starts from 0

   ;; Style-compliant but just states the obvious
   (setv ind (dec x))  ; sets index to x-1

   ;; Bad
   (setv ind (dec x));typing words for fun


Coding Style
============

+ As a convention, try not to use ``def`` for anything other than global
  variables; use ``setv`` inside functions, loops, etc.

  .. code-block:: clj

     ;; Good (and preferred)
     (def *limit* 400000)

     (defn fibs [a b]
       (while true
         (yield a)
         (setv (, a b) (, b (+ a b)))))

     ;; Bad (and not preferred)
     (defn fibs [a b]
       (while true
         (yield a)
         (def (, a b) (, b (+ a b)))))


+ Do not use s-expression syntax where vector syntax is intended.
  For instance, the fact that the former of these two examples works
  is just because the compiler isn't overly strict. In reality, the
  correct syntax in places such as this is the latter.

  .. code-block:: clj

     ;; Bad (and evil)
     (defn foo (x) (print x))
     (foo 1)

     ;; Good (and preferred)
     (defn foo [x] (print x))
     (foo 1)


+ Use the threading macro or the threading tail macros when encountering
  deeply nested s-expressions. However, be judicious when using them. Do
  use them when clarity and readability improves; do not construct
  convoluted, hard to understand expressions.

  .. code-block:: clj

     ;; Preferred
     (def *names*
       (with [f (open "names.txt")]
         (-> (.read f) (.strip) (.replace "\"" "") (.split ",") (sorted))))

     ;; Not so good
     (def *names*
       (with [f (open "names.txt")]
       (sorted (.split "," (.replace "\"" "" (.strip (.read f)))))))

     ;; Probably not a good idea
     (defn square? [x]
       (->> 2 (pow (int (sqrt x))) (= x)))


+ Clojure-style dot notation is preferred over the direct call of
  the object's method, though both will continue to be supported.

  .. code-block:: clj

     ;; Good
     (with [fd (open "/etc/passwd")]
       (print (.readlines fd)))

     ;; Not so good
     (with [fd (open "/etc/passwd")]
       (print (fd.readlines)))


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

+ This guide is heavily inspired from `@paultag`_ 's blog post `Hy
  Survival Guide`_
+ The `Clojure Style Guide`_

.. _`Hy Survival Guide`: http://notes.pault.ag/hy-survival-guide/
.. _`Clojure Style Guide`: https://github.com/bbatsov/clojure-style-guide
.. _`@paultag`: https://github.com/paultag
