"""US-001 : durcissement du sandbox d'exécution de code (skills Office).

Deux protections :
1. Blocage de l'introspection par dunders (évasion classique du namespace
   restreint : ().__class__.__bases__[0].__subclasses__()).
2. Exécution dans un sous-process spawn isolé : l'interpréteur enfant n'hérite
   pas de la mémoire du backend (token de session, clé Fernet), donc une
   éventuelle évasion ne donne pas accès aux secrets du process principal.
"""
import queue

import pytest
from app.services.skills.code_executor import (
    CodeExecutionError,
    _run_generation_in_subprocess,
    execute_sandboxed,
    validate_code,
)

XLSX_OK = "wb = Workbook()\nws = wb.active\nws['A1'] = title\nwb.save(output_path)"


@pytest.mark.parametrize(
    "snippet",
    [
        "x = ().__class__.__bases__",
        "x = ().__class__.__subclasses__()",
        "x = type.__mro__",
        "x = (1).__class__.__globals__",
        "x = ().__class__.__base__.__subclasses__()",
    ],
)
def test_validate_code_bloque_introspection_dunder(snippet):
    is_valid, _ = validate_code(snippet)
    assert is_valid is False


def test_validate_code_accepte_du_code_office_legitime():
    is_valid, msg = validate_code(XLSX_OK)
    assert is_valid is True, msg


def test_worker_genere_le_fichier_et_signale_ok(tmp_path):
    out = tmp_path / "test.xlsx"
    rq: queue.Queue = queue.Queue()
    _run_generation_in_subprocess(XLSX_OK, str(out), "Mon titre", "xlsx", 10, rq)
    status, _ = rq.get_nowait()
    assert status == "ok"
    assert out.exists()


def test_worker_signale_erreur_sur_code_qui_leve(tmp_path):
    rq: queue.Queue = queue.Queue()
    _run_generation_in_subprocess(
        "raise ValueError('boum')", str(tmp_path / "x.xlsx"), "T", "xlsx", 10, rq
    )
    status, detail = rq.get_nowait()
    assert status == "error"
    assert "boum" in detail


@pytest.mark.asyncio
async def test_execute_sandboxed_rejette_evasion_dunder(tmp_path):
    code = "wb = Workbook()\nx = ().__class__.__bases__\nwb.save(output_path)"
    with pytest.raises(CodeExecutionError):
        await execute_sandboxed(code, str(tmp_path / "x.xlsx"), "T", "xlsx")


@pytest.mark.asyncio
async def test_execute_sandboxed_passe_par_un_sous_process_spawn(monkeypatch, tmp_path):
    """L'exécution doit transiter par un Process spawn isolé, pas par le thread
    du backend (sinon une évasion accéderait aux secrets en mémoire)."""
    import multiprocessing as mp

    captured: dict = {}
    real_get_context = mp.get_context

    class _Q:
        def get(self, timeout=None):
            return ("ok", "")

    class _P:
        def __init__(self, target, args, daemon=False):
            captured["target"] = target

        def start(self):
            pass

        def is_alive(self):
            return False

        def join(self, t=None):
            pass

        def terminate(self):
            pass

    class _Ctx:
        def Queue(self):
            return _Q()

        def Process(self, target, args, daemon=False):
            return _P(target, args, daemon)

    monkeypatch.setattr(
        mp, "get_context", lambda m: _Ctx() if m == "spawn" else real_get_context(m)
    )

    await execute_sandboxed(XLSX_OK, str(tmp_path / "x.xlsx"), "T", "xlsx")
    assert captured["target"].__name__ == "_run_generation_in_subprocess"
