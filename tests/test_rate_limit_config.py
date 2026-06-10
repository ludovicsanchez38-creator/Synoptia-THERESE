"""US-006 : le rate limiting doit être réellement appliqué.

Le Limiter slowapi était instancié sans `default_limits` et aucune route n'était
décorée : le middleware ne limitait rien, alors que le log annonçait
« rate limiting active ». On vérifie que des limites par défaut sont configurées.
"""
from app.main import app


def test_limiter_a_des_limites_par_defaut():
    limiter = getattr(app.state, "limiter", None)
    assert limiter is not None, "slowapi Limiter absent de app.state"
    # slowapi expose les limites globales via _default_limits
    default_limits = getattr(limiter, "_default_limits", [])
    assert len(default_limits) > 0, (
        "Le Limiter n'a aucune limite par défaut : le rate limiting est inerte."
    )
