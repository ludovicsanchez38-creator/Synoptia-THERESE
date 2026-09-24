"""B-1220 : B-450 incomplet. L'export complet XLSX (POST /api/crm/export/all)
construisait et enregistrait le classeur sur la boucle d'événements :
pendant l'export, l'application ne répondait plus. Les exports unitaires
passent déjà par asyncio.to_thread.
"""

import threading

import pytest


@pytest.mark.asyncio
async def test_le_classeur_de_l_export_complet_est_construit_hors_de_la_boucle(client, monkeypatch):
    from app.services import crm_export

    fils: list[str] = []
    vrai_classeur = crm_export.Workbook

    def classeur_espion(*args, **kwargs):
        fils.append(threading.current_thread().name)
        return vrai_classeur(*args, **kwargs)

    monkeypatch.setattr(crm_export, "Workbook", classeur_espion)
    await client.post("/api/memory/contacts", json={"first_name": "Alice", "last_name": "Martin"})

    resp = await client.post("/api/crm/export/all?format=xlsx")

    assert resp.status_code == 200, resp.text
    assert fils, "le classeur n'a pas été construit"
    # La boucle de l'application tourne dans le fil du portail de TestClient ;
    # un export sorti de la boucle construit son classeur dans un autre fil.
    assert all(nom.startswith(("asyncio_", "ThreadPoolExecutor", "AnyIO worker")) for nom in fils), fils
