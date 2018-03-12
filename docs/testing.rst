=======
Testing
=======

The Hy package provides a very basic pytest plugin out of the box to
help testing Hy code.

A simple test function with just four lines of code::

    # content of test_sample.hy
    (defn func [x]
      (+ x 1))

    (def test-answer []
      (assert (func 3) 5))

You can now execute the test function::

    $ pytest
    =========================== test session starts ============================
    platform linux -- Python 3.x.y, pytest-3.x.y, py-1.x.y, pluggy-0.x.y
    rootdir: $REGENDOC_TMPDIR, inifile:
    plugins: hy-x.y
    collected 1 item

    test_sample.hy F                                                     [100%]

    ================================= FAILURES =================================
    _______________________________ test_answer ________________________________

	(defn test-answer []
    >     (assert (= (func 3) 5)))
    E     AssertionError

    test_sample.hy:5: AssertionError
    ========================= 1 failed in 0.12 seconds =========================

This test returns a failure report because ``func(3)`` does not return ``5``.

``pytest`` will run all files of the form test_*.hy or \*_test.hy in
the current directory and its subdirectories. It will follow the
`standard test discovery rules
<https://docs.pytest.org/en/latest/goodpractices.html#test-discovery>`_,
but that its customized with ``hy_files`` rather than with
``python_files``.
