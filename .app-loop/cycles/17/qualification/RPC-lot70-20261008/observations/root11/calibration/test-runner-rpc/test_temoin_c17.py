import os

def test_temoin_c17():
    assert (2 if os.environ.get("C17_TEST_RUNNER_DEFECT") == "1" else 1) == 1
