"Helpers for testing type parameters."

(import typing [TypeVar TypeVarTuple ParamSpec TypeAliasType])

(defn show [f]
  (lfor
    tp f.__type_params__
    [(type tp) tp.__name__
      (getattr tp "__bound__" None)
      (getattr tp "__constraints__" #())]))
