(import [gevent.server [StreamServer]])


(defn handle [socket address]
  (.send socket "Hello from Lisp!\n")
  (for [x (range 5)] (.send socket (+ (str x) "\n")))
  (.close socket))


(setv server (StreamServer (, "127.0.0.1" 5000) handle))
(.serve-forever server)
