"""US-016 : performance backend - démarrage à froid et latence par message.

Le coût n°1 était l'import de torch (via sentence_transformers) déclenché par
les réexports d'app/services/__init__.py : payé par le backend AU DÉMARRAGE et
par le sous-process sandbox à CHAQUE génération de document.
"""
import subprocess
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).parent.parent / "src" / "backend"


def test_import_app_services_ne_charge_pas_torch():
    """Importer app.services (et app.services.embeddings) ne doit pas charger
    torch ni sentence_transformers - vérifié dans un interpréteur NEUF."""
    code = (
        "import sys; import app.services; import app.services.embeddings; "
        "leaked = [m for m in ('torch', 'sentence_transformers') if m in sys.modules]; "
        "print('LEAKED:' + ','.join(leaked) if leaked else 'CLEAN')"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True, text=True, cwd=str(BACKEND), timeout=60,
    )
    assert result.returncode == 0, result.stderr[-500:]
    assert "CLEAN" in result.stdout, (
        f"torch/sentence_transformers chargés à l'import : {result.stdout!r} - "
        "le démarrage à froid et le sous-process sandbox repayent des secondes "
        "d'import (US-016)"
    )


def test_services_init_sans_reexports():
    """Les réexports d'app/services/__init__.py ne doivent pas revenir
    (ils forçaient l'import en cascade de tous les services)."""
    content = (BACKEND / "app" / "services" / "__init__.py").read_text(encoding="utf-8")
    import_lines = [
        line for line in content.splitlines()
        if line.strip().startswith(("from ", "import "))
    ]
    assert import_lines == [], f"Réexports revenus dans services/__init__.py : {import_lines}"


def test_mcp_init_en_arriere_plan():
    """Le spawn MCP (npx, réseau) ne doit pas bloquer le lifespan : /health
    doit répondre dès que le coeur est prêt."""
    content = (BACKEND / "app" / "main.py").read_text(encoding="utf-8")
    assert "_init_mcp_bg" in content, "init MCP doit être une tâche de fond"
    assert "asyncio.create_task(_init_mcp_bg())" in content


def test_entity_names_requete_ciblee():
    """_get_existing_entity_names ne doit plus hydrater toutes les entités."""
    content = (BACKEND / "app" / "routers" / "chat.py").read_text(encoding="utf-8")
    assert "select(Contact.first_name, Contact.last_name, Contact.company)" in content
    assert "select(Project.name)" in content


@pytest.mark.asyncio
async def test_tasks_pagines(client, db_session):
    """US-016 : la liste des tâches est bornée (limit/offset)."""
    from app.models.entities import Task

    for i in range(15):
        db_session.add(Task(id=f"t-{i:02d}", title=f"Tâche {i}", status="todo"))
    await db_session.commit()

    resp = await client.get("/api/tasks/?limit=10")
    assert resp.status_code == 200
    assert len(resp.json()) == 10

    resp_page2 = await client.get("/api/tasks/?limit=10&offset=10")
    assert resp_page2.status_code == 200
    assert len(resp_page2.json()) == 5

    # Pas de doublons entre pages
    ids_p1 = {t["id"] for t in resp.json()}
    ids_p2 = {t["id"] for t in resp_page2.json()}
    assert not ids_p1 & ids_p2
