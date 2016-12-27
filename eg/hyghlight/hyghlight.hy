#!/usr/bin/env hy

(import os.path)

(import hy.compiler)
(import hy.core)


;; absolute path for Hy core
(setv *core-path* (os.path.dirname hy.core.--file--))


(defn collect-macros [collected-names opened-file]
  (while True
    (try
     (let [data (read opened-file)]
       (if (and (in (first data)
                    '(defmacro defmacro/g! defn))
                (not (.startswith (second data) "_")))
         (.add collected-names (second data))))
     (except [e EOFError] (break)))))


(defmacro core-file [filename]
  `(open (os.path.join *core-path* ~filename)))


(defmacro contrib-file [filename]
  `(open (os.path.join *core-path* ".." "contrib" ~filename)))


(defn collect-core-names []
  (doto (set)
        (.update hy.core.language.*exports*)
        (.update hy.core.shadow.*exports*)
        (collect-macros (core-file "macros.hy"))
        (collect-macros (core-file "bootstrap.hy"))))


(defn collect-contrib-names []
  (doto (set)
        (collect-macros (contrib-file "alias.hy"))
        (collect-macros (contrib-file "anaphoric.hy"))
        (collect-macros (contrib-file "curry.hy"))
        (collect-macros (contrib-file "flow.hy"))
        (collect-macros (contrib-file "loop.hy"))
        (collect-macros (contrib-file "meth.hy"))
        (collect-macros (contrib-file "multi.hy"))
        (collect-macros (contrib-file "profile.hy"))
        (collect-macros (contrib-file "sequences.hy"))
        (collect-macros (contrib-file "walk.hy"))))


(defn collect-compiler-names []
  (set-comp (str name)
            [name (hy.compiler.-compile-table.keys)]
            (not (in "<class" (str name)))))


(defn collect-python-builtins []
  (set-comp function.--name--
            [function (.values --builtins--)]
            (in "built-in function" (repr function))))


(defn to-lisp-names [collected-names]
  (let [to-add (set) to-discard (set)]
    (for [name collected-names]
      (let [lisp-name (.replace (str name) "_" "-")]
        (if (in "-bang" lisp-name)
          (do (.add to-discard name)
              (.add to-discard lisp-name)
              (.add to-add (.replace lisp-name "-bang" "!"))))

        (if (in "is-" lisp-name)
          (.add to-add (.join "" (-> (drop 3 lisp-name)
                                     (list)
                                     (+ ["?"])))))

        (if (in "-" lisp-name)
          (do
           (.add to-add lisp-name)
           (.add to-discard name)))))

    (-> (doto collected-names (.update to-add))
        (.difference to-discard))))


(defn hyghlight-names []
  (-> (.union (collect-core-names)
              (collect-contrib-names)
              (collect-compiler-names)
              (collect-python-builtins))
      (to-lisp-names)
      (sorted)))


(defn generate-highlight-js-file []
  (defn replace-highlight-js-keywords [line]
    (if (in "// keywords" line)
      (+ line
         (.join " +\n"
                (list-comp (.format "{space}'{line} '"
                                    :space (* " " 6)
                                    :line (.join " " keyword-line))
                           [keyword-line (partition (hyghlight-names) 10)])))
      line))

  (with [f (open "templates/hy.js")]
        (.join ""
               (list-comp (replace-highlight-js-keywords line)
                          [line (.readlines f)]))))


(defmain [&rest args]
  (print (generate-highlight-js-file)))
