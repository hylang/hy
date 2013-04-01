Language Spec
=============

This bit covers a bit about Hy's lovable quirks and eccentricities.

In a nutshell, Hy is a lisp dialect, but one that converts its
structure into Python (literally a conversion into Python's abstract
syntax tree!).  This is pretty cool because it means Hy is several
things:

 - A lisp that feels very pythonic
 - For lispers, a great way to use lisp's crazy powers but in the wide
   world of Python's libraries (why yes, you now can write a Django
   application in lisp!)
 - For pythonistas, a great way to start exploring lisp, from the
   comfort of python!
 - For everyone: a pleasant language that has a lot of neat ideas!


Basic intro to lisp for pythonistas
-----------------------------------

Okay, maybe you've never used lisp before, but you've used python!

A "hello world" in hy is actually super simple.  Let's try it:

.. code-block:: clj

   (print "hello world")

See?  Easy!  As you may have guessed, this is the same as the python
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
passed in.  In fact, in hy (as with most lisps) we can pass in
multiple arguments to the plus operator:

.. code-block:: clj

   (+ 1 3 55)

Which would return 59.

Maybe you've heard of lisp before but don't know much about it.  Lisp
isn't as hard as you might think, and hy inherits from python, so hy
is a great way to start learning lisp.  The main thing that's obvious
about lisp is that there's a lot of parentheses.  This might seem
confusing at first, but it isn't so hard.  Let's look at some simple
math that's wrapped in a bunch of parentheses that we could enter into
the hy interpreter:

.. code-block:: clj

   (def result (- (/ (+ 1 3 88) 2) 8))

This would return 37.  But why?  Well, we could look at the equivalent
expression in python::
  
  result = ((1 + 3 + 88) / 2) - 8

If you were to try to figure out how the above were to work in python,
you'd of course figure out the results by solving each inner
parenthesis.  That's the same basic idea in hy.  Let's try this
exercise first in python::

  result = ((1 + 3 + 88) / 2) - 8
  # simplified to...
  result = (92 / 2) - 8
  # simplified to...
  result = 46 - 8
  # simplified to...
  result = 38

Now let's try the same thing in hy:

.. code-block:: clj

   (def result (- (/ (+ 1 3 88) 2) 8))
   ; simplified to...
   (def result (- (/ 92 2) 8))
   ; simplified to...
   (def result (- 46 8))
   ; simplified to...
   (def result 38)

As you probably guessed, this last expression with "def" means to
assign the variable "result" to 38.

See?  Not too hard!

This is the basic premise of lisp... lisp stands for "list
processing"... this means that the structure of the program is
actually lists of lists.  (If you're familiar with python lists,
imagine the entire same structure as above but with square brackets
instead, any you'll be able to see the structure above as both a
program and a datastructure.)  This is easier to understand with more
examples, so let's write a simple python program and test it and then
show the equivalent hy program::

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

Now let's look at the equivalent hy program:

.. code-block:: clj

   (defn simple-conversation []
      (print "Hello!  I'd like to get to know you.  Tell me about yourself!")
      (def name (raw_input "What is your name? "))
      (def age (raw_input "What is your age? "))
      (print (+ "Hello " name "!  I see you are "
                 age " years old.")))

If you look at the above program, as long as you remember that the
first element in each list of the program is the function (or
macro... we'll get to those later) being called and that the rest are
the arguments, it's pretty easy to figure out what this all means.
(As you probably also guessed, defn is the hy method of defining
methods.)

Still, lots of people find this confusing at first because there's so
many parentheses, but there are plenty of things that can help make
this easier: keep indentation nice and use an editor with parenthesis
matching (this will help you figure out what each parenthesis pairs up
with) and things will start to feel comfortable.

There are some advantages to having a code structure that's actually a
very simple datastructure as the core of lisp is based on.  For one
thing, it means that your programs are easy to parse and that the
entire actual structure of the program is very clearly exposed to you.
(There's an extra step in hy where the structure you see is converted
to python's own representations... in more "pure" lisps such as common
lisp or emacs lisp, the data structure you see for the code and the
data structure that is executed is much more literally close.)

Another implication of this is macros: if a program's structure is a
simple data structure, that means you can write code that can write
code very easily, meaning that implementing entirely new language
features can be very fast.  Previous to hy, this wasn't very possible
for python programmers... now you too can make use of macros'
incredible power (just be careful to not aim them footward)!


Hy is python flavored lisp (or vice versa?)
-------------------------------------------

Hy converts to python's own abstract syntax tree, so you'll soon start
to find that all the familiar power of python is at your fingertips.

You have full access to python's data types and standard library in
hy.  Let's experiment with this in the hy interpreter::

  => [1 2 3]
  [1, 2, 3]
  => {"dog" "bark"
  ... "cat" "meow"}
  ...
  {'dog': 'bark', 'cat': 'meow'}

(You may notice that at present, the common lisp method of quoting
things like so:

.. code-block:: clj

   '(1 2 3)

does not work.  Instead, use angle brackets as above.)

You also have access to all the builtin types' nice methods::

  => (.strip " fooooo   ")
  "fooooo"

What's this?  Yes indeed, this is precisely the same as::

  " fooooo   ".strip()

That's right... lisp with dot notation!  If we have this string
assigned as a variable, we can also do the following:

.. code-block:: clj

   (def this-string " fooooo   ")
   (this-string.strip)

What about conditionals?:

.. code-block:: clj

   (if (try-some-thing)
     (print "this is if true")
     (print "this is if false"))

As you can tell above, the first argument to if is a truth test, the
second argument is a body if true, and the third argument (optional!)
is if false (ie, "else"!).

If you need to do more complex conditionals, you'll find that you
don't have elif available in hy.  Instead, you should use something
called "cond".  In python, you might do something like::

  somevar = 33
  if somevar > 50:
      print "That variable is too big!"
  elif somevar < 10:
      print "That variable is too small!"
  else:
      print "That variable is jussssst right!"

In hy, you would do:

.. code-block:: clj

   (cond
    ((> somevar 50)
     (print "That variable is too big!"))
    ((< somevar 10)
     (print "That variable is too small!"))
    (true
     (print "That variable is jussssst right!")))

What you'll notice is that cond switches off between a some statement
that is executed and checked conditionally for true or falseness, and
then a bit of code to execute if it turns out to be true.  You'll also
notice that the "else" is implemented at the end simply by checking
for "true"... that's because true will always be true, so if we get
this far, we'll always run that one!

You might notice above that if you have code like:

.. code-block:: clj

   (if some-condition
     (body-if-true)
     (body-if-false))

But wait!  What if you want to execute more than one statment in the
body of one of these?

You can do the following:

.. code-block:: clj

   (if (try-some-thing)
     (do
       (print "this is if true")
       (print "and why not, let's keep talking about how true it is!))
     (print "this one's still simply just false"))

You can see that we used "do" to wrap multiple statments.  If you're
familiar with other lisps, this is the equivalent of "progn"
elsewhere.

Comments start with semicolons::

  (print "this will run")
  ; (print "but this will not")
  (+ 1 2 3)  ; we'll execute the addition, but not this comment!

Looping is not hard but has a kind of special structure.  In python,
we might do::

  for i in range(10):
      print "'i' is now at " + str(i)

The equivalent in hy would be::

  (for (i (range 10))
     (print (+ "'i' is now at " (str i))))

TODO: explain the extra power of hy's for, the list comprehensions
aspect ;)

You can also import and make use of various python libraries.  For
example:

.. code-block:: clj

   (import os)
  
   (if (os.path.isdir "/tmp/somedir")
     (os.mkdir "/tmp/somedir/anotherdir")
     (print "Hey, that path isn't there!"))

Comments start with semicolons:

.. code-block:: clj

   (print "this will run")
   ; (print "but this will not")
   (+ 1 2 3)  ; we'll execute the addition, but not this comment!


TODO
----

 - How do I define classes?
 - Blow your mind with macros!
 - Where's my banana???
