"""Une capture déposée dans le chat doit arriver au modèle comme une image.

Incident du 31/08/2026 : Ludo glisse une capture d'écran dans THÉRÈSE et lit
« Type de fichier non autorisé pour l'indexation : '.png' [...] Ce fichier ne
sera pas utilisé pour répondre. » Vérification faite, aucun chemin image
n'existait dans l'application, sur aucun fournisseur, alors que le modèle
sélectionné (gpt-5.6-luna) sait lire une image.

Ces tests portent le cœur : qu'un message puisse porter une image, et que
chaque fournisseur la reçoive dans SON format.
"""

from app.services.context import ContextWindow
from app.services.providers.base import ImageJointe, Message

_PNG = "iVBORw0KGgoAAAANSUhEUg=="


def _message_avec_image(texte: str = "Que vois-tu ?") -> Message:
    return Message(
        role="user",
        content=texte,
        images=[ImageJointe(media_type="image/png", donnees_base64=_PNG)],
    )


def test_openai_recoit_l_image_en_bloc_image_url():
    fenetre = ContextWindow(messages=[_message_avec_image()])
    contenu = fenetre.to_openai_format()[-1]["content"]
    assert isinstance(contenu, list), "le contenu doit devenir une liste de blocs"
    types = [bloc.get("type") for bloc in contenu]
    assert "image_url" in types, f"aucun bloc image : {types}"
    bloc = next(b for b in contenu if b.get("type") == "image_url")
    assert bloc["image_url"]["url"] == f"data:image/png;base64,{_PNG}"


def test_anthropic_recoit_l_image_en_bloc_source_base64():
    fenetre = ContextWindow(messages=[_message_avec_image()])
    _, messages = fenetre.to_anthropic_format()
    contenu = messages[-1]["content"]
    assert isinstance(contenu, list)
    bloc = next(b for b in contenu if b.get("type") == "image")
    assert bloc["source"]["media_type"] == "image/png"
    assert bloc["source"]["data"] == _PNG


def test_gemini_recoit_l_image_en_inline_data():
    fenetre = ContextWindow(messages=[_message_avec_image()])
    _, contents = fenetre.to_gemini_format()
    parts = contents[-1]["parts"]
    part = next(p for p in parts if "inline_data" in p)
    assert part["inline_data"]["mime_type"] == "image/png"
    assert part["inline_data"]["data"] == _PNG


def test_une_image_sans_texte_n_est_pas_jetee():
    """Le filtre des messages vides jetait tout message sans contenu texte.

    Déposer une capture sans rien écrire est le geste le plus naturel : il ne
    doit pas faire disparaître le message.
    """
    fenetre = ContextWindow(messages=[_message_avec_image(texte="")])
    assert len(fenetre.to_openai_format()) == 1, "message image-seul jeté (OpenAI)"
    assert len(fenetre.to_anthropic_format()[1]) == 1, "jeté (Anthropic)"
    assert len(fenetre.to_gemini_format()[1]) == 1, "jeté (Gemini)"


def test_un_message_sans_image_garde_un_contenu_texte_simple():
    """Aucune régression : sans image, le format ne change pas."""
    fenetre = ContextWindow(messages=[Message(role="user", content="Bonjour")])
    assert fenetre.to_openai_format()[-1]["content"] == "Bonjour"
    assert fenetre.to_anthropic_format()[1][-1]["content"] == "Bonjour"


# --- Chargement depuis le disque -------------------------------------------

import base64  # noqa: E402
from pathlib import Path  # noqa: E402

import pytest  # noqa: E402


def _ecrire_png(dossier: Path, nom: str, octets: bytes = b"\x89PNG\r\n\x1a\n") -> Path:
    chemin = dossier / nom
    chemin.write_bytes(octets)
    return chemin


def test_une_image_est_chargee_et_encodee(tmp_path: Path):
    from app.services.images_jointes import charger_images_jointes

    chemin = _ecrire_png(tmp_path, "capture.png")
    images, ecartees = charger_images_jointes([str(chemin)])

    assert ecartees == []
    assert len(images) == 1
    assert images[0].media_type == "image/png"
    assert base64.b64decode(images[0].donnees_base64) == chemin.read_bytes()


def test_un_fichier_texte_n_est_pas_pris_pour_une_image(tmp_path: Path):
    from app.services.images_jointes import charger_images_jointes

    note = tmp_path / "note.md"
    note.write_text("# Titre", encoding="utf-8")
    images, ecartees = charger_images_jointes([str(note)])
    assert images == [] and ecartees == []


def test_une_image_trop_lourde_est_ecartee_et_nommee(tmp_path: Path):
    """Écartée en le DISANT : une image avalée en silence ferait croire au
    lecteur que le modèle l'a vue."""
    from app.services.images_jointes import TAILLE_MAX_IMAGE, charger_images_jointes

    grosse = _ecrire_png(tmp_path, "enorme.png", b"\x89PNG" + b"0" * TAILLE_MAX_IMAGE)
    images, ecartees = charger_images_jointes([str(grosse)])
    assert images == []
    assert any("enorme.png" in e for e in ecartees), ecartees


def test_une_image_absente_du_disque_est_ecartee_pas_fatale(tmp_path: Path):
    from app.services.images_jointes import charger_images_jointes

    images, ecartees = charger_images_jointes([str(tmp_path / "fantome.png")])
    assert images == []
    assert any("fantome.png" in e for e in ecartees), ecartees


def test_le_nombre_d_images_par_tour_est_borne_et_dit(tmp_path: Path):
    from app.services.images_jointes import PLAFOND_IMAGES_PAR_TOUR, charger_images_jointes

    chemins = [
        str(_ecrire_png(tmp_path, f"c{i}.png"))
        for i in range(PLAFOND_IMAGES_PAR_TOUR + 2)
    ]
    images, ecartees = charger_images_jointes(chemins)
    assert len(images) == PLAFOND_IMAGES_PAR_TOUR
    assert len(ecartees) == 2, ecartees


@pytest.mark.parametrize(
    ("nom", "attendu"),
    [
        ("a.png", "image/png"),
        ("b.JPG", "image/jpeg"),
        ("c.jpeg", "image/jpeg"),
        ("d.webp", "image/webp"),
        ("e.gif", "image/gif"),
    ],
)
def test_le_type_media_suit_l_extension(tmp_path: Path, nom: str, attendu: str):
    from app.services.images_jointes import charger_images_jointes

    chemin = _ecrire_png(tmp_path, nom)
    images, _ = charger_images_jointes([str(chemin)])
    assert images[0].media_type == attendu


# --- Câblage dans le chat ---------------------------------------------------


def test_les_images_se_posent_sur_le_dernier_message(tmp_path: Path):
    from app.routers.chat import _attacher_images
    from app.services.providers.base import Message as LLMMessage

    capture = _ecrire_png(tmp_path, "capture.png")
    messages = [
        LLMMessage(role="user", content="premier tour"),
        LLMMessage(role="user", content="Que vois-tu ?"),
    ]
    ecartees = _attacher_images(messages, [str(capture)])

    assert ecartees == []
    assert messages[-1].images, "l'image doit être posée sur le tour courant"
    assert not messages[0].images, "les tours précédents ne sont pas touchés"


def test_un_chemin_image_ne_part_plus_dans_l_extraction_de_texte(tmp_path: Path):
    """C'est la cause exacte du message vu par Ludo.

    Tant qu'une image traverse la chaîne d'indexation, elle produit « Type de
    fichier non autorisé pour l'indexation », que l'utilisateur lit comme un
    refus alors qu'il vient simplement de montrer une capture.
    """
    from app.routers.chat import separer_images_et_documents

    capture = _ecrire_png(tmp_path, "capture.png")
    note = tmp_path / "note.md"
    note.write_text("# Titre", encoding="utf-8")

    documents, images = separer_images_et_documents([str(note), str(capture)])
    assert documents == [str(note)]
    assert images == [str(capture)]


def test_sans_piece_jointe_rien_ne_change(tmp_path: Path):
    from app.routers.chat import _attacher_images
    from app.services.providers.base import Message as LLMMessage

    messages = [LLMMessage(role="user", content="Bonjour")]
    assert _attacher_images(messages, None) == []
    assert messages[-1].images == []
