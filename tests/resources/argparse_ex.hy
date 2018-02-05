#!/usr/bin/env hy
;; Copyright 2018 the authors.
;; This file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.

(import sys)
(import argparse)

(setv parser (argparse.ArgumentParser))

(.add_argument parser "-i")
(.add_argument parser "-c")

(setv args (.parse_args parser))

;; using (cond) allows -i to take precedence over -c

(cond [args.i
       (print (str args.i))]
      [args.c
       (print (str "got c"))])
