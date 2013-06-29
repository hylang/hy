;;; Hy tumblr printer.
;;; Copyright (c) Paul R. Tagliamonte, 2013, MIT/Expat license.


(import [urllib2 [urlopen]]
        [lxml [etree]]
        [sys [argv]])


(defn get-rss-feed-name [tumblr]
  (kwapply (.format "http://{tumblr}.tumblr.com/rss") {"tumblr" tumblr}))

(defn get-rss-feed [tumblr]
  (.parse etree (urlopen (get-rss-feed-name tumblr))))

(defn print-posts [tumblr]
  (for [post (.xpath (get-rss-feed tumblr) "//item/title")]
    (print post.text)))

(if (slice argv 2)
  (print-posts (get argv 2))
  (print-posts "this-plt-life"))
