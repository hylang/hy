;;; Get a frozenset of Hy reserved words
(import hy sys keyword)

(setv _cache None)

(defn names []
  "Return a frozenset of reserved symbol names.

  The result of the first call is cached."
  (global _cache)
  (if (is _cache None) (do
    (setv unmangle (. sys.modules ["hy.lex.parser"] hy_symbol_unmangle))
    (setv _cache (frozenset (map unmangle (+
      hy.core.language.*exports*
      hy.core.shadow.*exports*
      (list (.keys (get hy.macros._hy_macros None)))
      keyword.kwlist
      (list-comp k [k (.keys hy.compiler.-compile-table)]
        (isinstance k hy._compat.string-types))))))))
  _cache)
