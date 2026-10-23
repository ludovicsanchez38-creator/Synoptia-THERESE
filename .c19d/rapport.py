"""Assemble le rapport à partir des preuves conservées, sans estimer de total."""
import json
import re
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parent.parent
entries = json.loads((root / '.c19d/journal.json').read_text())
fiche_texte = (root / '.c19d/fiches.json.txt').read_text()
decodeur = json.JSONDecoder()
fiches = {}
verdicts = {}
pos = 0
while True:
    debut = fiche_texte.find('\n{', pos)
    if debut < 0:
        break
    objet, fin = decodeur.raw_decode(fiche_texte[debut + 1:])
    (verdicts if 'verdict' in objet else fiches)[objet['id']] = objet
    pos = debut + 1 + fin

assert len(fiches) == 47 and len(verdicts) == 46

log = subprocess.check_output(['git','log','--oneline','f01582fa..HEAD'], cwd=root, text=True)

def preuve(nom):
    return f'[sortie {nom}](.c19d/preuves/{nom}.log)'

def synthese(nom):
    fichier = root / '.c19d/preuves' / (nom + '.log')
    if not fichier.exists():
        return 'En attente.'
    texte = re.sub(r'\x1b\[[0-9;]*m','',fichier.read_text())
    lignes = [l.strip() for l in texte.splitlines() if
              re.match(r'(Test Files|Tests\s|Errors\s|\d+ passed|\d+ failed|All checks passed!|Found \d+|✖ |Code de sortie)',l.strip())]
    return ' ; '.join(lignes) if lignes else 'Pas de diagnostic imprimé ; résultat à confirmer dans la sortie de commande.'

intro = '''# COCO — C19-D, interface, UX et accessibilité

Branche `boucle/c12-visuel`, base `f01582fa` (0.79.0). Rapport préparé dans le seul dossier autorisé à l’écriture. Le chemin demandé sous `/home/synoptia/staging/therese-c19-campagne-2026-10-23/` est extérieur : aucune copie n’y a été écrite.

Les 47 fiches complètes et les 46 entrées de reproduction correspondantes ont été lues, ainsi que toutes les captures citées pour ce lot. B-1112 n’a pas d’entrée autonome dans `rapport.json` : sa reproduction est la note de B-1075. Le relevé de départ est conservé dans [.c19d/fiches.json.txt](.c19d/fiches.json.txt).

Les corrections sont couvertes par un test rouge conservé avant modification, puis un test vert. Les logs intermédiaires ratés restent archivés ; les liens de chaque défaut pointent vers les preuves retenues. Certaines exécutions groupées contiennent aussi des tests historiques en échec : les tests du défaut, identifiés par son numéro, sont ceux à comparer. Les logs ciblés et les contrôles finaux permettent de distinguer ces cas.

Aucune dépendance installée, aucun fournisseur d’IA appelé, aucune pile ou port de recette démarré. Les tests remplacent les API et les modèles. Les jeux pytest et les fichiers temporaires sont dirigés vers `.c19d/tmp/`. Le petit plugin pytest local laisse imprimer le résumé avant la sortie forcée qu’effectuait trop tôt le `conftest.py` existant ; le fichier partagé n’est pas modifié.

## Limites et décisions laissées ouvertes

- **B-1068** : les commandes ne sont plus imbriquées. La poignée, l’ouverture et la suppression restent trois commandes accessibles. Imposer un seul arrêt de tabulation demanderait une convention de navigation entre elles ; aucune navigation nouvelle n’a été choisie sans décision produit.
- **B-1077** : le PDF traduit `overdue` en « En retard ». La validité métier d’un avoir en retard reste ouverte ; la route et les statuts permis ne sont pas changés.
- **Mesures visuelles** : jsdom ne mesure ni les largeurs ni les pixels. Les contraintes de classes/structure sont testées pour B-1052, B-1053, B-1072, B-1079, B-1084 et B-1093 ; les mesures Chrome indiquées ci-dessous restent à faire. Les noms natifs de Fichiers exigent aussi une vérification Tauri.
- **B-1102** : la fonction réelle du relevé est exécutée sous Vitest avec des contrôles DOM et des snapshots accessibles doubles. Le test Chromium supplémentaire n’a pas pu démarrer car `@playwright/test` n’est pas installé dans les dépendances accessibles ici ; rien n’a été installé. La confirmation du nom calculé dans Chrome reste demandée.
- Constats annexes des notes, hors des 47 références : la hauteur de « Tout ignorer » (B-1061), les espaces des milliers des montants du prototype (B-1082) et le sort métier des avoirs en retard sont signalés, sans correction supplémentaire inventée.
- B-1056 : la reproduction réfutait l’absence d’Échap ; le défaut corrigé concerne le focus et le nom de la croix. B-1093 : le focus global et les paragraphes étaient déjà lisibles ; seuls les écarts mesurés du bouton sont corrigés. B-1102 : le SVG titré était déjà nommé ; la correction couvre notamment l’image avec `alt`.

Le regroupement final des compléments dans leurs commits de défaut a conservé exactement le même arbre Git, après les contrôles : [preuve](.c19d/preuves/regroupement-commits.log).

## Défauts
'''
sections = [intro]
for entree in entries:
    for identifiant in entree['ids'].split():
        fiche = fiches[identifiant]
        verdict = verdicts.get(identifiant)
        sections.append(f"\n### {identifiant}\n\n")
        sections.append(f"- Cause : {entree['cause']}\n")
        if verdict:
            sections.append(f"- Reproduction : {verdict['verdict']}. Attendu : {verdict['attendu']}\n")
        else:
            sections.append('- Reproduction : note de B-1075 et observation de la fiche B-1112.\n')
        sections.append(f"- Correctif : {entree['correction']}\n")
        sections.append(f"- Rouge : {preuve(entree['rouge'])}. Vert : {preuve(entree['vert'])}.\n")
        sections.append(f"- Commit : `{entree['commit']}` ({entree['ids']}).\n")
        sections.append(f"- À mesurer/rejouer dans Chrome : {entree['chrome']}\n")

sections.append('''
## Rejeux inventés après correction

Les entrées exactes figurent dans les tests paramétrés. Les listes ci-dessous identifient les dix scénarios de chaque changement de logique ; les valeurs bancaires et jetons sont des exemples de test, jamais des identifiants de l’utilisatrice.

| Correctif | Dix entrées/scénarios après correction | Preuve |
|---|---|---|
| B-1088 | « Secrétariat général : appeler Léa jeudi » ; « Je vous prie de trouver le devis joint » ; « Paul est parti en congés lundi » ; « Diagnostic de performance énergétique du local » ; « Traitement de la commande 678 » ; IBAN belge ; IBAN néerlandais ; mot de passe factice ; `api_key` factice ; `refresh_token` factice | `test_rejeu_apres_correctif` dans `tests/test_c19d_b1088_securite_memoire.py` |
| B-1075 et B-1112 | Appeler Luc ; Préparer la visite ; Lire le devis ; Commander les tuiles ; Réserver la salle ; Relancer Léa ; Vérifier les plans ; Revoir le budget ; Ranger le dossier ; Confirmer la livraison. Pour chacune : Entrée ouvre, poignée saisit, Échap annule sans quitter. | `TaskKanban.c19d.test.tsx` |
| B-1064 | Erreur réseau ; Réponse 500 ; Réponse 502 ; Document supprimé ; Accès refusé ; Délai dépassé ; Service indisponible ; Réponse illisible ; Connexion interrompue ; Lecture interrompue. Pour chacune : message, absence de chargement permanent et reprise réussie. | `DocumentWorkspace.c19d.test.tsx` |
| B-1056 | Résumer ce courrier ; Relire le devis ; Préparer un rendez-vous ; Expliquer la facture ; Classer cette note ; Lister les travaux ; Traduire le paragraphe ; Comparer les offres ; Rédiger une relance ; Préparer la visite. Focus reçu et Échap ferme la seule commande. | `PanelContainer.b1726.test.tsx` |
| B-1068 | Terrasse ; Charpente ; Cuisine ; Bureau ; Jardin ; Façade ; Salon ; Garage ; Atelier ; Grenier. Ouverture distincte de la poignée pour chaque nom. | `ProjectsKanban.test.tsx` |
| B-1046 et B-1097 | `grok-4.21-0412-reasoning` ; `grok-4.21-0412-non-reasoning` ; `google/gemini-4.2-flash` ; `meta-llama/llama-5-scout` ; `deepseek-v5-chat` ; `ministral-12b-2610` ; `claude-sonnet-5-7-20261022` ; `openai/gpt-7-mini` ; `qwen-4-3b` ; `minimax-m3` | `test_c19d_b1046_1097.py` |
| B-1077 | OVERDUE/avoir ; overdue entouré d’espaces/avoir ; draft/avoir ; sent/avoir ; paid/avoir ; cancelled/avoir ; overdue/facture ; sent/facture ; sent/devis ; accepted/devis | `test_c19d_b1077.py` |
| B-1081 et B-1083 | sent/facture ; paid/facture ; cancelled/facture ; sent/devis ; accepted/devis ; refused/devis ; expired/devis ; sent/avoir ; paid/avoir ; draft/facture | `InvoiceConversationCard.test.tsx` |
| B-1082 | TVA 0 ; 2,1 ; 5,5 ; 10 ; 20 ; 4,5 ; 7,7 ; 8,1 ; 12,25 ; 19,6 % | `InvoiceConversationCard.test.tsx` |
| B-1086 | 0 ; 100 ; 999 ; 1 000 ; 1 550 ; 12 000 ; 28 345 ; 100 000 ; 1 234 567 ; 9 999 999 jetons | `LimitsTab.cycle6.test.tsx` |
| B-1091 | Dix montages et cycles ouvrir/replier, sans identifiant absent ; libellés premier à dixième dans le test. | `B-1091.test.tsx` |
| B-1094 | Projets terrasse ; grange ; atelier ; toiture ; cuisine ; salon ; jardin ; bureau ; garage ; cave. Une erreur de lecture ne devient jamais un vide. | `ProjectDeliverablesSection.p153.test.tsx` |
| B-1102 | Ouvrir Léa ; Fermer « Projet » ; Revenir à l’accueil ; Sauver le devis ; Lire une note ; Copier un lien ; nom avec guillemets ; nom avec barre oblique inverse ; Accès à l’Agenda ; nom sur deux lignes. Le snapshot prime sur l’`alt` différent. | `B-1102.test.js` |

Les autres corrections changent un texte constant, un jeton, une classe ou une association ARIA et conservent les règles et les gestes existants.

Le test national ajouté après le premier correctif a révélé un cas italien encore manquant : [rouge](.c19d/preuves/B-1088-integration-et-pays.log). Les groupes sont désormais décrits explicitement et les dix pays passent : [vert](.c19d/preuves/B-1088-integration-et-pays-vert.log).

Deux gardes supplémentaires ont ensuite signalé des régressions du premier ajustement : quatre identifiants/exception (`smtpToken`, `clientSecret`, `SMTPTOKEN`, `token_limits`) échouaient ([rouge identifiants](.c19d/preuves/B-1088-identifiants-rouge.log)), puis la ponctuation des coordonnées n’était pas entièrement préservée ([rouge séparateurs](.c19d/preuves/B-1088-separateurs-rouge.log)). Les identifiants et les séparateurs sont corrigés ; les preuves initiales ne sont pas remplacées. Deux nouveaux rejeux de dix entrées figurent dans `test_rejeu_identifiants_apres_ajustement` et `test_rejeu_separateurs_apres_correctif` : cinq secrets ou IBAN factices refusés et cinq libellés professionnels admis par série. Le [contrôle de sécurité final](.c19d/preuves/B-1088-securite-finale-vert.log) inclut les tests de protection historiques.

Les assertions B-1065 et B-1067 ont été affinées pour viser le nom calculé et le fragment affiché, puis rejouées sur la base : [rouge de confirmation](.c19d/preuves/contrats-affines-base-rouge.log). Les contraintes de rendu restent à mesurer dans Chrome.

B-1088 reçoit en plus sept créations réelles de fiches via le service et les dix formats nationaux déjà filtrés, dont une représentation Unicode. Le corpus historique de protection est rejoué : mots de passe, clés, jetons, cartes bancaires et catégories sensibles restent refusés. Le refus nomme une catégorie sans réafficher sa valeur.

''')
sections.append('## Contrôles\n\n')
for nom in ['moteur-livraison-definitive','moteur-final-livre','moteur-final-definitif','moteur-final','moteur-routers-import-notifications','B-1088-integration-et-pays-vert','B-1088-securite-finale-vert','rejeux-interface','rejeux-commandes-et-instrument','contrats-et-clavier-vert','validation-board-libelles','splash-vert','factures-gardes-vert','navigation-et-poignees-vert','frontend-c19d-final','gardes-du-controle-complet-vert','tsc-final-definitif','eslint-final-definitif','ruff-livraison-definitive','vitest-complet','vitest-complet-final','dates-pool-processus','dates-pool-threads']:
    sections.append(f'- {preuve(nom)} : {synthese(nom)}\n')
sections.append('''
Les sorties finales ne sont déclarées réussies que lorsque leur code de sortie est connu. Le premier passage complet a terminé **881 fichiers** : **3 651 tests réussis et 14 échecs**. Onze échecs venaient des anciennes attentes de libellé, de nom ou de position. Ces gardes sont mises à jour et leur reprise passe : [38 tests verts](.c19d/preuves/gardes-du-controle-complet-vert.log).

Les trois autres résultats varient suivant le contexte : choix Souverain du Board, assistant de commande de l’accueil et retour de l’assistant e-mail. Une archive intégrale de f01582fa a passé les six tests correspondants lors d’un premier passage, puis a échoué sur Board et accueil lors d’un second, sans correctifs du lot ([premier passage](.c19d/preuves/base-trois-tests-hors-lot.log), [rejeu de la base](.c19d/preuves/base-trois-tests-hors-lot-rejeu.log)). L’assistant e-mail passe aussi isolément dans l’arbre corrigé ([preuve](.c19d/preuves/email-hors-lot-isole.log)). Ces observations signalent une instabilité de test ; elles ne suffisent pas à en attribuer la cause. Le passage complet reste distinct des reprises ciblées et n’est pas déclaré vert par déduction.

Le passage complet final avec quatre threads a terminé **881 fichiers** : **3 673 tests réussis et 3 échecs** (3 676 tests). Le test e-mail B-329 échoue encore dans ce passage. Les deux autres échecs sont dans `civilDate.joursCouverts.test.ts`, fichier et code d’agenda inchangés : le changement de fuseau durant le test échoue avec des threads. Le même fichier exécuté seul reproduit exactement **2 échecs et 4 réussites** avec des threads, puis **6 réussites** en processus séparés, mode par défaut du projet ([threads](.c19d/preuves/dates-pool-threads.log), [processus](.c19d/preuves/dates-pool-processus.log)). Le contrôle complet final est donc **rouge** ; les reprises isolées ne le remplacent pas.

## Historique demandé

Commande : `git log --oneline f01582fa..HEAD`, capturée après les 39 commits de correctifs et avant le commit de remise du rapport.

```text
'''+log+'```\n')
(root / 'coco-c19d-rapport.md').write_text(''.join(sections))
print('Rapport écrit dans le dossier de travail, avec les résultats de contrôles conservés.')
