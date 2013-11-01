(require hy.contrib.meth)
(import [hy.cmdline [HyREPL]]
        [sys]
        [StringIO [StringIO]]
        [flask [Flask redirect request]]
        [json])

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
                 

(def repl (MyHyREPL))

(def app (Flask __name__))
(route hello "/<name>" [name] (.format "(hello \"{0}!\")" name))
(route eval-get "/eval" [] (json.dumps (repl.eval (get request.args "code"))))
