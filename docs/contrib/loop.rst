==========
loop/recur
==========

.. versionadded:: 0.10.0

The ``loop`` / ``recur`` macro gives programmers a simple way to use
tail-call optimization (TCO) in their Hy code.

    A tail call is a subroutine call that happens inside another
    procedure as its final action; it may produce a return value which
    is then immediately returned by the calling procedure. If any call
    that a subroutine performs, such that it might eventually lead to
    this same subroutine being called again down the call chain, is in
    tail position, such a subroutine is said to be tail-recursive,
    which is a special case of recursion. Tail calls are significant
    because they can be implemented without adding a new stack frame
    to the call stack. Most of the frame of the current procedure is
    not needed any more, and it can be replaced by the frame of the
    tail call. The program can then jump to the called
    subroutine. Producing such code instead of a standard call
    sequence is called tail call elimination, or tail call
    optimization. Tail call elimination allows procedure calls in tail
    position to be implemented as efficiently as goto statements, thus
    allowing efficient structured programming.

    -- Wikipedia (http://en.wikipedia.org/wiki/Tail_call)

Macros
======

.. _loop:

loop
-----

``loop`` establishes a recursion point. With ``loop``, ``recur``
rebinds the variables set in the recursion point and sends code
execution back to that recursion point. If ``recur`` is used in a
non-tail position, an exception is thrown.

Usage: `(loop bindings &rest body)`

Example:

.. code-block:: hy

    (require hy.contrib.loop)

    (defn factorial [n]
      (loop [[i n] [acc 1]]
        (if (zero? i)
          acc
          (recur (dec i) (* acc i)))))

    (factorial 1000)
