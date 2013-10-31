(require hy.contrib.meth)
(import [hy.cmdline [HyREPL]]
        [sys]
        [StringIO [StringIO]]
        [flask [Flask redirect request]])

(defclass MyHyREPL [HyREPL]
  [[eval (fn [self code]
           (setv old-stdout sys.stdout)
           (setv fake-stdout (StringIO))
           (setv sys.stdout fake-stdout)
           (HyREPL.runsource self code "<input>" "single")
           (setv sys.stdout old-stdout)
           (fake-stdout.getvalue))]])
                 

(def repl (MyHyREPL))

(def app (Flask __name__))
(route hello "/<name>" [name] (.format "(hello \"{0}!\")" name))
(route eval-get "/eval" [] (repl.eval (get request.args "code")))
