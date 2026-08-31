"""Un refus de génération doit dire quoi faire, pas seulement constater.

Incident du 31/08/2026, trouvé par Ludo dans le chat (pas dans le créateur de
fichiers). Le modèle posait encore ses questions à l'utilisateur (« montant de
ton apport ? ») et a déclenché l'outil de génération dans le même tour. L'outil
a reçu les questions comme contenu, n'y a trouvé aucun tableau, et a refusé.

Le refus remontait tel quel : « Échec de génération du document : le contenu
produit n'est pas exploitable (aucun tableau de données) ». Ce texte ne sert ni
à l'utilisateur, qui lit une panne là où il manquait juste des chiffres, ni au
modèle, qui reçoit un constat sans consigne et peut boucler à l'identique.
"""
import pytest
from app.services import workspace_tools


class _ReponseEnEchec:
    success = False
    error = "le contenu produit n'est pas exploitable (aucun tableau de données)"
    file_name = None
    file_id = None


class _RegistreQuiRefuse:
    output_dir = "/tmp"

    async def execute(self, *_a, **_k):
        return _ReponseEnEchec()


@pytest.mark.asyncio
async def test_le_refus_dit_au_modele_de_demander_les_chiffres(monkeypatch):
    # L'import est local à la fonction : on accroche le module d'origine.
    from app.services import skills as module_skills

    monkeypatch.setattr(
        module_skills, "get_skills_registry", lambda: _RegistreQuiRefuse()
    )
    message = await workspace_tools._generate_document(
        {
            "format": "xlsx",
            "content": "Montant de ton apport ? Montant d'emprunt envisagé ?",
            "title": "Prévisionnel boucherie",
        },
        None,
    )
    bas = message.lower()
    assert "demande" in bas, (
        f"le refus doit demander les informations manquantes : {message!r}"
    )
    assert "même contenu" in bas or "à l'identique" in bas, (
        f"le refus doit interdire de réessayer tel quel : {message!r}"
    )
    # La cause reste dite : sans elle, ni l'utilisateur ni le modèle ne savent
    # ce qui manquait.
    assert "tableau" in bas, f"la cause doit rester lisible : {message!r}"
