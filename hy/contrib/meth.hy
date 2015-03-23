;;; Hy on Meth
;;; based on paultag's meth library to access a Flask based application

(defmacro/g! route-with-methods-decorated [name decorators path methods params &rest code]
  "Same as route but with an extra methods array to specify HTTP methods"
  `(let [[~g!decorator (apply app.route [~path] {"methods" ~methods})]]
     (with-decorator ~g!decorator ~@decorators
       (defn ~name ~params
         (progn ~@code)))))

;; Some route-with-methods-decorated macro examples
(defmacro-alias [get-route-decorated route-decorated] [name decorators path params &rest code]
  "Get request"
  `(route-with-methods-decorated ~name ~decorators ~path ["GET"] ~params ~@code))

(defmacro post-route-decorated [name decorators path params &rest code]
  "Post request"
  `(route-with-methods-decorated ~name ~decorators ~path ["POST"] ~params ~@code))

(defmacro put-route-decorated [name decorators path params &rest code]
  "Put request"
  `(route-with-methods-decorated ~name ~decorators ~path ["PUT"] ~params ~@code))

(defmacro delete-route-decorated [name decorators path params &rest code]
  "Delete request"
  `(route-with-methods-decorated ~name ~decorators ~path ["DELETE"] ~params ~@code))

(defmacro/g! route-with-methods [name path methods params &rest code]
  "Same as route but with an extra methods array to specify HTTP methods"
  `(route-with-methods-decorated ~name [] ~path ~methods ~params ~@code))

;; Some route-with-methods macro examples
(defmacro-alias [get-route route] [name path params &rest code]
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

