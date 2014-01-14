;;; Simple Flask application
;;;
;;; Requires to have Flask installed
;;;
;;; You can test it via:
;;;
;;;   $ curl 127.0.0.1:5151
;;;   $ curl -X POST 127.0.0.1:5151/post
;;;   $ curl -X POST 127.0.0.1:5151/both
;;;   $ curl 127.0.0.1:5151/both

(import [flask [Flask]])

(require hy.contrib.meth)

(setv app (Flask "__main__"))

(route get-index "/" []
  (str "Hy world!"))

(post-route post-index "/post" []
  (str "Hy post world!"))

(route-with-methods both-index "/both" ["GET" "POST"] []
  (str "Hy to both worlds!"))

(apply app.run [] {"port" 5151})
