import subprocess


def test_bin_hy():
    p = subprocess.Popen("echo | bin/hy",
                         shell=True)
    p.wait()
    assert p.returncode == 0
