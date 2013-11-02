(import [sys]
        [StringIO [StringIO]]
        [json]
        [hy.cmdline [HyREPL]]
        [hy]
        [flask [Flask redirect request render_template]])

(defclass MyHyREPL [HyREPL]
  [[eval (fn [self code]
           (setv old-stdout sys.stdout)
           (setv old-stderr sys.stderr)
           (setv fake-stdout (StringIO))
           (setv sys.stdout fake-stdout)
           (setv fake-stderr (StringIO))
           (setv sys.stderr fake-stderr)
           (HyREPL.runsource self code "<input>" "single")
           (setv sys.stdout old-stdout)
           (setv sys.stderr old-stderr)
           {"stdout" (fake-stdout.getvalue) "stderr" (fake-stderr.getvalue)})]])
                 
(def app (Flask __name__))

(with-decorator (kwapply (app.route "/") {"methods" ["GET"]})
  (fn []
    (kwapply (render_template "index.html") {"hy_version" hy.__version__})
    ))

(with-decorator (kwapply (app.route "/eval") {"methods" ["POST"]})
  (fn [] 
    (let [[repl (MyHyREPL)] [input (request.get_json)]]
      (foreach [expr (get input "env")]
        (repl.eval expr))
      (json.dumps (repl.eval (get input "code")))
    )))
