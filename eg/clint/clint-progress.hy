(import [clint.textui [progress]]
        [time [sleep]]
        [random [random]])

(for [x (.bar progress (range 100))]
  (sleep (* (random) 0.1)))
