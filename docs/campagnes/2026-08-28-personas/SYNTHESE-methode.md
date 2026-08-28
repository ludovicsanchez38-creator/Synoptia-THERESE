# Campagne dix personas — THÉRÈSE 0.53.0-alpha, 28/08/2026

## Ce qui a été fait

Dix personas métier écrits à partir de la cible réelle de Synoptïa, chacun avec
son métier, son niveau technique, ses lignes rouges et six à sept tâches
concrètes de bout en bout. Grok les a joués **un par un**, chacun sur une
instance neuve.

| # | Persona | Ce qu'il vient chercher |
|---|---|---|
| 01 | Dr Hélène Vasseur, médecin généraliste | Six minutes entre deux patients. Secret médical = ligne rouge |
| 02 | Sébastien Roux, plombier-chauffagiste | Un devis le soir à la table de la cuisine, des impayés à relancer |
| 03 | Camille Ferrand, écrivaine | De l'intendance, pas un nègre. Hostile à l'IA qui écrit |
| 04 | Me Antoine Béranger, avocat | Des délais, des dossiers étanches, le secret professionnel |
| 05 | Claire Dumontier, magistrate | Méfiance de principe. Traque la surpromesse |
| 06 | Yann Le Guen, formateur indépendant | Qualiopi, et l'œil de celui qui devra l'expliquer à un débutant |
| 07 | Nadia Belkacem, dirigeante d'organisme de formation | « Qu'est-ce que ça remplace, qu'est-ce que je ressaisis deux fois ? » |
| 08 | Philippe Marchand, responsable administratif, 57 ans | Ne clique pas sur un bouton dont il ne comprend pas le nom |
| 09 | Julien Ferry, boulanger | Trois minutes, depuis un téléphone, deux doigts |
| 10 | Sylvie Ranc, directrice d'association | Des adhérents, pas des clients. Zéro budget logiciel |

## Le harnais

Une campagne précédente (14/06) avait été cassée par un persona zélé : appel à
`/api/shutdown`, puis relance manuelle du serveur **sans** `THERESE_DATA_DIR` —
écriture dans la vraie base. Les garde-fous ont donc été rendus **mécaniques**,
pas seulement écrits dans le protocole :

- **Port 17931**, ni celui de l'app packagée (17293), ni celui de la passe UI.
  Un persona qui frappe le mauvais port écrirait dans les vraies données.
- **Data-dir neuf par persona**, effacé et recréé entre chacun. Chacun vit donc
  un premier lancement — la surface que l'on cherche justement à observer.
- **Un superviseur possède le cycle de vie du serveur.** `/api/shutdown` est
  toujours non protégé en 0.53 : un appel parasite ne casse pas la campagne et
  personne n'a de raison de relancer à la main.
- **Modèle local Ollama `qwen3:8b`**, configuré par l'orchestrateur à chaque
  démarrage, jamais par le persona. Aucune clé d'API n'atteint un agent testeur.
- **Function calling vérifié avant de lancer** : un smoke-test a créé un contact
  réel. Sans ça, on découvre au persona 3 que le chemin outils est cassé.
- **Intégrité de la base réelle contrôlée** avant, pendant et après.

### Deux incidents de harnais, dits comme tels

1. **Le backend est mort pendant le persona 03.** Aucune trace d'erreur, aucun
   appel `/api/shutdown` (la route journalise). Cause probable : la mémoire —
   Ollama occupait 36 % des 16 Go de la machine, mémoire libre à 18 %. **C'est
   ma campagne, pas le produit.** En revanche, le 401 muet qui a suivi est, lui,
   un vrai défaut (voir la fiche O3).
2. **Le backend jetable écrit ses journaux dans la vraie arborescence.** Découvert
   par le contrôle d'intégrité. Ce n'est pas un incident de harnais mais un
   défaut produit (fiche O1) : `THERESE_DATA_DIR` n'est honoré que par une
   partie des chemins.

**La base réelle est intacte** : 932 fichiers avant, 932 après, aucun modifié.

## La contre-expertise

Les findings personas ne sont pas pris pour argent comptant. Deux passes :

1. J'ai vérifié chaque finding dans le code.
2. **Soso (Codex) a été lancé pour me réfuter.** Verdict : « Un seul finding
   tient tel quel. Le reste mélange absolus faux, causes ratées et gravités
   gonflées. »

Il avait raison sur l'essentiel. Trois de mes affirmations étaient fausses, une
gravité sur deux était gonflée, et **il a trouvé un défaut que ni les personas
ni moi n'avions vu** (l'envoi de facture répond 501 en toutes circonstances).
Le détail des requalifications est dans `constats-orchestrateur/verifications.md`.

Le retournement le plus important porte sur le chiffrement : j'avais classé
l'incident en « hallucination du modèle local ». Soso est allé lire le prompt
système, qui **ordonne** au modèle de dire que la base n'est pas chiffrée — alors
qu'elle l'est depuis US-014. Et un test verrouille la consigne.

## Ce que cette méthode ne peut pas voir

Un agent ne clique pas. La campagne a couvert l'API réelle et la lecture du code
de l'interface, pas les gestes. Échappent structurellement (liste établie par la
contre-expertise) :

- les actions rendues invisibles hors survol, qui ne reviennent pas au focus
  clavier ;
- l'ordre de tabulation, les annonces des lecteurs d'écran, les panneaux
  masqués, les débordements, le responsive réel ;
- les dialogues natifs Tauri, l'ouverture des PDF, les permissions de fichiers,
  le sidecar dans l'application packagée ;
- le rendu visuel effectif des PDF : polices, césures, pagination ;
- les courses entre l'état React, `localStorage` et le backend après une
  navigation, une fermeture ou un flux interrompu.

C'est la raison de la passe UI au navigateur qui suit cette campagne.
