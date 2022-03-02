;;; Get a frozenset of Hy reserved words

(import sys keyword)

(setv _cache None)

(defn macros []
  "Return a frozenset of Hy's core macro names."
  (frozenset (map hy.unmangle (+
    (list (.keys hy.core.result_macros.__macros__))
    (list (.keys hy.core.macros.__macros__))))))

(defn names []
  "Return a frozenset of reserved symbol names.

  The result of the first call is cached.

  The output includes all of Hy's core functions and macros, plus all
  Python reserved words. All names are in unmangled form (e.g.,
  ``not-in`` rather than ``not_in``).

  Examples:
    ::

       => (import hy.extra.reserved)
       => (in \"defclass\" (hy.extra.reserved.names))
       True
  "
  (global _cache)
  (when (is _cache None)
    (setv _cache (| (macros) (frozenset (map hy.unmangle
                                             keyword.kwlist)))))
  _cache)
