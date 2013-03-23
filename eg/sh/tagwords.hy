;; python-sh from hy

(import-from sh cat grep)
(print "Words that end with `tag`:")
(print (-> (cat "/usr/share/dict/words") (grep "-E" "tag$")))
