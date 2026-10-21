"""Comparer les tailles capturées et vérifier les contrats des outils raccourcis."""
import ast
import json
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[1]
logs = root / '.recette-r6/logs'
contrats = {}
for fichier, noms in {
    'web_search.py': ['WEB_SEARCH_TOOL'],
    'workspace_tools.py': ['GENERATE_DOCUMENT_TOOL', 'SEARCH_INVOICES_TOOL', 'INVOICE_TOTALS_TOOL'],
}.items():
    chemin = 'src/backend/app/services/' + fichier
    avant = subprocess.check_output(['git', 'show', f'a1a1f3a3:{chemin}'], cwd=root, text=True)
    apres = (root / chemin).read_text()
    def lire(texte):
        outils = {}
        for noeud in ast.parse(texte).body:
            nom = (noeud.targets[0].id if isinstance(noeud, ast.Assign) and isinstance(noeud.targets[0], ast.Name)
                   else noeud.target.id if isinstance(noeud, ast.AnnAssign) and isinstance(noeud.target, ast.Name) else None)
            if nom in noms:
                outil = ast.literal_eval(noeud.value)
                outil['function'].pop('description')
                outils[nom] = outil
        return outils
    assert lire(avant) == lire(apres), f'Contrat changé : {fichier}'
    contrats[fichier] = noms
bilan = {}
for fichier in sorted((logs / 'charge-avant-premiere').glob('*.json')):
    avant = json.loads(fichier.read_text())
    apres = json.loads((logs / 'charge' / fichier.name).read_text())
    bilan[avant['fournisseur']] = {'avant': avant, 'apres': apres}
assert len(bilan) == 14
resultat = {'methode': 'HTTP MockTransport, vrais routeur/service/adaptateurs, Bonjour sans profil ni historique ; JSON compact ; estimation ceil(caractères/4), pas une mesure du tokenizer fournisseur',
    'contrats_identiques': contrats, 'fournisseurs': bilan}
(logs / 'charge-comparaison.json').write_text(json.dumps(resultat, ensure_ascii=False, indent=2))
for nom, valeurs in bilan.items():
    print(nom, 'système', valeurs['avant']['systeme']['jetons_estimes'], '→', valeurs['apres']['systeme']['jetons_estimes'],
          '; outils', valeurs['avant']['outils']['jetons_estimes'], '→', valeurs['apres']['outils']['jetons_estimes'],
          '; requête', valeurs['avant']['requete']['jetons_estimes'], '→', valeurs['apres']['requete']['jetons_estimes'])
print('Noms, paramètres, obligations et types des quatre outils : identiques à a1a1f3a3.')
