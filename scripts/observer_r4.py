"""Conserver immédiatement les preuves des rouges malgré os._exit hérité."""

def pytest_runtest_logreport(report):
    if report.failed:
        print(f'\nECHEC {report.nodeid} ({report.when})\n{report.longrepr}', flush=True)
