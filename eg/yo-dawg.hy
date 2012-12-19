; vim: tabstop=2 expandtab shiftwidth=2 softtabstop=2 filetype=lisp
; Copyright (c) Paul Tagliamonte, in sofar as any of this is at all
;  copyrightable.

(import ["json"])

(print "I'll eval s-expressions you input")
(loop (print
  (kwapply (json.dumps
    (lex (read))) {"sort_keys" true "indent" 4})))
