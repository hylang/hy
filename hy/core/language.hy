;;;; This contains some of the core Hy functions used
;;;; to make functional programming slightly easier.
;;;;


(defn cycle [coll]
  "Yield an infinite repetition of the items in coll"
  (while true
    (for [x coll]
      (yield x))))

(defn dec [n]
  "Decrement n by 1"
  (- n 1))

(defn distinct [coll]
  "Return a generator from the original collection with duplicates
   removed"
  (let [ [seen [] ] 
         [citer (iter coll)] 
         [val (next citer)] ]
    (while (not (none? val))
      (do
       (if (not_in val seen)
         (do 
          (yield val)
          (.append seen val)))
       (setv val (next citer))))))

(defn drop [count coll]
  "Drop `count` elements from `coll` and yield back the rest"
  (let [ [citer (iter coll)] ]
    (try (for [i (range count)]
           (next citer))
         (catch [StopIteration]))
    citer))

(defn even? [n]
  "Return true if n is an even number"
  (= (% n 2) 0))

(defn filter [pred coll]
  "Return all elements from coll that pass filter"
  (let [ [citer (iter coll)] [val (next citer)] ]
    (while (not (none? val))
      (if (pred val)
        (yield val))
      (setv val (next citer)))))

(defn inc [n]
  "Increment n by 1"
  (+ n 1))

(defn instance? [klass x]
  (isinstance x klass))

(defn iterable? [x]
  "Return true if x is iterable"
  (try (do (iter x) true)
       (catch [Exception] false)))

(defn iterate [f x]
  (setv val x)
  (while true
    (yield val)
    (setv val (f val))))

(defn iterator? [x]
  "Return true if x is an iterator"
  (try (= x (iter x))
       (catch [TypeError] false)))

(defn neg? [n]
  "Return true if n is < 0"
  (< n 0))

(defn none? [x]
  "Return true if x is None"
  (is x None))

(defn nth [coll index]
  "Return nth item in collection or sequence, counting from 0"
  (if (not (neg? index))
    (if (iterable? coll)
      (try (first (list (take 1 (drop index coll))))
           (catch [IndexError] None))
      (try (get coll index)
           (catch [IndexError] None)))
    None))

(defn odd? [n]
  "Return true if n is an odd number"
  (= (% n 2) 1))

(defn pos? [n]
  "Return true if n is > 0"
  (> n 0))

(defn remove [pred coll]
  "Return coll with elements removed that pass `pred`"
  (let [ [citer (iter coll)] [val (next citer)] ]
    (while (not (none? val))
      (if (not (pred val))
        (yield val))
      (setv val (next citer)))))

(defn repeat [x &optional n]
  "Yield x forever or optionally n times"
  (if (none? n)
    (setv dispatch (fn [] (while true (yield x))))
    (setv dispatch (fn [] (for [_ (range n)] (yield x)))))
  (dispatch))

(defn repeatedly [func]
  "Yield result of running func repeatedly"
  (while true
    (yield (func))))

(defn take [count what]
  "Take `count` elements from `what`, or the whole set if the total
    number of entries in `what` is less than `count`."
  (setv what (iter what))
  (for [i (range count)]
    (yield (next what))))

(defn take-nth [n coll]
  "Return every nth member of coll
     raises ValueError for (not (pos? n))"
  (if (pos? n)
    (let [ [citer (iter coll)] [val (next citer)] ]
      (while (not (none? val))
        (yield val)
        (for [_ (range (dec n))]
          (next citer))
        (setv val (next citer))))
    (raise (ValueError "n must be positive"))))

(defn take-while [pred coll]
  "Take all elements while `pred` is true"
  (let [ [citer (iter coll)] [val (next citer)] ]
    (while (pred val)
      (yield val)
      (setv val (next citer)))))

(def *exports* ["cycle" "dec" "distinct" "drop" "even?" "filter" "inc" 
                "instance?" "iterable?" "iterate" "iterator?" "neg?" 
                "none?" "nth" "odd?" "pos?" "remove" "repeat" "repeatedly"
                "take" "take_nth" "take_while"])
