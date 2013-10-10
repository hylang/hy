;;; Meth
;; based on paultag's meth library to access a Flask based application

(defmacro route [name path params code]
  "Default get request"
  `(let [[deco (.route app ~path)]]
                 (with-decorator deco
                   (defn ~name ~params ~@code))))

(defmacro route-with-methods [name path params code methods]
  "Same as route but with an extra methods array to specify HTTP methods"
  `(let [[deco (kwapply (.route app ~path)
                                    {"methods" ~methods})]]
                 (with-decorator deco
                   (defn ~name ~params ~@code))))

;; Some macro examples
(defmacro post-route [name path params code]
  "Post request"
  `(route-with-methods ~name ~path ~params ~code ["POST"]))

(defmacro put-route [name path params code]
  "Put request"
  `(route-with-methods ~name ~path ~params ~code ["PUT"]))

(defmacro delete-route [name path params code]
  "Delete request"
  `(route-with-methods ~name ~path ~params ~code ["DELETE"]))


;;; Simple example application
;;; Requires to have Flask installed

;; (import [flask [Flask]])
;; (setv app (Flask "__main__"))

;; (require methy)

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
