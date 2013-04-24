import subprocess


def run_cmd(cmd):
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         shell=True)
    p.wait()
    return p.returncode, p.stdout, p.stderr


def test_bin_hy():
    ret = run_cmd("echo | bin/hy")
    assert ret[0] == 0


def test_bin_hy_stdin():
    ret = run_cmd("echo \"(koan)\" | bin/hy")
    assert ret[0] == 0
    assert "monk" in ret[1].read().decode("utf-8")


def test_bin_hy_cmd():
    ret = run_cmd("bin/hy -c \"(koan)\"")
    assert ret[0] == 0
    assert "monk" in ret[1].read().decode("utf-8")

    ret = run_cmd("bin/hy -c \"(koan\"")
    assert ret[0] == 1
    assert "LexException" in ret[1].read().decode("utf-8")


def test_bin_hy_icmd():
    ret = run_cmd("echo \"(ideas)\" | bin/hy -i \"(koan)\"")
    assert ret[0] == 0
    output = ret[1].read().decode("utf-8")

    assert "monk" in output
    assert "figlet" in output


def test_bin_hy_file():
    ret = run_cmd("bin/hy eg/nonfree/halting-problem/halting.hy")
    assert ret[0] == 0
    assert "27" in ret[1].read().decode("utf-8")
