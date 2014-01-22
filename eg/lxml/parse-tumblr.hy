;;; Hy tumblr printer.
;;; Copyright (c) Paul R. Tagliamonte, 2013, MIT/Expat license.


(import [lxml [etree]]
        [sys [argv]])

(try
  (import [urllib.request [urlopen]])
  (catch [ImportError]
    (import [urllib2 [urlopen]])))

(defn get-rss-feed-name [tumblr]
  (.format "http://{0}.tumblr.com/rss" tumblr))

(defn get-rss-feed [tumblr]
  (.parse etree (urlopen (get-rss-feed-name tumblr))))

(defn print-posts [tumblr]
  (for [post (.xpath (get-rss-feed tumblr) "//item/title")]
    (print post.text)))

(if (slice argv 2)
  (print-posts (get argv 2))
  (print-posts "this-plt-life"))
