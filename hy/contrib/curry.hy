(import inspect functools sys)


(defn curry [func]
  (let [[sig (.getargspec inspect func)]
        [count (len sig.args)]]

    (fn [&rest args]
      (if (< (len args) count)
        (apply functools.partial (+ [(curry func)] (list args)))
        (apply func args)))))


(defmacro fnc [args &rest body]
  `(do (import hy.contrib.curry)
       (with-decorator hy.contrib.curry.curry (fn [~@args] ~@body))))


(defmacro defnc [name args &rest body]
  `(def ~name (fnc [~@args] ~@body)))
