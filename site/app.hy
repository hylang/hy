; Copyright (c) Paul R. Tagliamonte <tag@pault.ag>, 2013 under the terms of
; hy.

(import-from flask
             Flask render-template request make-response)

(import-from pygments-extension PygmentsExtension)

(import-from hy.errors HyError)
(import-from hy.lex LexException)
(import-from hy.importer import_string_to_ast)

(import autopep8)
(import astor.codegen)


(def app (Flask "__main__"))  ; long story, needed hack
(.add_extension app.jinja_env PygmentsExtension)


(defn hy-to-py [hython]
  (.fix-string autopep8
               (.to_source astor.codegen (import-string-to-ast hython))))

(defn err [msg] (make-response msg 500))


; view routes
(route "/" [] (render-template "repl.html"))

(post-route "/hy2py" []
  (try (hy-to-py (get request.form "code"))
    (catch LexException (err "Incomplete Code."))
    (catch HyError (err "Generic error during processing."))
    (catch Exception (err "Erm, you broke something."))))
