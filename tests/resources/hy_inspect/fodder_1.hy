; first line of the file
"A module docstring."

(import inspect)

(defn spam [a #* g b c [d 3] [e 4] [f 5] #** h]
  (eggs (+ b d) (+ c f)))

(defn eggs [x y]
  "A docstring."
  (global fr st)
  (setv fr (inspect.currentframe))
  (setv st (inspect.stack))
  (setv p x)
  (setv q (/ y 0)))

; comment before StupidGit
(defclass StupidGit []
  "A longer,
    indented

       docstring."

  (defn abuse [self a b c]
    "Another

        docstring

     containing
\t

    tabs

     "
    (self.argue a b c)))


(defclass MalodorousPervert [StupidGit]
  (defn abuse [self a b c])
  (defn [property] contradiction [self]))


(defclass ParrotDroppings [])


(defclass FesteringGob [MalodorousPervert ParrotDroppings]
  (defn abuse [self a b c])
  (defn _getter [self])
  (setv contradiction (property _getter)))


(defn :async lobbest [grenade])


; Test that getsource works on a line that includes
; a closing parenthesis with the opening paren being in another line
#(
) (setv after_closing (fn [] 1))


(defclass ParentNoDoc []
  (defn [hy.I.functools.cached_property] foo [self]))

(defclass ChildNoDoc [ParentNoDoc])
