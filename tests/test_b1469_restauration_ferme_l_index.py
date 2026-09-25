"""B-1469 (recette P-146, lot 5, KO-9) : après une restauration, « Effacer
toutes mes données » laissait sur disque l'index vectoriel (profil et
contact nommés), sans message : « attempt to write a readonly database ».
La restauration fermait la base mais jamais le client Qdrant ; elle
remplaçait le dossier `qdrant` sous ses pieds, et le client gardait une
connexion vers le fichier supprimé. Toute écriture vectorielle échouait
ensuite, la purge comprise.

Qdrant est une doublure dans les tests : on vérifie que la restauration
ferme le client, pour qu'il se rouvre sur les fichiers restaurés."""

import pytest

PASSE = "Passphrase-Test-123"


@pytest.mark.asyncio
async def test_la_restauration_ferme_le_client_vectoriel(client, monkeypatch):
    import app.services.qdrant as module

    doublure = module.get_qdrant_service()
    monkeypatch.setattr(module, "_qdrant_service", doublure)
    doublure.close.reset_mock()

    sauvegarde = await client.post("/api/data/backup", json={"password": PASSE})
    assert sauvegarde.status_code == 200, sauvegarde.text
    nom = sauvegarde.json()["backup_name"]
    doublure.close.reset_mock()

    reponse = await client.post(f"/api/data/restore/{nom}?confirm=true", json={"password": PASSE})
    assert reponse.status_code == 200, reponse.text
    assert doublure.close.called, "le client Qdrant n'a pas été fermé : il écrit ensuite dans un fichier supprimé"


@pytest.mark.asyncio
async def test_une_purge_qui_ne_vide_pas_l_index_le_dit(client, monkeypatch):
    import app.services.qdrant as module

    doublure = module.get_qdrant_service()
    monkeypatch.setattr(doublure.client.delete, "side_effect", RuntimeError("attempt to write a readonly database"))
    reponse = await client.delete("/api/data/all?confirm=true")
    assert reponse.status_code == 200, reponse.text
    corps = reponse.json()
    assert "index de recherche n'a pas pu être vidé" in corps["note"], corps["note"]
    assert corps.get("index_vide") is False
