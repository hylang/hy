; Copyright (c) Paul R. Tagliamonte <tag@pault.ag>, 2013 under the terms of
; hy.

(import-from flask
             Flask render-template request)

(import-from pygments highlight)
(import-from pygments.formatters HtmlFormatter)
(import-from pygments.lexers PythonLexer
                             ClojureLexer)

(import-from pygments-extension PygmentsExtension)
(import-from hy.importer import_string_to_ast)
(import codegen)


(def app (Flask "__main__"))  ; long story, needed hack
(.add_extension app.jinja_env PygmentsExtension)


; pygments bits.
(def lexers {"python" (PythonLexer)
             "lisp"   (ClojureLexer)})


(defn colorize-python [x]
  (highlight x (get lexers "python") (HtmlFormatter)))


(defn hy-to-py [hython]
  (.to_source codegen
    (import-string-to-ast hython)))


; view routes
(route "/" [] (render-template "index.html"))


(post-route "/format/<language>" [language]
  (highlight
    (get request.form "code")
    (get lexers language)
    (HtmlFormatter)))


(post-route "/hy2py" [] (hy-to-py (get request.form "code")))


(post-route "/hy2pycol" []
  (colorize-python (hy-to-py (get request.form "code"))))
