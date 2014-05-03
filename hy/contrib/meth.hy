;;; Hy on Meth
;;; based on paultag's meth library to access a Flask based application

(defmacro route-with-methods [name path methods params &rest code]
  "Same as route but with an extra methods array to specify HTTP methods"
  `(let [[deco (apply app.route [~path]
                                    {"methods" ~methods})]]
                 (with-decorator deco
                   (defn ~name ~params 
                     (progn ~@code)))))

;; Some macro examples
(defmacro route [name path params &rest code]
  "Get request"
  `(route-with-methods ~name ~path ["GET"] ~params ~@code))

(defmacro post-route [name path params &rest code]
  "Post request"
  `(route-with-methods ~name ~path ["POST"] ~params ~@code))

(defmacro put-route [name path params &rest code]
  "Put request"
  `(route-with-methods ~name ~path ["PUT"] ~params ~@code))

(defmacro delete-route [name path params &rest code]
  "Delete request"
  `(route-with-methods ~name ~path ["DELETE"] ~params ~@code))
