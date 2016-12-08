;; Copyright (c) 2016 Tuukka Turto <tuukka.turto@oktaeder.net>
;;
;; Permission is hereby granted, free of charge, to any person obtaining a
;; copy of this software and associated documentation files (the "Software"),
;; to deal in the Software without restriction, including without limitation
;; the rights to use, copy, modify, merge, publish, distribute, sublicense,
;; and/or sell copies of the Software, and to permit persons to whom the
;; Software is furnished to do so, subject to the following conditions:
;;
;; The above copyright notice and this permission notice shall be included in
;; all copies or substantial portions of the Software.
;;
;; THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
;; IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
;; FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
;; THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
;; LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
;; FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
;; DEALINGS IN THE SOFTWARE.
;;

(defclass Sequence []
  [--init-- (fn [self func]
              "initialize a new sequence with a function to compute values"
              (setv (. self func) func)
              (setv (. self cache) [])
              (setv (. self high-water) -1))
   --getitem-- (fn [self n]
                 "get nth item of sequence"
                 (if (hasattr n "start")
                   (genexpr (get self x) [x (range n.start n.stop
                                                   (or n.step 1))])
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
   --iter-- (fn [self]
              "create iterator for this sequence"
              (setv index 0)
              (try (while True
                     (yield (get self index))
                     (setv index (inc index)))
                   (except [_ IndexError]
                     (raise StopIteration))))
   --len-- (fn [self]
             "length of the sequence, dangerous for infinite sequences"
             (setv index (. self high-water))
             (try (while True
                    (get self index)
                    (setv index (inc index)))
                  (except [_ IndexError]
                    (len (. self cache)))))
   max-items-in-repr 10
   --str-- (fn [self]
             "string representation of this sequence"
             (setv items (list (take (inc self.max-items-in-repr) self)))
             (.format (if (> (len items) self.max-items-in-repr)
                        "[{0}, ...]"
                        "[{0}]")
                      (.join ", " (map str items))))
   --repr-- (fn [self]
              "string representation of this sequence"
              (.--str-- self))])

(defmacro seq [param &rest seq-code]
  `(Sequence (fn ~param (do ~@seq-code))))

(defmacro defseq [seq-name param &rest seq-code]
  `(def ~seq-name (Sequence (fn ~param (do ~@seq-code)))))

(defn end-sequence []
  "raise IndexError exception to signal end of sequence"
  (raise (IndexError "list index out of range")))
