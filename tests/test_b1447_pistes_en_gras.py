"""B-1447 (recette P-146, lot 3, KO-6) : qwen3:8b terminait sa section par
« **Pistes :** » et trois puces. Le marqueur exigeait la ligne exacte
`PISTES:` : rien n'était extrait, et les pistes partaient dans le texte de la
section, donc dans les exports destinés au client.

La variante en gras est acceptée, SEULE sur sa ligne et suivie uniquement de
puces jusqu'à la fin : un bloc final. Un « Pistes : financement… » de
contenu (revue adversariale du lot B) ne coupe toujours rien."""

from app.services.document_orchestrator import parse_draft_output


def test_le_bloc_en_gras_final_est_extrait():
    brut = "Le planning tient en trois temps.\n\n**Pistes :**\n- Agenda partagé\n- Relances automatiques\n* Point hebdomadaire\n"
    contenu, pistes = parse_draft_output(brut)
    assert contenu == "Le planning tient en trois temps."
    assert pistes == ["Agenda partagé", "Relances automatiques", "Point hebdomadaire"]


def test_les_variantes_du_gras_sont_reconnues():
    for marqueur in ("**PISTES:**", "**Pistes:**", "**Pistes** :", "__Pistes :__"):
        contenu, pistes = parse_draft_output(f"Texte.\n{marqueur}\n- Une idée")
        assert (contenu, pistes) == ("Texte.", ["Une idée"]), marqueur


def test_un_gras_suivi_de_texte_reste_du_contenu():
    brut = "Intro.\n**Pistes :**\n- Une idée\nUn paragraphe qui continue la section."
    assert parse_draft_output(brut) == (brut.strip(), [])


def test_une_ligne_de_contenu_pistes_ne_coupe_rien():
    brut = "Pistes : financement bancaire, aides publiques.\n- Une puce de contenu"
    assert parse_draft_output(brut) == (brut.strip(), [])
