"""Le prompt ne promet que les outils réellement disponibles.

Relevé par la relecture adversariale du retrait d'outil : le bloc « capacités »
annonce ses verbes par paires, et la paire entière est conditionnée à un seul
nom. `create_calendar_event` restait donc annoncé après avoir été retiré parce
que `list_calendar_events`, lui, était encore là.

C'est exactement la consigne qui produit la seconde carte : un modèle faible
lit la capacité, invente l'appel, et redemande une action déjà en attente.
"""
import re
from pathlib import Path

SOURCE = Path("src/backend/app/routers/chat.py").read_text()


def _bloc_capacites() -> list[tuple[str, str]]:
    """(condition, ligne annoncée) pour chaque capacité du prompt."""
    paires = []
    lignes = SOURCE.split("\n")
    for i, ligne in enumerate(lignes):
        if "capabilities +=" not in ligne:
            continue
        for precedente in reversed(lignes[max(0, i - 3) : i]):
            if precedente.strip().startswith("if ") and "tool_names" in precedente:
                paires.append((precedente, ligne))
                break
    return paires


def test_chaque_outil_annonce_est_conditionne_a_sa_propre_presence():
    manquants = []
    for condition, annonce in _bloc_capacites():
        annonces = set(re.findall(r"\*\*([a-z_]+)\*\*", annonce))
        gardes = set(re.findall(r'"([a-z_]+)" in tool_names', condition))
        for outil in annonces - gardes:
            manquants.append(f"{outil} annoncé sous la garde de {sorted(gardes)}")
    assert not manquants, "outils promis sans vérifier leur présence : " + "; ".join(
        manquants
    )
