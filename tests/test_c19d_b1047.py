import ast
from pathlib import Path


def test_notifications_accentuees():
    arbre = ast.parse(Path('src/backend/app/services/notification_service.py').read_text())
    textes = [n.value for n in ast.walk(arbre) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    for attendu in ['Facture impayée', 'Relance échue', 'Tâche en retard', 'RDV demain à ']:
        assert any(attendu in texte for texte in textes)
    assert not any('impayee depuis' in t or 'prevue il y a' in t for t in textes)
