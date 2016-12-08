;;; Hy on Meth
;;; based on paultag's meth library to access a Flask based application

(defmacro route-with-methods [name path methods params &rest code]
  "Same as route but with an extra methods array to specify HTTP methods"
  `(let [deco (apply app.route [~path]
                     {"methods" ~methods})]
     (with-decorator deco
       (defn ~name ~params
         (do ~@code)))))

(defn rwm [name path method params code]
  `(do (require hy.contrib.meth)
       (hy.contrib.meth.route-with-methods ~name ~path ~method ~params ~@code)))

;; Some macro examples
(defmacro route [name path params &rest code]
  "Get request"
  (rwm name path ["GET"] params code))

(defmacro post-route [name path params &rest code]
  "Post request"
  (rwm name path ["POST"] params code))

(defmacro put-route [name path params &rest code]
  "Put request"
  (rwm name path ["PUT"] params code))

(defmacro delete-route [name path params &rest code]
  "Delete request"
  (rwm name path ["DELETE"] params code))
