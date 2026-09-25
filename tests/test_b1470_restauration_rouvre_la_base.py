"""B-1470 (recette P-146, lot 5, KO-10) : après une restauration, le modèle
actif passait seul de qwen3:8b à un autre modèle Ollama. La restauration
fermait la base (`close_db` remet le moteur synchrone à None) et rien ne la
rouvrait avant un redémarrage manuel : la lecture des préférences du modèle
échouait (« Database not initialized ») et le chat retombait sur le premier
modèle venu. La restauration rouvre la base et fait relire les préférences."""

import pytest

PASSE = "Passphrase-Test-123"


@pytest.mark.asyncio
async def test_apres_restauration_la_base_se_lit_et_le_modele_se_relit(client):
    import app.services.llm as llm
    from app.models.database import get_sync_connection

    sauvegarde = await client.post("/api/data/backup", json={"password": PASSE})
    assert sauvegarde.status_code == 200, sauvegarde.text
    llm.get_llm_service()  # un service déjà construit, comme dans l'app lancée

    reponse = await client.post(
        f"/api/data/restore/{sauvegarde.json()['backup_name']}?confirm=true", json={"password": PASSE},
    )
    assert reponse.status_code == 200, reponse.text
    with get_sync_connection() as connexion:  # levait « Database not initialized »
        assert connexion is not None
    assert llm._llm_service is None, "le service de modèles garde la configuration lue sans base"
