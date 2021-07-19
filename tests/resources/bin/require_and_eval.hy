(require tests.resources.macros [test-macro])

(print (hy.eval '(do (test-macro) (cut "zabc" blah None))))
