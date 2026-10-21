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
