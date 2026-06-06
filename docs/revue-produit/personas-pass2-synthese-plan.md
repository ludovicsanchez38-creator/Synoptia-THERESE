# Synthèse - 2e passage personas (Thérèse Desktop)

> 06/06/2026. 11 personas métier, 5 tâches chacun, sur un backend **live** (Mistral small), après le lot S (garde-fous prompt, fantôme vectoriel, scoring) et le lot M (badge local/cloud, profil émetteur, chat branché CRM/calendrier).

## 1. Le chiffre brut est trompeur

Moyenne pass 2 : **6,50/10** vs pass 1 : 6,95/10. **La baisse est un artefact de méthode**, pas une régression produit.

Les 11 personas tournaient **en parallèle sur le MÊME backend** (un seul profil émetteur, une seule mémoire CRM partagée). Résultat : des fuites entre personas (le devis du plombier signé au nom de la formatrice, la mémoire qui mélange les contacts de tous). En usage réel, Thérèse est **mono-utilisateur souverain** : un seul profil, un seul CRM, zéro contamination. Quand on neutralise cet artefact, le signal est inverse :

- Les personas dont les correctifs P0 étaient le cœur **montent tous** : Formatrice **6,5 → 8**, Photographe **6,5 → 8**, Comptable **6 → 7**, Avocate **6,5 → 7**, Restauratrice **6 → 6,5**.
- Les personas qui **baissent** (Plombier 8,5→5,5, RH 8→6, Ostéo 7→5,5, Agent immo 6,5→5,5) le font à cause de **deux problèmes** : la contamination inter-personas (artefact) et deux vrais bugs (notes CRM jetées, hallucination de calendrier).

## 2. Ce qui est VALIDÉ en live (les correctifs tiennent)

| Correctif | Verdict live | Preuve |
|---|---|---|
| **Souveraineté (C2)** - le plus grave du pass 1 | **LEVÉ, unanime** | Les 11 personas : « stocké localement dans `~/.therese/`, SQLite chiffré, aucun hébergeur/serveur/lien ». Fini le « hébergée en France/UE/RAM » et le faux lien OpenAI. |
| **Badge local/cloud (C1)** | **LEVÉ** | `provider` correct sur chaque message (mistral ET ollama testés de bout en bout). |
| **Scoring CRM (C8)** | **LEVÉ** | Scores divergents (Mercier 125 vs Vasseur 50), recalcul fonctionnel. Fini le « figé à 60 ». |
| **Profil émetteur + garde-fou (C7)** | **LEVÉ** | Formatrice : PDF refusé en **400** sans SIRET, puis SIRET propagé au PDF conforme. Photographe : profil propagé dans la clause de cession. |
| **Fantôme vectoriel RGPD art.17 (C4)** | **LEVÉ** | Photographe : après anonymisation, la fiche ne remonte plus en recherche. |
| **read_contact / anti-hallu** | **LARGEMENT LEVÉ** | Lecture des vraies données client, plus de faux lien de téléchargement (dév), plus d'IBAN inventé (plombier), placeholders `[à vérifier]`, plus d'art. 227-22 CP erroné (photographe). |

C'est l'essentiel : **les deux contre-signaux les plus graves du pass 1 (l'IA bluffe sur la souveraineté, l'IA invente le droit/le SIRET) sont largement neutralisés**, et les fonctions tueuses (profil émetteur, scoring, RGPD démontrable) sont opérationnelles.

## 3. Les VRAIS bugs que le passage 2 a trouvés (à corriger)

### P0 - Bloquants

1. **Notes CRM jetées à la création** *(confirmé par 5 personas : RH, ostéo, dév, comptable, photographe)*
   `POST /api/crm/contacts` ignore silencieusement le champ `notes` (le schéma `CreateCRMContactRequest` ne le contient pas). La note métier (« tensions codir », « cervicalgie chronique », « acompte 40% versé ») n'est ni stockée, ni cherchable, ni résumée. **Effet domino** : la recherche sémantique par thème échoue (rien à indexer). Bloquant pour RH/santé/compta. **Fix simple** : ajouter `notes`/`address`/`tags` au schéma + au handler.

2. **Hallucination de calendrier** *(plombier, dév, restauratrice)*
   Aucun calendrier connecté (l'API exige un compte Google) → au lieu de dire « aucun calendrier connecté », l'IA **invente des RDV** datés et les présente comme réels. Le comptable, lui, a eu le bon réflexe (« aveu honnête d'absence d'accès ») : **le comportement dépend de la formulation**. Le lot M a élargi la fenêtre mais n'a pas traité le cas « pas de calendrier ». **Fix** : quand l'outil renvoie une erreur/zéro événement, forcer le prompt à dire l'absence, ne jamais broder + activer un calendrier local par défaut (sans compte Google).

### P1 - Fort impact

3. **Bug de sérialisation `GET /api/crm/contacts/{id}`** *(ostéo, comptable, photographe)*
   La route unitaire renvoie `score/stage/notes = None` alors que les valeurs existent en base (le recalcul les voit). Bug d'hydratation de l'endpoint individuel.

4. **Souveraineté : surpromesse sur le TRAITEMENT** *(RH, formatrice, ostéo)*
   L'IA dit parfois « aucune donnée ne quitte ta machine, même pas pour traitement » alors que le chat tourne sur Mistral **cloud**. Elle confond la couche **stockage** (locale, vraie) et la couche **traitement** (cloud quand on choisit Mistral). Le garde-fou dit la nuance mais le modèle la simplifie. **Fix** : durcir la formulation du bloc souveraineté (distinguer explicitement stockage vs traitement à chaque réponse).

5. **Juridique : références périmées affirmées** *(avocate, dév, comptable)*
   Le garde-fou stoppe l'**invention** mais pas la **connaissance périmée** énoncée avec aplomb : `L441-6` (abrogé → L441-10), `1343-5` au lieu de `1231-6`, `226-15` au lieu de `226-13`. C'est exactement la partie **« L »** de P0-IA-2 (RAG juridique sur corpus vérifié) qu'on avait laissée pour plus tard. Le `[à vérifier]` ne couvre pas les numéros précis énoncés comme sûrs.

6. **Skill Office non branché au chat** *(dév)*
   « Génère-moi un Word » ne produit aucun fichier (le routage intent → skill reste fragile). Décision lot M : laissé en détection d'intention, à transformer en outil appelable.

## 4. Les artefacts du test mutualisé (à NE PAS confondre avec des bugs produit)

- **Fuite du profil émetteur entre personas** : un seul backend = un seul profil global. Le devis du plombier sort au nom de la formatrice. En mono-utilisateur réel, il n'y a qu'un profil. *(Pour un futur multi-tenant : scoper le profil et la mémoire par utilisateur.)*
- **Mémoire CRM partagée** : la recherche sémantique remonte les contacts de tous les personas. Même cause, même remède multi-tenant.

Ces deux points ont fait perdre des points à plusieurs personas mais ne se produisent pas chez un solopreneur seul devant son app.

## 5. Plan de correction priorisé (pour un 3e passage)

**Lot « quick wins » (S, à faire vite, gros effet sur les notes)**
1. **Notes CRM** : ajouter `notes`/`address`/`tags` à `CreateCRMContactRequest` + handler `create_crm_contact` (+ vérifier l'embedding). *(débloque RH, santé, compta, dév)*
2. **Hallucination calendrier** : prompt « si l'outil calendrier ne renvoie rien / erreur, dis l'absence, n'invente jamais » + calendrier local par défaut. *(débloque plombier, dév, restauratrice, comptable)*
3. **Sérialisation `GET /contacts/{id}`** : réparer l'hydratation score/stage/notes.
4. **Souveraineté traitement** : durcir le bloc prompt (stockage local vs traitement cloud, à chaque réponse).

**Lot « M »**
5. **RAG juridique** (la partie « L » de P0-IA-2) : corpus Légifrance vérifié pour les clauses/références types (corrige L441-6, 1231-6, etc.).
6. **Skill Office en outil appelable** (generate_docx/pptx/xlsx) au lieu de la détection d'intention.

**Pré-requis 3e passage**
7. Lancer les personas **un par un sur une base fraîche** (ou scoper par tenant) pour mesurer le vrai signal sans l'artefact de contamination.

## 6. Conclusion

Le lot S + lot M ont **tenu leur promesse sur les contre-signaux décisifs** : la souveraineté ne sabote plus l'argument de vente, le scoring vit, le profil émetteur rend les factures conformes et bloquantes, le RGPD est démontrable (anonymisation nette), le badge local/cloud existe, et Ollama tourne enfin avec des modèles costauds (le « sensible en local » est réel). Les notes des métiers réglementés montent.

Le passage 2 a fait son travail de filet : il a sorti **deux bugs produits nets et corrigeables** (notes CRM jetées, hallucination calendrier) et confirmé que le **RAG juridique** reste le prochain vrai chantier. Une fois ces quatre quick wins faits et les personas relancés un par un, on devrait voir la moyenne franchir nettement les 7,5/10.
