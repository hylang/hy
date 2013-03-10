;

(import-from flask
             Flask render-template request)


(def app (Flask "__main__"))  ; long story, needed hack


(route "/" [] (render-template "index.html"))
