"""RAG juridique : corpus de références légales vérifiées + lookup par mots-clés.

Ancre les réponses et documents juridiques sur des références VÉRIFIÉES sur sources
officielles (Légifrance/service-public) au lieu de la connaissance périmée du modèle.
Cf. 2e passage personas : Mistral citait L441-6 alors que les pénalités de retard B2B
ont été recodifiées à l'art. L441-10 (ordonnance 2019-359). Le garde-fou prompt
stoppait l'invention mais pas la donnée périmée ; ce corpus la corrige à la source.
"""

import json
import logging
import unicodedata
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

_CORPUS_PATH = Path(__file__).resolve().parent.parent / "data" / "legal_corpus.json"
_MAX_MATCHES = 4


def _norm(text: str) -> str:
    """Minuscule + sans accents : matching robuste (test global : « intérêts »,
    « commerçants » ne matchaient pas les mots-clés sans normalisation)."""
    lowered = text.lower()
    return "".join(
        c for c in unicodedata.normalize("NFD", lowered) if unicodedata.category(c) != "Mn"
    )


@lru_cache(maxsize=1)
def _load_corpus() -> list[dict]:
    """Charge le corpus vérifié (mis en cache)."""
    try:
        data = json.loads(_CORPUS_PATH.read_text(encoding="utf-8"))
        return data.get("entries", [])
    except Exception as e:  # pragma: no cover - corpus manquant/illisible
        logger.warning(f"Corpus juridique illisible : {e}")
        return []


def lookup_legal(message: str, max_matches: int = _MAX_MATCHES) -> list[dict]:
    """Retourne les entrées du corpus dont un mot-clé apparaît dans le message.

    Matching simple par sous-chaîne (le corpus est petit et les mots-clés ciblés) :
    fiable, déterministe, et sans dépendance à un embedding.
    """
    if not message:
        return []
    text = _norm(message)
    scored: list[tuple[int, dict]] = []
    for entry in _load_corpus():
        score = sum(1 for kw in entry.get("keywords", []) if kw and _norm(kw) in text)
        if score > 0:
            scored.append((score, entry))
    scored.sort(key=lambda m: m[0], reverse=True)
    return [entry for _, entry in scored[:max_matches]]


def format_legal_context(matches: list[dict]) -> str:
    """Formate les références vérifiées pour injection dans le contexte du prompt."""
    if not matches:
        return ""
    lines = [
        "## Références légales VÉRIFIÉES (Légifrance, à utiliser telles quelles)",
        (
            "Les références ci-dessous ont été vérifiées sur sources officielles. Pour les "
            "sujets concernés, utilise UNIQUEMENT ces numéros d'article (ne les remplace pas "
            "par ta mémoire). Pour toute AUTRE référence, applique la règle "
            "« [à confirmer sur Légifrance] ». Une relecture humaine reste requise."
        ),
        "",
    ]
    for e in matches:
        lines.append(f"- **{e.get('reference', '')}** ({e.get('code', '')}) : {e.get('summary', '')}")
        if e.get("key_figures"):
            lines.append(f"  Chiffres clés : {e['key_figures']}")
        if e.get("source_url"):
            lines.append(f"  Source : {e['source_url']}")
    return "\n".join(lines)


def get_legal_context(message: str) -> str:
    """Helper combiné : lookup + format (chaîne vide si aucun sujet juridique détecté)."""
    return format_legal_context(lookup_legal(message))
