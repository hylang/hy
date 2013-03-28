; Copyright (c) Paul R. Tagliamonte <tag@pault.ag>, 2013 under the terms of
; hy.

(import-from flask
             Flask render-template request make-response)

(import-from hy.errors HyError)
(import-from hy.lex LexException)
(import-from hy.importer import-string-to-ast)

(import astor.codegen)
(import autopep8)


(def app (Flask "__main__"))  ; long story, needed hack


(defn hy-to-py [hython]
  (.fix-string autopep8
               (.to_source astor.codegen (import-string-to-ast hython))))

(defn err [msg] (make-response msg 500))


; view routes
(route index "/" [] (render-template "repl.html"))

(post-route hy2py "/hy2py" []
  (try
    (hy-to-py (get request.form "code"))
  (catch LexException e (err "Incomplete Code."))
  (catch HyError e (err "Generic error during processing."))
  (catch Exception e (err "Erm, you broke something."))))
