;;; Hy Multi-Index Slicing module
;; Copyright 2021 the authors.
;; this file is part of Hy, which is free software licensed under the Expat
;; license. See the LICENSE.
"Macros for elegantly slicing and dicing multi-axis and multidimensional sequences.

Libraries like ``numpy`` and ``pandas`` make extensive use of python's slicing syntax
and even extends it to allow multiple slices using tuples. This makes handling
multi-axis (pandas) and multidimensional arrays (numpy) extremely elegant and efficient.
Hy doesn't support Python's sugared slicing syntax (``1::-2 # => slice(1, None, 2)``).
Which makes slicing quite cumbersome, especially when tuple's get thrown into the mix.
Hy's ``cut`` form makes single slices easy, but anything more than that becomes
much more difficult to construct and parse. Where python can express a multidimensional
slice as:

.. code-block:: python

   >>> arr[1:-2:2,3:5,:]

The equivalent in Hy would be::

   => (get arr (, (slice 1 -2 2) (slice 3 5) (slice None)))

which is hardly ideal. This module provides an ``ncut`` macro and a ``#:`` tag macro
that enable python's sugared slicing form in Hy so that the previous could be expressed as::

   => (ncut a 1:-1:2 3:5 :)

or more manually using the tag macro as::

   => (get a (, #: 1:-2:2 #: 3:5 #: :))
"
(eval-and-compile
  (defn parse-colon [sym]
    (lfor index (.split (str sym) ":")
          (if (empty? index) None
              (int index))))

  (defn parse-indexing [sym]
    (cond
      [(and (isinstance sym hy.models.Expression) (= (get sym 0) :))
       `(slice ~@(cut sym 1 None))]

      [(and (symbol? sym) (= sym '...))
       'Ellipsis]

      [(and (isinstance sym (, hy.models.Keyword hy.models.Symbol))
            (in ":" (str sym)))
       (try `(slice ~@(parse-colon sym)) (except [ValueError] sym))]

      [True sym])))

(defmacro ncut [seq key1 #* keys]
  "N-Dimensional ``cut`` macro with shorthand slice notation.

  Libraries like ``numpy`` and ``pandas`` extend Python's sequence
  slicing syntax to work with tuples to allow for elegant handling of
  multidimensional arrays (numpy) and multi-axis selections (pandas).
  A key in ``ncut`` can be any valid kind of index; specific,
  ranged, a numpy style mask. Any library can make use of tuple based
  slicing, so check with each lib for what is and isn't valid.

  Args:
    seq: Slicable sequence
    key1: A valid sequence index. What is valid can change from library to
      library.
    *keys: Additional indices. Specifying more than one index will expand
      to a tuple allowing multi-dimensional indexing.

  Examples:
    Single dimensional list slicing
    ::

       => (ncut (list (range 10)) 2:8:2)
       [2 4 6]

    numpy multidimensional slicing:
    ::

       => (setv a (.reshape (np.arange 36) (, 6 6)))
       => a
       array([[ 0,  1,  2,  3,  4,  5],
              [ 6,  7,  8,  9, 10, 11],
              [12, 13, 14, 15, 16, 17],
              [18, 19, 20, 21, 22, 23],
              [24, 25, 26, 27, 28, 29],
              [30, 31, 32, 33, 34, 35]])
       => (ncut a (, 0 1 2 3 4) (, 1 2 3 4 5))
       array([ 1,  8, 15, 22, 29])
       => (ncut a 3: (, 0 2 5))
       array([[18, 20, 23],
              [24, 26, 29],
              [30, 32, 35]])
       => (ncut a 1:-1:2 3:5)
       array([[ 9, 10],
              [21, 22]])
       => (ncut a ::2 3 None)
       array([[ 3],
              [15],
              [27]])
       => (ncut a ... 0)
       array([ 0,  6, 12, 18, 24, 30])

    Because variables can have colons in Hy (eg: ``abc:def`` is a valid identifier),
    the sugared slicing form only allows numeric literals. In order to construct slices
    that involve names and/or function calls, the form ``(: ...)`` can be used in an
    ``ncut`` expresion as an escape hatch to ``slice``:
    ::

       => (setv abc:def -2)
       => (hy.macroexpand '(ncut a abc:def (: (sum [1 2 3]) None abc:def)))
       (get a (, abc:def (slice (sum [1 2 3]) None abc:def)))

    Pandas allows extensive slicing along single or multiple axes:
    ::

       => (setv s1 (pd.Series (np.random.randn 6) :index (list \"abcdef\")))
       => s1
       a    0.687645
       b   -0.598732
       c   -1.452075
       d   -0.442050
       e   -0.060392
       f    0.440574
       dtype: float64

       => (ncut s1 (: \"c\" None 2))
       c   -1.452075
       e   -0.060392
       dtype: float64

    ::

       => (setv df (pd.DataFrame (np.random.randn 8 4)
                                 :index (pd.date-range \"1/1/2000\" :periods 8)
                                 :columns (list \"ABCD\")))
       => df
                          A         B         C         D
       2000-01-01 -0.185291 -0.803559 -1.483985 -0.136509
       2000-01-02 -3.290852 -0.688464  2.715168  0.750664
       2000-01-03  0.771222 -1.170541 -1.015144  0.491510
       2000-01-04  0.243287  0.769975  0.473460  0.407027
       2000-01-05 -0.857291  2.395931 -0.950846  0.299086
       2000-01-06 -0.195595  0.981791 -0.673646  0.637218
       2000-01-07 -1.022636 -0.854971  0.603573 -1.169342
       2000-01-08 -0.494866  0.783248 -0.064389 -0.960760

       => (ncut df.loc : [\"B\" \"A\"])
                          B         A
       2000-01-01 -0.803559 -0.185291
       2000-01-02 -0.688464 -3.290852
       2000-01-03 -1.170541  0.771222
       2000-01-04  0.769975  0.243287
       2000-01-05  2.395931 -0.857291
       2000-01-06  0.981791 -0.195595
       2000-01-07 -0.854971 -1.022636
       2000-01-08  0.783248 -0.494866

  .. note::

     For more info on the capabilities of multiindex slicing, check with the respective
     library.

     - `Pandas <https://pandas.pydata.org/pandas-docs/stable/user_guide/indexing.html>`_
     - `Numpy <https://numpy.org/doc/stable/reference/arrays.indexing.html>`_
  "
  `(get ~seq ~(if keys
               `(, ~@(map parse-indexing (, key1 #* keys)))
               (parse-indexing key1))))

(defmacro "#:" [key]
  "Shorthand tag macro for constructing slices using Python's sugared form.

  Examples:
    ::

       => #: 1:4:2
       (slice 1 4 2)
       => (get [1 2 3 4 5] #: 2::2)
       [3 5]

    Numpy makes use of ``Ellipsis`` in its slicing semantics so they can also be
    constructed with this macro in their sugared ``...`` form.
    ::

       => #: ...
       Ellipsis

    Slices can technically also contain strings (something pandas makes use of
    when slicing by string indices) and because Hy allows colons in identifiers,
    to construct these slices we have to use the form ``(...)``:
    ::

       => #:(\"colname\" 1 2)
       (slice \"colname\" 1 2)
  "
  (if (isinstance key hy.models.Expression) (parse-indexing `(: ~@key))
      (parse-indexing key)))
