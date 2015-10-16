;; adapted from the example in PEP 492
;; https://www.python.org/dev/peps/pep-0492/#working-example

(import asyncio)

(defasync replhy-server []
  (print "Replhy Server listening on localhost:8000!")
  (await (asyncio.start-server handle-connection "localhost" 8000)))

(defasync handle-connection [reader writer]
  (print "New connection ...")

  (while true
    ;; XXX TODO: make it possible for this to be `(let [[data (await
    ;; (.read reader 8192))]]` ... and so on. At time of writing,
    ;; that's a `SyntaxError: 'await' outside async function`
    ;; (presumably because the Hy `let` binding gets compiled to an
    ;; ordinary non-async Python function).
    (setv data (await (.read reader 8192)))
    (if-not data
       (break))
    (print (.format "Sending {:.10}... back!" (repr data)))
    (.write writer data)))

(defmain [&rest args]
  (let [[loop (asyncio.get-event-loop)]]
    (.run-until-complete loop (replhy-server))
    (try (.run-forever loop)
         (finally (.close loop)))))
