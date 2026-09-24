"""B-1191 : une commande absente du PATH confiné est nommée, pas prise pour un confinement en panne.

Attendu : MESSAGE_REFUS (bac_a_sable.py:98-102) est réservé au confinement qui
ne peut pas tourner (commentaire tools.py:789 « Le confinement lui-même n'a pas
démarré ») ; une commande introuvable est une autre cause, à nommer (avant
B-1153, create_subprocess_exec levait FileNotFoundError et run_command rendait
« Erreur d'exécution : [Errno 2] No such file or directory: 'pytest' »).
Mesure : vrai /usr/bin/sandbox-exec, vrai profil ; PATH du moteur réduit à
/usr/bin:/bin (PATH repris tel quel par environnement_confine, _ENV_CONSERVE).
"""

import shutil
import sys

import pytest

pytestmark = pytest.mark.skipif(sys.platform != "darwin", reason="Seatbelt macOS")


@pytest.mark.asyncio
async def test_pytest_absent_du_path_n_est_pas_un_confinement_en_panne(monkeypatch, tmp_path):
    from app.services.agents import bac_a_sable
    from app.services.agents.tools import AgentToolExecutor

    async def confinement_disponible():
        return None

    # Isole la cause : la sonde n'est pas en jeu, seul le lancement l'est.
    monkeypatch.setattr(bac_a_sable, "confinement_indisponible", confinement_disponible)
    monkeypatch.setenv("PATH", "/usr/bin:/bin")
    assert shutil.which("pytest", path="/usr/bin:/bin") is None

    reponse = await AgentToolExecutor(str(tmp_path)).run_command("pytest -q")
    assert "désactivées" not in reponse and "pytest" in reponse, reponse


@pytest.mark.asyncio
async def test_temoin_commande_presente_s_execute_confinee(monkeypatch, tmp_path):
    """Témoin : make (présent dans /usr/bin) part bien, confiné, et rend son code."""
    from app.services.agents import bac_a_sable
    from app.services.agents.tools import AgentToolExecutor

    async def confinement_disponible():
        return None

    monkeypatch.setattr(bac_a_sable, "confinement_indisponible", confinement_disponible)
    monkeypatch.setenv("PATH", "/usr/bin:/bin")
    reponse = await AgentToolExecutor(str(tmp_path)).run_command("make test")
    assert reponse.startswith("Code retour"), reponse
