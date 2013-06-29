#!/usr/bin/env hy

(import sys)
(import argparse)

(setf parser (argparse.ArgumentParser))

(.add_argument parser "-i")
(.add_argument parser "-c")

(setf args (.parse_args parser))

;; using (cond) allows -i to take precedence over -c

(cond (args.i
       (print (str args.i)))
      (args.c
       (print (str "got c"))))
