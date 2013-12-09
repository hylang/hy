# coding: hy

from __future__ import print_function

@(defn hello [] 
  (print "hello world !!"))

@(hello)

A = 1 + 2 + @(+ 1 1)
print(A)

@(defmacro pr [x]
   `(print ~x))

def test_macro():
    print("test macro")
    @(pr "test macro 2")

test_macro()
