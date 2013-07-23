;;;; This contains some of the core Hy functions used
;;;; to make functional programming slightly easier.
;;;;


(defn take [count what]
  "Take `count` elements from `what`, or the whole set if the total
   number of entries in `what` is less than `count`."
  (setv what (iter what))
  (for [i (range count)]
    (yield (next what))))


(defn drop [count coll]
  "Drop `count` elements from `coll` and return the iter"
  (let [ [citer (iter coll)] ]
    (for [i (range count)]
      (next citer))
    citer))

(defmacro kwapply [call kwargs] 
  (let [[fun (first call)]
        [args (rest call)]] 
    (quasiquote (apply (unquote fun) 
                       [(unquote-splice args)] 
                       (unquote kwargs)))))

(def *exports* ["take" "drop" "kwapply"])
