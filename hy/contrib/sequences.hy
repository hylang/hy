;; Copyright 2021 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

(defclass Sequence []

  (defn --init-- [self func]
    "initialize a new sequence with a function to compute values"
    (setv (. self func) func)
    (setv (. self cache) [])
    (setv (. self high-water) -1))

  (defn --getitem-- [self n]
    "get nth item of sequence"
    (if (hasattr n "start")
    (gfor x (range n.start n.stop (or n.step 1))
         (get self x))
    (do (when (neg? n)
         ; Call (len) to force the whole
         ; sequence to be evaluated.
         (len self))
       (if (<= n (. self high-water))
         (get (. self cache) n)
         (do (while (< (. self high-water) n)
               (setv (. self high-water) (inc (. self high-water)))
               (.append (. self cache) (.func self (. self high-water))))
             (get self n))))))

   (defn --iter-- [self]
     "create iterator for this sequence"
     (setv index 0)
     (try (while True
            (yield (get self index))
            (setv index (inc index)))
          (except [IndexError]
            (return))))

   (defn --len-- [self]
     "length of the sequence, dangerous for infinite sequences"
     (setv index (. self high-water))
     (try (while True
            (get self index)
            (setv index (inc index)))
          (except [IndexError]
            (len (. self cache)))))

   (setv max-items-in-repr 10)

   (defn --str-- [self]
     "string representation of this sequence"
     (setv items (list (take (inc self.max-items-in-repr) self)))
     (.format (if (> (len items) self.max-items-in-repr)
                "[{0}, ...]"
                "[{0}]")
              (.join ", " (map str items))))

   (defn --repr-- [self]
     "string representation of this sequence"
     (.--str-- self)))

(defmacro seq [param &rest seq-code]
  `(Sequence (fn ~param (do ~@seq-code))))

(defmacro defseq [seq-name param &rest seq-code]
  `(setv ~seq-name (Sequence (fn ~param (do ~@seq-code)))))

(defn end-sequence []
  "raise IndexError exception to signal end of sequence"
  (raise (IndexError "list index out of range")))
