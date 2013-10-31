(require hy.contrib.meth)
(import [flask [Flask redirect]])

(def app (Flask __name__))

(route hello "/<name>" [name] (.format "(hello \"{0}!\")" name))
(route root "/" [] (redirect "/hyne"))
