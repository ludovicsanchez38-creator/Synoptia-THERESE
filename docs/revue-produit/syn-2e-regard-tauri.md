# 2e regard Syn — navigation refonte (environnement Tauri réel)

**Branche** : `chantier-revue-produit` · **Pour Syn** : ce que Claude ne peut PAS valider en navigateur (le mode dev navigateur n'a pas le runtime Tauri). Concentre-toi sur le réel.

## Contexte
Claude a validé en navigateur (DOM + captures) : pastille, Échap unifié, ⌘K (registre), vue Indexation, `window.__therese.runAction`. Tout vert. Mais 2 choses nécessitent le **vrai Tauri** + un 2e regard indépendant.

## À valider en priorité (Tauri uniquement)

### 1. Vue Indexation des fichiers (le point aveugle navigateur)
L'onglet « Fichiers » a quitté la Mémoire pour devenir une **vue dédiée**. En navigateur, `FileBrowser` affiche « Impossible de charger le répertoire personnel » (normal : pas de `@tauri-apps/plugin-fs` hors app). **Dans Thérèse réelle, ça doit marcher.**
- ⌘K → taper « indexation » → « Indexation des fichiers » → Entrée.
- La vue doit **lister ton répertoire personnel** (pas d'erreur), permettre de naviguer dans les dossiers, et **indexer un fichier** (sélection → indexation RAG).
- KO si : erreur de chargement, navigation cassée, indexation qui ne prend pas.

### 2. Mémoire : plus d'onglet Fichiers, mais tout le reste intact
La Mémoire ne contient plus que les **Contacts** (arbitrage A/B : on garde la Mémoire, on sort juste les Fichiers).
- Ouvre la Mémoire (⌘M ou icône) : il ne doit y avoir **aucun onglet Contacts/Fichiers**, juste la liste de contacts + recherche + pills de scope (Tout/Global/Projet/Conv.).
- **RGPD intact** : sur un contact, le menu RGPD (Export Art.20, Renouveler consentement, Anonymiser Art.17) doit toujours marcher.
- **Recherche intacte** : taper un mot des NOTES d'un contact (pas son nom) doit le remonter (moitié sémantique, réparée hier).
- **Import/Export VCF** toujours présents.

## À reconfirmer (2e regard, tu l'avais fait pour L6/L7)
- **Pastille** : crée un contact via une conversation (extraction Thérèse → « Sauvegarder ») → « N contacts liés à cette conversation » apparaît au-dessus de l'input → clic → ouvre la Mémoire.
- **Échap** : depuis CRM, Email, Mémoire, Indexation → Échap revient au chat. Depuis ⌘K ouvert → Échap ferme la palette (pas de retour de vue parasite).
- **⌘K bas niveau** : dans la console devtools, `window.__therese.runAction('crm.open')` doit ouvrir le CRM sans clic. `window.__therese.getActions().length` ≈ 20.

## Garde-fou
- Confirme que les contacts **sans `source`** (créés hors pipeline) restent visibles en **Mémoire** mais pas en **CRM** (c'est voulu : axes `scope` ≠ `source`). C'est exactement ce qui aurait cassé si on avait fusionné Contacts→CRM (arbitrage).

## Rendu
Poste ton verdict dans le hub (OK / KO par point), comme ton 2e regard L6/L7. Si KO sur l'Indexation Tauri, c'est le point le plus important (Claude ne pouvait pas le voir).
