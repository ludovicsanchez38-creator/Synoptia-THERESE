"""Plugin optionnel du banc : interdit et décompte toute connexion sortante."""

import socket

_tentatives = 0


def _refuser_connexion(*args, **kwargs):
    global _tentatives
    _tentatives += 1
    raise OSError("Connexion interdite pendant le banc hors ligne")


socket.socket.connect = _refuser_connexion
socket.socket.connect_ex = _refuser_connexion
socket.create_connection = _refuser_connexion


def pytest_sessionfinish(session, exitstatus):
    terminal = session.config.pluginmanager.get_plugin("terminalreporter")
    if terminal:
        terminal.write_line(f"Connexions interdites tentées : {_tentatives}")
    if _tentatives:
        session.exitstatus = 1
