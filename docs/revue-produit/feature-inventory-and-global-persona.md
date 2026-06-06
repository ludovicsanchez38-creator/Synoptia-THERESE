# Inventaire des fonctionnalités Thérèse + persona de test global

> Pré-release 0.20.0. Inventaire exhaustif (issu des routers) + un persona unique dont le parcours exerce l'ensemble.

## 1. Inventaire des fonctionnalités (par zone)

| # | Zone | Endpoints clés | Ce qu'on teste |
|---|---|---|---|
| 1 | **Chat multi-LLM** | `POST /api/chat/send` (stream true/false), `/conversations`, `/deep-research` | Réponse, badge provider (local/cloud), historique, outils (read_contact, generate_document, calendrier, email, web_search) |
| 2 | **Mémoire / recherche** | `POST /api/memory/search`, `/contacts`, `/projects` | Recherche sémantique + hybride, contacts/projets, notes indexées |
| 3 | **CRM** | `/api/crm/contacts`, `/contacts/{id}` (GET), `/recalculate-score`, `/pipeline/stats`, `/activities` | Création (notes persistées), scoring dynamique, pipeline, activités |
| 4 | **Facturation** | `/api/invoices` (devis/facture/avoir), `/{id}/pdf`, `/billing/profile-status`, `/mark-paid`, `/convert` | Garde-fou émetteur (400 sans SIRET), PDF conforme, devises (dont CAD), conversion devis→facture |
| 5 | **Profil émetteur** | `/api/config/profile` | SIRET/NDA/code APE stockés, propagés au PDF et au chat |
| 6 | **Email** | `/api/email/auth/*`, `/messages`, `/messages/draft`, signature | Setup IMAP, lecture/brouillon, signature HTML par compte |
| 7 | **Calendrier** | `/api/calendar/events`, `/quick-add`, CalDAV, import/export ICS | Événements, anti-hallu (pas de compte → dit l'absence) |
| 8 | **Board de décision IA** | `/api/board/advisors`, `/deliberate`, `/decisions` | 5 conseillers, délibération |
| 9 | **Génération d'images** | `/api/images/generate`, `/generate-with-reference`, `/list` | Génération (gpt-image), référence |
| 10 | **Transcription vocale** | `/api/voice/transcribe` | Audio → texte |
| 11 | **Skills Office** | `/api/skills/list`, `/execute/{id}`, `/download/{id}` | DOCX/PPTX/XLSX, via outil chat `generate_document` |
| 12 | **MCP** | `/api/mcp/servers`, `/tools`, `/presets` | Serveurs MCP, presets, install |
| 13 | **RGPD** | `/api/rgpd/export`, `/anonymize`, `/renew-consent`, `/stats`, `/infer` | Export Art.20, anonymisation Art.17 (fantôme vectoriel purgé) |
| 14 | **Config / LLM** | `/api/config/llm`, `/api-key`, `/working-directory`, `/therese-md`, `/onboarding` | Choix provider/modèle, clés, dossier de travail |
| 15 | **Tasks** | `/api/tasks` (CRUD + complete) | Tâches, complétion |
| 16 | **Notifications** | `/api/notifications` | Liste, compteur, marquage lu |
| 17 | **Calculateurs** | `/api/calculators/roi`, `/ice`, `/rice`, `/npv`, `/break-even` | Calculs de décision |
| 18 | **Escalation / coûts** | `/api/escalation/estimate-cost`, `/limits`, `/usage/*` | Estimation coût, limites, conso |
| 19 | **Personnalisation** | `/api/personalisation/templates`, `/llm-behavior`, `/features` | Templates, comportement LLM, feature flags |
| 20 | **Fichiers / indexation** | `/api/files/index`, `/upload`, `/{id}/content` | Indexation pour RAG |
| 21 | **Agents dev** | `/api/agents/*` | (hors périmètre persona métier : feature dev/autonome) |
| 22 | **Dashboard** | `/api/dashboard/today` | Vue du jour |
| 23 | **Follow-ups** | `/api/follow_ups/due` | Relances email programmées |
| 24 | **RAG juridique** | (injection contexte) | Références vérifiées (L441-10, 293 B...), [à confirmer] sur le reste |
| 25 | **Souveraineté** | (prompt) | Stockage local vs traitement cloud, pas de bluff |

## 2. Le persona global : « Claire Fontaine », consultante-formatrice solo (Manosque)

Activité variée qui touche tout : conseil + formation (OF) + un peu de création visuelle. Profil émetteur réel à renseigner. Son parcours de test (un fil) :

1. **Onboarding / profil** : renseigne son profil émetteur (nom, SIRET, NDA d'OF, adresse), vérifie `billing/profile-status`.
2. **Config LLM / badge** : envoie un message, vérifie le badge provider ; bascule Ollama puis Mistral.
3. **Souveraineté** : « où sont mes données, même pour le traitement ? ».
4. **CRM** : crée 2 clients avec notes (un chaud, un froid), vérifie les scores divergents + notes persistées + GET fiche ; pipeline stats.
5. **Mémoire/recherche** : recherche par thème (note), vérifie que la bonne fiche remonte.
6. **Chat ↔ CRM** : « donne-moi le suivi de [client] » (read_contact, pas d'invention).
7. **Calendrier** : « mes échéances 60 jours » (anti-hallu si pas de compte) ; quick-add d'un événement local.
8. **Facturation** : crée un devis pour un client, génère le PDF (garde-fou émetteur OK car profil rempli), convertit en facture, marque payé ; teste une devise CAD.
9. **Skills Office** : « génère un programme de formation en Word » (generate_document → vrai fichier).
10. **Juridique (RAG)** : « clause de pénalités de retard » (doit citer L441-10, pas L441-6) ; « franchise TVA » (293 B).
11. **Board de décision** : délibération sur un choix (5 conseillers).
12. **Calculateurs** : ROI d'un investissement formation.
13. **Image** : moodboard / visuel (si clé dispo).
14. **RGPD** : export d'un contact (Art.20), anonymisation d'un autre (Art.17), vérifie que le fantôme ne remonte plus.
15. **Tasks / notifications** : crée une tâche, la complète ; liste les notifications.
16. **Email** : (si configurable en test) brouillon + signature ; sinon vérifie le comportement sans compte.

Critères : pour chaque étape, l'action aboutit, les données réelles sont utilisées (pas d'hallucination), la souveraineté et le juridique sont justes, les garde-fous se déclenchent. Tout KO = bug à corriger avant 0.20.0.
