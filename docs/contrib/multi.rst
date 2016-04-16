========
defmulti
========

.. versionadded:: 0.10.0

``defmulti``, ``defmethod`` and ``default-method`` lets you define
multimethods where a dispatching function is used to select between different
implementations of the function. Inspired by Clojure's multimethod and based
on the code by `Adam Bard`_.

.. code-block:: clj

    => (require hy.contrib.multi)
    => (defmulti area [shape]
    ...  "calculate area of a shape"
    ...  (:type shape))
  
    => (defmethod area "square" [square]
    ...  (* (:width square)
    ...     (:height square)))
  
    => (defmethod area "circle" [circle]
    ...  (* (** (:radius circle) 2) 
    ...     3.14))

    => (default-method area [shape]
    ...  0)

    => (area {:type "circle" :radius 0.5})
    0.785

    => (area {:type "square" :width 2 :height 2})
    4

    => (area {:type "non-euclid rhomboid"})
    0

``defmulti`` is used to define the initial multimethod with name, signature
and code that selects between different implementations. In the example,
multimethod expects a single input that is type of dictionary and contains
at least key :type. The value that corresponds to this key is returned and
is used to selected between different implementations.

``defmethod`` defines a possible implementation for multimethod. It works
otherwise in the same way as ``defn``, but has an extra parameters 
for specifying multimethod and which calls are routed to this specific
implementation. In the example, shapes with "square" as :type are routed to
first function and shapes with "circle" as :type are routed to second
function.

``default-method`` specifies default implementation for multimethod that is
called when no other implementation matches.

Interfaces of multimethod and different implementation don't have to be
exactly identical, as long as they're compatible enough. In practice this
means that multimethod should accept the broadest range of parameters and
different implementations can narrow them down.

.. code-block:: clj

    => (require hy.contrib.multi)
    => (defmulti fun [&rest args]
    ...  (len args))

    => (defmethod fun 1 [a]
    ...  a)

    => (defmethod fun 2 [a b]
    ...  (+ a b))

    => (fun 1)
    1

    => (fun 1 2)
    3

.. _Adam Bard: https://adambard.com/blog/implementing-multimethods-in-python/
