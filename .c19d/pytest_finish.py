"""Le hook historique sort trop tôt ; terminer après le résumé pytest."""
import os
import sys

import pytest

_status = 0


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_sessionfinish(session, exitstatus):
    global _status
    _status = int(exitstatus)
    yield


def pytest_unconfigure(config):
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(_status)
