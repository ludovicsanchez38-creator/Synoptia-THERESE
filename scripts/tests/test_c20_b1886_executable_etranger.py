"""B-1886 : un PE étranger avec table de certificats factice passe la garde."""

import importlib.util
import io
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]


def test_un_executable_etranger_ne_passe_pas_par_sa_seule_table_pe(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location("licences_c20", ROOT / "scripts/verify_packaged_licenses.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    raw = bytearray(0x200)
    raw[:2] = b"MZ"
    raw[0x3C:0x40] = (0x80).to_bytes(4, "little")
    raw[0x80:0x84] = b"PE\0\0"
    optional = 0x80 + 24
    raw[optional:optional + 2] = (0x20B).to_bytes(2, "little")
    security = optional + 112 + 4 * 8
    raw[security:security + 8] = (0x1000).to_bytes(4, "little") + (0x200).to_bytes(4, "little")
    etranger = bytes(raw) + b"binaire tiers, aucune signature reelle"
    assert module.authenticode_signed(etranger)
    assert module.system.sha(etranger) != module.system.sha(b"binaire de ce build")

    dossier = Path("/virtuel/installeur")
    moteur = dossier / "backend.exe"
    principal = dossier / "therese.exe"
    fichiers = {moteur: b"MZmoteur", principal: etranger}
    ancien_rglob, ancien_is_file, ancien_open, ancien_read_bytes = Path.rglob, Path.is_file, Path.open, Path.read_bytes
    monkeypatch.setattr(Path, "rglob", lambda p, motif: iter(fichiers) if p == dossier and motif == "*" else (iter(()) if p == dossier else ancien_rglob(p, motif)))
    monkeypatch.setattr(Path, "is_file", lambda p: True if p in fichiers else ancien_is_file(p))
    monkeypatch.setattr(Path, "open", lambda p, *a, **kw: io.BytesIO(fichiers[p]) if p in fichiers else ancien_open(p, *a, **kw))
    monkeypatch.setattr(Path, "read_bytes", lambda p: fichiers[p] if p in fichiers else ancien_read_bytes(p))
    monkeypatch.setattr(module, "check_resources", lambda *_: None)
    monkeypatch.setattr(module, "engine_name", lambda _: "backend.exe")
    monkeypatch.setattr(module, "built_digests", lambda *_: {module.system.sha(b"binaire de ce build")})
    monkeypatch.setattr(module.system, "onefile", lambda _: {})
    monkeypatch.setattr(module.system, "verify_files", lambda *_: None)

    with pytest.raises(ValueError):
        module.verify_directory(dossier, {"files": {}}, "Windows", package="msi")
