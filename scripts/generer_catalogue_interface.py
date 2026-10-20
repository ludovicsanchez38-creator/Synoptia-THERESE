"""Régénérer le repli frontend après modification du catalogue du moteur."""
import json
from pathlib import Path

from app.services.modeles_catalogue import catalogue_pour_interface

chemin = Path(__file__).resolve().parents[1] / 'src/frontend/src/lib/modelesCatalogue.generated.json'
chemin.write_text(json.dumps(catalogue_pour_interface(), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
