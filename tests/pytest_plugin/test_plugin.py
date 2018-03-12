def test_hy_test(testdir):
    testdir.makefile(
        "hy",
        test_example="""
            (defn test-func1 [])
        """)

    result = testdir.runpytest_subprocess()
    assert result.ret == 0


def test_hy_test_with_fixture(testdir):
    testdir.makefile(
        "hy",
        test_example="""
            (import [pytest [fixture]])

            #@(fixture (defn foobar [] 42))

            (defn test-func1 [foobar]
              (assert (= foobar 42)))
        """)

    result = testdir.runpytest_subprocess()
    assert result.ret == 0


def test_hy_test_class(testdir):
    testdir.makefile(
        "hy",
        test_example="""
            (defclass Tests []
              (defn test-func1 [self]))
        """)

    result = testdir.runpytest_subprocess()
    assert result.ret == 0
