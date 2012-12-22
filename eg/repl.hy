; vim: tabstop=2 expandtab shiftwidth=2 softtabstop=2 filetype=lisp
; Copyright (c) Paul Tagliamonte, in sofar as any of this is at all
;  copyrightable.

(loop (print (eval (read))))
; Yes folks, this is where REPL comes from.
