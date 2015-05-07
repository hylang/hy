;;; Hy named let macro

;;; Syntax::
;;;
;;;     (n-let name [[argument init-expr] ...] body)
;;;
;;; In Scheme, ``let`` macro has a second form called ``named let``.
;;; Its syntax is ``(let proc-id ([id init-expr] ...) body ...+)``.
;;; It evaluates the ``init-exprs``; the resulting values become arguments in
;;; an application of a procedure ``(lambda (id ...) body ...+)``, where
;;; ``proc-id`` is bound within the ``body``s to the procedure itself.
;;; ``n-let`` defines a lambda with initial expressions, and bind ``name`` to the
;;; lambda. It then implicitly calls the lambda with evaluated initial expressions.
;;; The ``name`` is bounded within the `body`. For simplicity, multiple `body`s
;;; as in Scheme is not supported.

(import [hy.models.list [HyList]])

(defmacro n-let [name args body]
  `(do
    (let [[~name (fn ~(HyList (map first args)) ~body)]]
     (~name ~@(map second args)))))



