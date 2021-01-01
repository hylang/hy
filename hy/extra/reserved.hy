;;; Get a frozenset of Hy reserved words
;; Copyright 2021 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

(import hy sys keyword)

(setv _cache None)

(defn names []
  "Return a frozenset of reserved symbol names.

  The result of the first call is cached."
  (global _cache)
  (if (is _cache None) (do
    (setv _cache (frozenset (map unmangle (+
      hy.core.language.EXPORTS
      hy.core.shadow.EXPORTS
      (list (.keys hy.core.macros.__macros__))
      keyword.kwlist
      (list (.keys hy.compiler._special_form_compilers))
      (list hy.compiler._bad_roots)))))))
  _cache)
