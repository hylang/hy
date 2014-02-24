;; You need to install the requests package first

(import os.path)
(import requests)


(setv *api-url* "https://api.github.com/{}")
(setv *rst-format* "* `{} <{}>`_")
(setv *missing-names* {"khinsen" "Konrad Hinsen"})
;; We have three concealed members on the hylang organization
;; and GitHub only shows public members if the requester is not
;; an owner of the organization.
(setv *concealed-members* [(, "aldeka" "Karen Rustad")
                           (, "tuturto" "Tuukka Turto")
                           (, "cndreisbach" "Clinton N. Dreisbach")])

(defn get-dev-name [login]
  (setv name (get (.json (requests.get (.format *api-url* (+ "users/" login)))) "name"))
  (if-not name
    (.get *missing-names* login)
    name))

(setv coredevs (requests.get (.format *api-url* "orgs/hylang/members")))

(setv result (set))
(for [dev (.json coredevs)]
  (result.add (.format *rst-format* (get-dev-name (get dev "login"))
                       (get dev "html_url"))))

(for [(, login name) *concealed-members*]
  (result.add (.format *rst-format* name (+ "https://github.com/" login))))

(setv filename (os.path.abspath (os.path.join os.path.pardir
                                              "docs" "coreteam.rst")))

(with [[fobj (open filename "w+")]]
  (fobj.write (+ (.join "\n" result) "\n")))
