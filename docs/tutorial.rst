========
Tutorial
========

.. TODO
..
..  - How do I index into arrays or dictionaries?
..  - How do I do array ranges?  e.g. x[5:] or y[2:10]
..  - Blow your mind with macros!
..  - Where's my banana???
..  - Mention that you can import .hy files in .py files and vice versa!

Welcome to the Hy tutorial!

In a nutshell, Hy is a Lisp dialect, but one that converts its
structure into Python ... literally a conversion into Python's abstract
syntax tree!  (Or to put it in more crude terms, Hy is lisp-stick on a
Python!)

This is pretty cool because it means Hy is several things:

 - A Lisp that feels very Pythonic
 - For Lispers, a great way to use Lisp's crazy powers but in the wide
   world of Python's libraries (why yes, you now can write a Django
   application in Lisp!)
 - For Pythonistas, a great way to start exploring Lisp, from the
   comfort of Python!
 - For everyone: a pleasant language that has a lot of neat ideas!


Basic intro to Lisp for Pythonistas
===================================

Okay, maybe you've never used Lisp before, but you've used Python!

A "hello world" program in Hy is actually super simple. Let's try it:

.. code-block:: clj

   (print "hello world")

See?  Easy!  As you may have guessed, this is the same as the Python
version of::

  print "hello world"

To add up some super simple math, we could do:

.. code-block:: clj

   (+ 1 3)

Which would return 4 and would be the equivalent of:

.. code-block:: clj

   1 + 3

What you'll notice is that the first item in the list is the function
being called and the rest of the arguments are the arguments being
passed in.  In fact, in Hy (as with most Lisps) we can pass in
multiple arguments to the plus operator:

.. code-block:: clj

   (+ 1 3 55)

Which would return 59.

Maybe you've heard of Lisp before but don't know much about it.  Lisp
isn't as hard as you might think, and Hy inherits from Python, so Hy
is a great way to start learning Lisp.  The main thing that's obvious
about Lisp is that there's a lot of parentheses.  This might seem
confusing at first, but it isn't so hard.  Let's look at some simple
math that's wrapped in a bunch of parentheses that we could enter into
the Hy interpreter:

.. code-block:: clj

   (setv result (- (/ (+ 1 3 88) 2) 8))

This would return 38.  But why?  Well, we could look at the equivalent
expression in python::

  result = ((1 + 3 + 88) / 2) - 8

If you were to try to figure out how the above were to work in python,
you'd of course figure out the results by solving each inner
parenthesis.  That's the same basic idea in Hy.  Let's try this
exercise first in Python::

  result = ((1 + 3 + 88) / 2) - 8
  # simplified to...
  result = (92 / 2) - 8
  # simplified to...
  result = 46 - 8
  # simplified to...
  result = 38

Now let's try the same thing in Hy:

.. code-block:: clj

   (setv result (- (/ (+ 1 3 88) 2) 8))
   ; simplified to...
   (setv result (- (/ 92 2) 8))
   ; simplified to...
   (setv result (- 46 8))
   ; simplified to...
   (setv result 38)

As you probably guessed, this last expression with ``setv`` means to
assign the variable "result" to 38.

See?  Not too hard!

This is the basic premise of Lisp. Lisp stands for "list
processing"; this means that the structure of the program is
actually lists of lists.  (If you're familiar with Python lists,
imagine the entire same structure as above but with square brackets
instead, any you'll be able to see the structure above as both a
program and a datastructure.)  This is easier to understand with more
examples, so let's write a simple Python program, test it, and then
show the equivalent Hy program::

  def simple_conversation():
      print "Hello!  I'd like to get to know you.  Tell me about yourself!"
      name = raw_input("What is your name? ")
      age = raw_input("What is your age? ")
      print "Hello " + name + "!  I see you are " + age + " years old."

  simple_conversation()

If we ran this program, it might go like::

  Hello!  I'd like to get to know you.  Tell me about yourself!
  What is your name? Gary
  What is your age? 38
  Hello Gary!  I see you are 38 years old.

Now let's look at the equivalent Hy program:

.. code-block:: clj

   (defn simple-conversation []
      (print "Hello!  I'd like to get to know you.  Tell me about yourself!")
      (setv name (raw-input "What is your name? "))
      (setv age (raw-input "What is your age? "))
      (print (+ "Hello " name "!  I see you are "
                 age " years old.")))

   (simple-conversation)

If you look at the above program, as long as you remember that the
first element in each list of the program is the function (or
macro... we'll get to those later) being called and that the rest are
the arguments, it's pretty easy to figure out what this all means.
(As you probably also guessed, ``defn`` is the Hy method of defining
methods.)

Still, lots of people find this confusing at first because there's so
many parentheses, but there are plenty of things that can help make
this easier: keep indentation nice and use an editor with parenthesis
matching (this will help you figure out what each parenthesis pairs up
with) and things will start to feel comfortable.

There are some advantages to having a code structure that's actually a
very simple data structure as the core of Lisp is based on.  For one
thing, it means that your programs are easy to parse and that the
entire actual structure of the program is very clearly exposed to you.
(There's an extra step in hy where the structure you see is converted
to Python's own representations ... in "purer" Lisps such as Common
Lisp or Emacs Lisp, the data structure you see in the code and the
data structure that is executed is much more literally close.)

Another implication of this is macros: if a program's structure is a
simple data structure, that means you can write code that can write
code very easily, meaning that implementing entirely new language
features can be very fast.  Previous to Hy, this wasn't very possible
for Python programmers ... now you too can make use of macros'
incredible power (just be careful to not aim them footward)!


Hy is a Lisp-flavored Python
============================

Hy converts to Python's own abstract syntax tree, so you'll soon start
to find that all the familiar power of python is at your fingertips.

You have full access to Python's data types and standard library in
Hy.  Let's experiment with this in the hy interpreter::

  => [1 2 3]
  [1, 2, 3]
  => {"dog" "bark"
  ... "cat" "meow"}
  ...
  {'dog': 'bark', 'cat': 'meow'}
  => (, 1 2 3)
  (1, 2, 3)

If you are familiar with other Lisps, you may be interested that Hy
supports the Common Lisp method of quoting:

.. code-block:: clj

   => '(1 2 3)
   (1L 2L 3L)

You also have access to all the built-in types' nice methods::

  => (.strip " fooooo   ")
  "fooooo"

What's this?  Yes indeed, this is precisely the same as::

  " fooooo   ".strip()

That's right---Lisp with dot notation!  If we have this string
assigned as a variable, we can also do the following:

.. code-block:: clj

   (setv this-string " fooooo   ")
   (this-string.strip)

What about conditionals?:

.. code-block:: clj

   (if (try-some-thing)
     (print "this is if true")
     (print "this is if false"))

As you can tell above, the first argument to ``if`` is a truth test, the
second argument is the body if true, and the third argument (optional!)
is if false (ie. ``else``).

If you need to do more complex conditionals, you'll find that you
don't have ``elif`` available in Hy.  Instead, you should use something
called ``cond``.  In Python, you might do something like::

  somevar = 33
  if somevar > 50:
      print "That variable is too big!"
  elif somevar < 10:
      print "That variable is too small!"
  else:
      print "That variable is jussssst right!"

In Hy, you would do:

.. code-block:: clj

   (cond
    [(> somevar 50)
     (print "That variable is too big!")]
    [(< somevar 10)
     (print "That variable is too small!")]
    [true
     (print "That variable is jussssst right!")])

What you'll notice is that ``cond`` switches off between a some statement
that is executed and checked conditionally for true or falseness, and
then a bit of code to execute if it turns out to be true.  You'll also
notice that the ``else`` is implemented at the end simply by checking
for ``true`` -- that's because ``true`` will always be true, so if we get
this far, we'll always run that one!

You might notice above that if you have code like:

.. code-block:: clj

   (if some-condition
     (body-if-true)
     (body-if-false))

But wait!  What if you want to execute more than one statement in the
body of one of these?

You can do the following:

.. code-block:: clj

   (if (try-some-thing)
     (do
       (print "this is if true")
       (print "and why not, let's keep talking about how true it is!))
     (print "this one's still simply just false"))

You can see that we used ``do`` to wrap multiple statements.  If you're
familiar with other Lisps, this is the equivalent of ``progn``
elsewhere.

Comments start with semicolons:

.. code-block:: clj

  (print "this will run")
  ; (print "but this will not")
  (+ 1 2 3)  ; we'll execute the addition, but not this comment!

Looping is not hard but has a kind of special structure.  In Python,
we might do::

  for i in range(10):
      print "'i' is now at " + str(i)

The equivalent in Hy would be:

.. code-block:: clj

  (for [i (range 10)]
    (print (+ "'i' is now at " (str i))))


You can also import and make use of various Python libraries.  For
example:

.. code-block:: clj

   (import os)

   (if (os.path.isdir "/tmp/somedir")
     (os.mkdir "/tmp/somedir/anotherdir")
     (print "Hey, that path isn't there!"))

Python's context managers (``with`` statements) are used like this:

.. code-block:: clj

     (with [[f (open "/tmp/data.in")]]
       (print (.read f)))

which is equivalent to::

  with open("/tmp/data.in") as f:
      print f.read()

And yes, we do have List comprehensions!  In Python you might do::

  odds_squared = [
    pow(num, 2)
    for num in range(100)
    if num % 2 == 1]

In Hy, you could do these like:

.. code-block:: clj

  (setv odds-squared
    (list-comp
      (pow num 2)
      (num (range 100))
      (= (% num 2) 1)))


.. code-block:: clj

  ; And, an example stolen shamelessly from a Clojure page:
  ; Let's list all the blocks of a Chessboard:

  (list-comp
    (, x y)
    (x (range 8)
     y "ABCDEFGH"))

  ; [(0, 'A'), (0, 'B'), (0, 'C'), (0, 'D'), (0, 'E'), (0, 'F'), (0, 'G'), (0, 'H'),
  ;  (1, 'A'), (1, 'B'), (1, 'C'), (1, 'D'), (1, 'E'), (1, 'F'), (1, 'G'), (1, 'H'),
  ;  (2, 'A'), (2, 'B'), (2, 'C'), (2, 'D'), (2, 'E'), (2, 'F'), (2, 'G'), (2, 'H'),
  ;  (3, 'A'), (3, 'B'), (3, 'C'), (3, 'D'), (3, 'E'), (3, 'F'), (3, 'G'), (3, 'H'),
  ;  (4, 'A'), (4, 'B'), (4, 'C'), (4, 'D'), (4, 'E'), (4, 'F'), (4, 'G'), (4, 'H'),
  ;  (5, 'A'), (5, 'B'), (5, 'C'), (5, 'D'), (5, 'E'), (5, 'F'), (5, 'G'), (5, 'H'),
  ;  (6, 'A'), (6, 'B'), (6, 'C'), (6, 'D'), (6, 'E'), (6, 'F'), (6, 'G'), (6, 'H'),
  ;  (7, 'A'), (7, 'B'), (7, 'C'), (7, 'D'), (7, 'E'), (7, 'F'), (7, 'G'), (7, 'H')]


Python has support for various fancy argument and keyword arguments.
In Python we might see::

  >>> def optional_arg(pos1, pos2, keyword1=None, keyword2=42):
  ...   return [pos1, pos2, keyword1, keyword2]
  ...
  >>> optional_arg(1, 2)
  [1, 2, None, 42]
  >>> optional_arg(1, 2, 3, 4)
  [1, 2, 3, 4]
  >>> optional_arg(keyword1=1, pos2=2, pos1=3, keyword2=4)
  [3, 2, 1, 4]

The same thing in Hy::

  => (defn optional-arg [pos1 pos2 &optional keyword1 [keyword2 42]]
  ...  [pos1 pos2 keyword1 keyword2])
  => (optional-arg 1 2)
  [1 2 None 42]
  => (optional-arg 1 2 3 4)
  [1 2 3 4]

If you're running a version of Hy past 0.10.1 (eg, git master),
there's also a nice new keyword argument syntax::

  => (optional-arg :keyword1 1
  ...              :pos2 2
  ...              :pos1 3
  ...              :keyword2 4)
  [3, 2, 1, 4]

Otherwise, you can always use `apply`.  But what's `apply`?

Are you familiar with passing in `*args` and `**kwargs` in Python?::

  >>> args = [1 2]
  >>> kwargs = {"keyword2": 3
  ...           "keyword1": 4}
  >>> optional_arg(*args, **kwargs)

We can reproduce this with `apply`::

  => (setv args [1 2])
  => (setv kwargs {"keyword2" 3
  ...              "keyword1" 4})
  => (apply optional-arg args kwargs)
  [1, 2, 4, 3]

There's also a dictionary-style keyword arguments construction that
looks like:

.. code-block:: clj

  (defn another-style [&key {"key1" "val1" "key2" "val2"}]
    [key1 key2])

The difference here is that since it's a dictionary, you can't rely on
any specific ordering to the arguments.

Hy also supports ``*args`` and ``**kwargs``.  In Python::

  def some_func(foo, bar, *args, **kwargs):
    import pprint
    pprint.pprint((foo, bar, args, kwargs))

The Hy equivalent:

.. code-block:: clj

  (defn some-func [foo bar &rest args &kwargs kwargs]
    (import pprint)
    (pprint.pprint (, foo bar args kwargs)))

Finally, of course we need classes!  In Python, we might have a class
like::

  class FooBar(object):
      """
      Yet Another Example Class
      """
      def __init__(self, x):
          self.x = x

      def get_x(self):
          """
          Return our copy of x
          """
          return self.x


In Hy:

.. code-block:: clj

  (defclass FooBar [object]
    "Yet Another Example Class"
    [[--init--
      (fn [self x]
        (setv self.x x)
        ; Currently needed for --init-- because __init__ needs None
        ; Hopefully this will go away :)
        None)]

     [get-x
      (fn [self]
        "Return our copy of x"
        self.x)]])


You can also do class-level attributes.  In Python::

  class Customer(models.Model):
      name = models.CharField(max_length=255)
      address = models.TextField()
      notes = models.TextField()

In Hy:

.. code-block:: clj

  (defclass Customer [models.Model]
    [[name (models.CharField :max-length 255})]
     [address (models.TextField)]
     [notes (models.TextField)]])

Hy <-> Python interop
=====================

By importing Hy, you can use Hy directly from Python!

If you save the following in ``greetings.hy``:

.. code-block:: clj

    (defn greet [name] (print "hello from hy," name))

Then you can use it directly from python, by importing hy before importing
the module. In Python::

    import hy
    import greetings

    greetings.greet("Foo")

You can also declare a function in python (or even a class!) and use it in Hy!

If you save the following in ``greetings.py`` in Python::

    def greet(name):
        print("hello, %s" % (name))

You can use it in Hy:

.. code-block:: clj

    (import greetings)
    (.greet greetings "foo")

To use keyword arguments, you can use in ``greetings.py``::

    def greet(name, title="Sir"):
        print("Greetings, %s %s" % (title,name))

.. code-block:: clj

    (import greetings)
    (.greet greetings "Foo")
    (.greet greetings "Foo" "Darth")
    (apply (. greetings greet) ["Foo"] {"title" "Lord"})

Which would output::

  Greetings, Sir Foo

  Greetings, Darth Foo

  Greetings, Lord Foo



Protips!
========

Hy also features something known as the "threading macro", a really neat
feature of Clojure's. The "threading macro" (written as ``->``) is used
to avoid deep nesting of expressions.

The threading macro inserts each expression into the next expression's first
argument place.

Let's take the classic:

.. code-block:: clj

    (loop (print (eval (read))))

Rather than write it like that, we can write it as follows:

.. code-block:: clj

    (-> (read) (eval) (print) (loop))

Now, using `python-sh <http://amoffat.github.com/sh/>`_, we can show
how the threading macro (because of python-sh's setup) can be used like
a pipe:

.. code-block:: clj

    => (import [sh [cat grep wc]])
    => (-> (cat "/usr/share/dict/words") (grep "-E" "^hy") (wc "-l"))
    210

Which, of course, expands out to:

.. code-block:: clj

    (wc (grep (cat "/usr/share/dict/words") "-E" "^hy") "-l")

Much more readable, no? Use the threading macro!
