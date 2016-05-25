(import [hy [importer]])
(import hy.importer)
(import [hy.importer [import_buffer_to_ast]])
(import os os.path pkgutil inspect)

(defn test_finder []
  (let [path (os.path.join (-> (inspect.currentframe)
                               (inspect.getfile)
                               (os.path.abspath)
                               (os.path.dirname))
                           "test_module")
        modules (list (map (fn [pkg] (get pkg 1)) (pkgutil.iter_modules [path])))]
    (assert (in "hytest" modules))
    (assert (in "pytest" modules))))

