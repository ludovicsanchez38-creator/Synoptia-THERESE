"""Mesurer les schémas et descriptions réellement offerts, sans modèle."""
import json
from pathlib import Path

from app.services.memory_tools import MEMORY_TOOLS
from app.services.ollama_budget import estimer_jetons
from app.services.tool_capabilities import capacites_outils
from app.services.tool_selection import groupe_outil
from app.services.web_search import web_tools
from app.services.workspace_tools import WORKSPACE_TOOLS

groupes = {}
for outil in [*web_tools(), *WORKSPACE_TOOLS, *MEMORY_TOOLS]:
 groupes.setdefault(groupe_outil(outil), []).append(outil)
resultat = {}
for groupe, outils in groupes.items():
 schemas = json.dumps(outils, ensure_ascii=False, separators=(',', ':'))
 description = capacites_outils([t['function']['name'] for t in outils])
 resultat[groupe] = {'outils': [t['function']['name'] for t in outils],
  'octets_schemas': len(schemas.encode()), 'octets_capacites': len(description.encode()),
  'jetons_estimes_schemas': estimer_jetons(schemas), 'jetons_estimes_capacites': estimer_jetons(description)}
chemin = Path(__file__).resolve().parents[1] / '.recette-r4/logs/groupes-outils.json'
chemin.write_text(json.dumps(resultat, ensure_ascii=False, indent=2))
print(json.dumps(resultat, ensure_ascii=False, indent=2))
