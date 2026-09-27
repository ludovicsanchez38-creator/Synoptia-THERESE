"""Règles communes pour les clés de préférences contenant des secrets."""

MOTIFS_DE_SECRET = (
    "api_key", "apikey", "secret", "token", "password", "passwd", "mot_de_passe",
)


def est_cle_secrete_de_preference(cle: str) -> bool:
    """Repère une clé sensible sans dépendre de sa catégorie ni de sa casse."""
    cle_minuscule = cle.lower()
    # Le terme « token » désigne ici un plafond de consommation, pas un jeton.
    if cle_minuscule == "token_limits":
        return False
    return any(motif in cle_minuscule for motif in MOTIFS_DE_SECRET)
