;;; Meth
;; based on paultag's meth library to access a Flask based application

(defmacro route-with-methods [name path methods params &rest code]
  "Same as route but with an extra methods array to specify HTTP methods"
  `(let [[deco (kwapply (.route app ~path)
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


;;; Simple example application
;;; Requires to have Flask installed

;; (import [flask [Flask]])
;; (setv app (Flask "__main__"))

;; (require hy.contrib.meth)

;; (print "setup / with GET")
;; (route get-index "/" []  (str "Hy world!"))

;; (print "setup /post with POST")
;; (post-route post-index "/post" []  (str "Hy post world!"))

;; (route-with-methods both-index "/both" [] 
;;   (str "Hy to both worlds!") ["GET" "POST"])

;; (.run app)

;;; Now you can do:
;;; curl 127.0.0.1:5000
;;; curl -X POST 127.0.0.1:5000/post
;;; curl -X POST 127.0.0.1:5000/both
;;; curl 127.0.0.1:5000/both
