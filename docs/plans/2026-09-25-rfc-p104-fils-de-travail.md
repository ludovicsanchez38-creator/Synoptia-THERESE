# RFC P-104 : un « fil de travail » au-dessus du projet

Rédigé le 25/09/2026. Proposition acceptée par Ludo **en RFC seulement** : aucun code avant la validation de ce document.

## 1. Le besoin

Dr_logic-3D, testeur alpha, sur Discord (fil du 25/09, 03:35 à 04:29) :

- L'unité de son travail n'est pas toujours le projet. Il passe d'un sujet à l'autre dans la journée, et le projet n'est pour lui qu'une forme d'activité parmi d'autres.
- Un même besoin se découpe vite en **variantes** (des sous-projets), chacune avec ses propres échanges et sa propre documentation.
- Il veut **quantifier le temps passé** sur chaque sujet.
- Quand les conversations restent à plat, l'information finit noyée.

## 2. Ce qui existe déjà

Relevé du 25/09 dans le code (chemin et ligne dans l'annexe).

**Points d'appui :**

- `project_id` est déjà porté par les tâches, les documents, les livrables, les événements d'agenda et les conversations.
- Le couple `scope` / `scope_id` est générique et déjà filtré par les cloisons.
- La conversation dispose d'un sélecteur de projet (« Documents généraux », un projet, « Tous les projets »), servi par un résolveur de périmètre qui ferme en cas d'échec.
- Les travaux (`ProcessingTask`) portent un projet, une conversation, un début et une fin. Leur commentaire annonce déjà « le temps par projet ».
- Le planning PERT (P-039) estime des durées et un avancement.

**Manques :**

- Aucune mesure du temps réalisé, aucun minuteur.
- Aucune hiérarchie de projets, aucun embranchement de conversation, aucune version de document.
- Le tiroir des conversations regroupe par date, l'accueil ne regroupe rien par projet, et la frise des travaux n'affiche pas le projet.
- **Le mot « activité » est déjà pris** : la table `activities` et la frise CRM désignent l'historique d'un contact (appel, e-mail, rendez-vous). Réutiliser ce mot créerait une confusion durable.

## 3. Trois options

| | A. Nouvelle entité « fil de travail » | B. Projets hiérarchiques | C. Étiquettes transverses |
|---|---|---|---|
| Idée | Une table `fils`, reliée à tout (projets, conversations, documents, tâches), avec des variantes (fils enfants) et des sessions de temps | Un `parent_id` sur les projets : le fil devient un projet parent, les variantes des sous-projets | Une étiquette posée sur les conversations et les documents, avec des vues filtrées |
| Pour | Répond aux trois besoins sans dénaturer le projet | Réutilise tout l'existant | Très léger |
| Contre | Nouvelle table, export, import et purge à étendre | Reste enfermé dans le projet, ce que le testeur récuse | Pas de temps passé, pas de variantes, se dilue |
| Effort | Moyen à large | Moyen | Petit |

## 4. Recommandation : l'option A, en deux phases

### Phase 1 : le fil et son temps

- **Nom provisoire : « fil de travail ».** Autres candidats : « chantier », « sujet ». Il faut surtout éviter « activité » (voir la section 2).
- **Modèle** :
  - `fils` : nom, statut (ouvert, en pause, clos), `parent_id` sur un niveau pour les variantes, dates, périmètre (`scope`) ;
  - `liens_de_fil` : `fil_id`, `type_entite`, `id_entite`, relation plusieurs-à-plusieurs. Un fil traverse plusieurs projets, et une conversation globale peut y entrer.
  - `sessions_de_travail` : `fil_id`, début, fin, source (minuteur ou saisie).
- **Temps passé** : explicite en phase 1, avec un minuteur démarrer / arrêter dans l'en-tête et une correction à la main. **Jamais inféré** : une durée devinée à partir des messages ou des travaux serait une fausse mesure affichée comme vraie.
- **Interface** :
  - un sélecteur « Fil » à côté du sélecteur de projet de la conversation ;
  - un filtre par fil dans le tiroir des conversations et la liste des documents ;
  - une carte « Reprendre » à l'accueil (dernier fil ouvert, temps du jour) ;
  - la vue d'un fil : ses variantes, ses conversations, ses documents, ses tâches et son temps.
- **Données** : les nouvelles tables entrent dans l'export, l'import, la purge RGPD et la restauration dès la phase 1, pas après. Chaque ajout de table dans ce cycle a montré que ces portes s'oublient.

### Phase 2, après usage réel

- Suggestions de temps à partir des travaux et de l'agenda, toujours proposées à la validation.
- Comparaison entre l'estimation du planning (P-039) et le temps réel.
- Synthèse d'un fil par l'assistant.
- Hors périmètre : la continuité entre plusieurs machines (P-108), qui relève d'un chantier de sécurité à part.

## 5. Décisions attendues de Ludo

1. **Le nom** : « fil de travail », « chantier », « sujet », ou autre.
2. **Les variantes** : un seul niveau de fils enfants, ou une hiérarchie libre ? Recommandation : un niveau.
3. **Le temps** : minuteur manuel seulement en phase 1 ? Recommandation : oui.
4. **Le rattachement** : un fil peut-il regrouper plusieurs projets, et une même conversation appartenir à plusieurs fils ? Recommandation : plusieurs projets oui, une conversation dans un seul fil.
5. **La place à l'accueil** : la carte « Reprendre » remplace-t-elle un bloc existant ou s'ajoute-t-elle ?

## 6. Livraison proposée (après validation)

1. Design court et revue adverse du design.
2. Modèle, migration, export, import, purge et restauration (TDD).
3. API et cloison.
4. Sélecteur, tiroir et vue du fil.
5. Minuteur et carte « Reprendre ».
6. Recette sur les données de démonstration.

Chaque lot fait l'objet d'un commit, avec sabotage des tests et revue adverse du diff.

## 7. Risques

- **Doublon de concept avec le projet** : il faut écrire noir sur blanc, dans l'interface, la différence entre un projet (un engagement client, avec devis et livrables) et un fil (le travail en cours, qui peut en traverser plusieurs).
- **Minuteur oublié** : un minuteur qui tourne toute la nuit fausse tout. Prévoir un plafond et une alerte au-delà de quelques heures.
- **Surcharge** : un sélecteur de plus dans la conversation, alors que Ludo a déjà dit « trop d'interfaces » (27/08). Le sélecteur doit rester discret et optionnel.

## Annexe : appuis dans le code

- Tables et rattachements : `models/entities.py` : Project l.89 à 99, Task l.560 à 568, Conversation l.177 à 187, Document l.957 à 980, Deliverable l.883 à 888, Activity (CRM) l.855 à 869.
- Périmètre : `routers/chat.py` l.651 (résolveur), l.3711 (rattachement) ; `services/memory_tools.py` l.347 (création), l.370, l.445 et l.1349 (cloisons).
- Temps : `models/processing.py` l.67 à 77 ; `services/traitements.py` l.376 (purge à 30 jours) ; planning `models/entities.py` l.645 à 650.
- Interface : `components/chat/ConversationProjectPicker.tsx` l.166 à 180 ; tiroir `components/prototype/PrototypeConversationDrawer.tsx` l.71 à 78.
- Migrations : `models/database.py` l.253 (ad hoc), l.617 (tête Alembic), l.1109 (`create_all`).
