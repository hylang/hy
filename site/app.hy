; Copyright (c) Paul R. Tagliamonte <tag@pault.ag>, 2013 under the terms of
; hy.



(import-from flask
             Flask render-template)

(import-from pygments highlight)
(import-from pygments.lexers PythonLexer ClojureLexer)
(import-from pygments.formatters HtmlFormatter)
(import codegen)


(def lexers {"python" (PythonLexer)
             "lisp"   (ClojureLexer)})


(def app (Flask "__main__"))  ; long story, needed hack


(route "/" [] (render-template "index.html"))


(defn colorize-python [x]
  (highlight x (index lexers "python") (HtmlFormatter)))


(defn hy-to-py [hython]
  (.to_source codegen (forge-ast "stdin" (tokenize hython))))


(decorate-with (kwapply (.route app "/format/<language>") {"methods" ["POST"]})
  (defn format-code [language]
    "Language HTML Formatter"
    (highlight
      (index request.form "code") (index lexers language) (HtmlFormatter))))


(decorate-with (kwapply (.route app "/hy2py") {"methods" ["POST"]})
  (defn translate-code []
    "Pythonic converter"
    (hy-to-py (index request.form "code"))))


(decorate-with (kwapply (.route app "/hy2pycol") {"methods" ["POST"]})
  (defn translate-code-with-color []
    "Pythonic converter"
    (colorize-python (hy-to-py (index request.form "code")))))
