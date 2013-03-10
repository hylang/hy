; Copyright (c) Paul R. Tagliamonte <tag@pault.ag>, 2013 under the terms of
; hy.



(import-from flask
             Flask render-template)


(def app (Flask "__main__"))  ; long story, needed hack


(route "/" [] (render-template "index.html"))
