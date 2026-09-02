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

SOURCE = Path("src/backend/app/routers/chat.py").read_text(encoding="utf-8")


def _bloc_capacites(source: str = SOURCE) -> list[tuple[str, str]]:
    """(condition, ligne annoncée) pour chaque capacité du prompt."""
    paires = []
    lignes = source.split("\n")
    for i, ligne in enumerate(lignes):
        if "capabilities +=" not in ligne:
            continue
        for precedente in reversed(lignes[max(0, i - 3) : i]):
            if precedente.strip().startswith("if ") and "tool_names" in precedente:
                paires.append((precedente, ligne))
                break
    return paires


def _capacites_sans_garde(source: str = SOURCE) -> list[str]:
    """Ce que le balayage reproche au prompt — instrument compris.

    B-077 : la liste des paires pouvait tomber à zéro (source vide, verbe
    `capabilities +=` renommé, garde `in tool_names` renommée) sans que rien ne
    le dise. Un balayage qui ne trouve plus sa cible ne prouve pas l'absence de
    faute : il prouve qu'il a cessé de regarder. Le défaut d'instrument est donc
    rendu comme un défaut à part entière.
    """
    paires = _bloc_capacites(source)
    verbes = [ligne for ligne in source.split("\n") if "capabilities +=" in ligne]
    manquants = []
    if not paires:
        manquants.append(
            "le balayage ne trouve plus aucune capacité : le verbe "
            "« capabilities += » ou la garde « in tool_names » a changé dans "
            "chat.py, et ce test ne surveille plus rien"
        )
    elif len(verbes) - len(paires) > 1:
        # Une seule ligne non appariée est attendue : le bloc des outils MCP,
        # gardé par `if mcp_tools:` et annoncé « **Outils externes** ».
        manquants.append(
            f"{len(verbes) - len(paires)} lignes « capabilities += » ne sont "
            "appariées à aucune garde `in tool_names` (une seule est attendue, "
            "celle des outils MCP) : le balayage a perdu des capacités en route"
        )
    for condition, annonce in paires:
        annonces = set(re.findall(r"\*\*([a-z_]+)\*\*", annonce))
        gardes = set(re.findall(r'"([a-z_]+)" in tool_names', condition))
        for outil in annonces - gardes:
            manquants.append(f"{outil} annoncé sous la garde de {sorted(gardes)}")
    return manquants


def test_chaque_outil_annonce_est_conditionne_a_sa_propre_presence():
    manquants = _capacites_sans_garde()
    assert not manquants, "outils promis sans vérifier leur présence : " + "; ".join(
        manquants
    )


def test_le_balayage_rougit_quand_il_ne_voit_plus_sa_cible():
    """B-077 : sans plancher, un source aveugle laissait le test vert.

    Trois façons de rendre le balayage aveugle, toutes atteignables par un
    refactor légitime de chat.py. Aucune ne doit passer en silence.
    """
    aveugles = {
        "source vide": "",
        "verbe renommé": SOURCE.replace("capabilities +=", "capacites +="),
        "garde renommée": SOURCE.replace(" in tool_names", " in outils_dispo"),
    }
    muets = [nom for nom, src in aveugles.items() if not _capacites_sans_garde(src)]
    assert muets == [], (
        "le balayage ne voit plus le bloc capacités et ne le dit pas : " + str(muets)
    )


# ---------------------------------------------------------------------------
# D6 (Dr_logic, 27/08) : « les documents indexés » fait partir Thérèse sur des
# factures.
#
# BUG-148 (juillet) corrigeait un vrai défaut : « envoie la facture
# FACT-2026-001 » finissait en « je n'ai pas d'outil de recherche pour les
# documents locaux », et le modèle proposait de RECRÉER la facture. Pour
# l'empêcher, on lui a ordonné d'utiliser search_invoices « AU LIEU de dire
# que tu ne peux pas chercher les documents locaux ».
#
# Sauf que la phrase du modèle était exacte : il n'a toujours aucun outil pour
# les documents indexés. L'ordre a débordé de son domaine, et il envoie
# désormais vers les factures quiconque parle de ses documents. La description
# de l'outil, elle, est correctement bornée aux factures et devis.
#
# Une capacité ne revendique que le domaine de son outil.
# ---------------------------------------------------------------------------

DOMAINES_ETRANGERS = (
    "les documents locaux",
    "les documents indexés",
    "les documents indexes",
    "tes documents",
    "les fichiers locaux",
)


def _ligne_de_capacite(outil: str) -> str:
    for _condition, annonce in _bloc_capacites():
        if f"**{outil}**" in annonce:
            return annonce
    raise AssertionError(f"capacité {outil} introuvable")


def test_la_recherche_de_factures_ne_revendique_pas_tous_les_documents():
    ligne = _ligne_de_capacite("search_invoices").lower()
    debordements = [d for d in DOMAINES_ETRANGERS if d in ligne]
    assert not debordements, (
        "la capacité search_invoices revendique un domaine qui n'est pas le sien : "
        + ", ".join(debordements)
    )


def test_la_consigne_utile_de_bug_148_est_conservee():
    """Ne pas jeter le correctif de juillet en corrigeant son débordement."""
    ligne = _ligne_de_capacite("search_invoices").lower()
    assert "recreer" in ligne or "recréer" in ligne, (
        "la consigne « ne propose JAMAIS de recréer un document existant » a disparu"
    )
    # B1 (28/08) : ce test exigeait le mot « pièce jointe ». La consigne dit
    # désormais l'impossibilité PLUS LARGEMENT — l'envoi n'existe nulle part,
    # y compris depuis la vue Facturation, où l'ancienne rédaction orientait
    # l'utilisateur dans un cul-de-sac. La propriété protégée (le modèle sait
    # qu'il ne peut pas envoyer, et ne doit pas l'affirmer) est conservée et
    # élargie ; seul le mot change.
    assert "impossible" in ligne, (
        "la consigne sur l'envoi impossible a disparu"
    )
    assert "send_email" in ligne, (
        "le modèle doit savoir explicitement de ne pas détourner send_email"
    )


# ---------------------------------------------------------------------------
# D6, suite : le catalogue de fichiers doit être ANNONCÉ.
#
# Un outil que le modèle ignore n'existe pas. C'est précisément ce qui a fait
# durer le manque : trois signalements, et à chaque fois le modèle répondait
# qu'il n'avait pas d'outil — ce qui était vrai.
# ---------------------------------------------------------------------------


def test_le_catalogue_de_fichiers_est_annonce_au_modele():
    annonces = " ".join(annonce for _c, annonce in _bloc_capacites())
    assert "**search_files**" in annonces
    assert "**read_file**" in annonces


def test_le_catalogue_dit_sa_frontiere_avec_la_facturation():
    """Sans frontière, le modèle retombe sur search_invoices — c'était D6."""
    ligne = _ligne_de_capacite("search_files").lower()
    assert "facture" in ligne, "la capacité doit dire ce qu'elle ne couvre pas"
