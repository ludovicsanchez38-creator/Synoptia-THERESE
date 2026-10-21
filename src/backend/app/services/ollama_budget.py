"""Une seule fenêtre locale pour le bornage R2 et le transport Ollama."""
import os
from typing import Any


def plafond_memoire() -> int:
    """BUG-052 conservé sous 8 Gio ; plafond prudent de 16k sur les autres postes."""
    try:
        ram = os.sysconf('SC_PHYS_PAGES') * os.sysconf('SC_PAGE_SIZE')
    except (AttributeError, ValueError, OSError):
        return 8192
    return 8192 if ram < 8 * 1024**3 else 16384


def fenetre_ollama(config: Any) -> int:
    # Ne jamais augmenter une petite fenêtre annoncée par le modèle.
    fenetre = config.context_window
    return min(fenetre, plafond_memoire()) if isinstance(fenetre, int) else 0


def estimer_jetons(texte: str) -> int:
    """Estimation locale explicite, jamais des octets comparés à des jetons.

    Le banc Qwen français/JSON mesure 3,8 à 4 octets/jeton. 3,5 garde
    une marge de 8 à 14 %, plus les enveloppes du chat. Les caractères hors
    alphabet latin gardent leur coût UTF-8 pessimiste. Aucun téléchargement.
    Ce n'est pas un tokenizer exact : les compteurs du banc restent l'oracle.
    """
    latin = sum(len(c.encode('utf-8')) for c in texte if ord(c) < 0x250)
    autres = sum(len(c.encode('utf-8')) for c in texte if ord(c) >= 0x250)
    return (latin * 2 + 6) // 7 + autres
