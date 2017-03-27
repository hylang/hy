;;;; Hy shadow functions

(import operator)


(defn + [&rest args]
  "Shadow + operator for when we need to import / map it against something"
  (if
    (= (len args) 1)
      (operator.pos (get args 0))
    args
      (reduce operator.add args)
    (raise (TypeError "Need at least 1 argument to add/concatenate"))))


(defn - [&rest args]
  "Shadow - operator for when we need to import / map it against something"
  (if
    (= (len args) 1)
      (- (get args 0))
    args
      (reduce operator.sub args)
    (raise (TypeError "Need at least 1 argument to subtract"))))


(defn * [&rest args]
  "Shadow * operator for when we need to import / map it against something"
  (if (= (len args) 0)
    1  ; identity
    (reduce operator.mul args)))


(defn / [&rest args]
  "Shadow / operator for when we need to import / map it against something"
  (if
    (= (len args) 1)
      (operator.truediv 1 (get args 0))
    args
      (reduce operator.truediv args)
    (raise (TypeError "Need at least 1 argument to divide"))))


(defn comp-op [op args]
  "Helper for shadow comparison operators"
  (if (< (len args) 2)
    (raise (TypeError "Need at least 2 arguments to compare"))
    (reduce (fn [x y] (and x y))
            (list-comp (op x y)
                       [(, x y) (zip args (cut args 1))]))))
(defn < [&rest args]
  "Shadow < operator for when we need to import / map it against something"
  (comp-op operator.lt args))
(defn <= [&rest args]
  "Shadow <= operator for when we need to import / map it against something"
  (comp-op operator.le args))
(defn = [&rest args]
  "Shadow = operator for when we need to import / map it against something"
  (comp-op operator.eq args))
(defn != [&rest args]
  "Shadow != operator for when we need to import / map it against something"
  (comp-op operator.ne args))
(defn >= [&rest args]
  "Shadow >= operator for when we need to import / map it against something"
  (comp-op operator.ge args))
(defn > [&rest args]
  "Shadow > operator for when we need to import / map it against something"
  (comp-op operator.gt args))

; TODO figure out a way to shadow "is", "is_not", "and", "or"


(setv *exports* ['+ '- '* '/ '< '<= '= '!= '>= '>])
