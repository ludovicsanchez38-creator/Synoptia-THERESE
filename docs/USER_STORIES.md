# User Stories - THERESE V2

> **Version** : MVP v2.7
> **Total** : 100 User Stories
> **Date** : 24 janvier 2026

---

## Resume Global

| Module | US | Tests Backend | Tests Frontend |
|--------|-----|---------------|----------------|
| Chat Multi-Provider | 10 | `test_routers_chat.py` | `chatStore.test.ts` |
| Skills Office | 10 | `test_routers_skills.py` | `SkillExecutionPanel.test.tsx` |
| MCP Tool Calling | 10 | `test_routers_mcp.py` | `ToolsPanel.test.tsx` |
| Board de Decision | 5 | `test_routers_board.py` | `BoardPanel.test.tsx` |
| Calculateurs | 5 | `test_routers_calculators.py` | - |
| Generation d'Images | 5 | `test_routers_images.py` | - |
| Memoire | 5 | `test_routers_memory.py` | `MemoryPanel.test.tsx` |
| Voice Input | 5 | `test_routers_voice.py` | `useVoiceRecorder.test.ts` |
| Onboarding | 5 | `test_routers_config.py` | `OnboardingWizard.test.tsx` |
| File Browser | 5 | - | `FileBrowser.test.tsx` |
| Web Search | 5 | `test_services_web_search.py` | - |
| Accessibilite | 5 | - | `accessibility.test.tsx` |
| Securite & Privacy | 5 | `test_security.py` | - |
| Edge Cases & Erreurs | 5 | `test_error_handling.py` | `error-handling.test.ts` |
| Performance | 5 | `test_performance.py` | `performance.test.ts` |
| Backup & Donnees | 5 | `test_backup.py` | - |
| Personnalisation | 5 | `test_routers_config.py` | `SettingsModal.test.tsx` |
| Escalation & Limites | 5 | `test_llm_limits.py` | - |
| **TOTAL** | **100** | | |

---

## 1. Chat Multi-Provider (10 US)

| ID | Status | En tant que... | Je veux... | Afin de... | Test |
|----|--------|----------------|------------|------------|------|
| US-CHAT-01 | :white_check_mark: | Utilisateur | Choisir parmi 6 providers LLM | Selectionner le modele adapte | `test_llm_providers` |
| US-CHAT-02 | :white_check_mark: | Utilisateur | Voir les reponses en streaming SSE | Avoir un feedback immediat | `test_streaming_response` |
| US-CHAT-03 | :white_check_mark: | Utilisateur | Mes conversations persistees SQLite | Retrouver mon historique | `test_conversation_persistence` |
| US-CHAT-04 | :white_check_mark: | Utilisateur | Creer une conversation ephemere | Tester sans polluer l'historique | `test_ephemeral_conversation` |
| US-CHAT-05 | :white_check_mark: | Utilisateur | L'IA utilise les tools MCP automatiquement | Enrichir les reponses | `test_mcp_tool_calling` |
| US-CHAT-06 | :white_check_mark: | Utilisateur | L'IA recherche sur le web | Obtenir des infos actualisees | `test_web_search_integration` |
| US-CHAT-07 | :white_check_mark: | Utilisateur | Utiliser /fichier et /analyse | Injecter du contenu rapidement | `test_slash_commands` |
| US-CHAT-08 | :white_check_mark: | Utilisateur | L'IA reconnait mon identite | Avoir des reponses personnalisees | `test_user_identity` |
| US-CHAT-09 | :white_check_mark: | Utilisateur | Extraction auto des entites | Enrichir ma memoire sans effort | `test_entity_extraction` |
| US-CHAT-10 | :white_check_mark: | Utilisateur | Naviguer avec raccourcis clavier | Gagner en productivite | `test_keyboard_shortcuts` |

---

## 2. Skills Office (10 US)

| ID | Status | En tant que... | Je veux... | Afin de... | Test |
|----|--------|----------------|------------|------------|------|
| US-SKILL-01 | :white_check_mark: | Utilisateur | Generer un document Word | Creer des docs pro rapidement | `test_docx_generation` |
| US-SKILL-02 | :white_check_mark: | Utilisateur | Generer une presentation PPT | Preparer mes reunions sans effort | `test_pptx_generation` |
| US-SKILL-03 | :white_check_mark: | Utilisateur | Generer un tableur Excel | Avoir des tableaux de bord prets | `test_xlsx_generation` |
| US-SKILL-04 | :white_check_mark: | Utilisateur | Voir une progression pendant generation | Savoir que c'est en cours | `test_skill_progress` |
| US-SKILL-05 | :white_check_mark: | Utilisateur | Telecharger le fichier en un clic | L'utiliser immediatement | `test_skill_download` |
| US-SKILL-06 | :white_check_mark: | Utilisateur | Reessayer en cas d'erreur | Ne pas perdre ma demande | `test_skill_retry` |
| US-SKILL-07 | :white_check_mark: | Utilisateur | Personnaliser mon prompt | Obtenir un document adapte | `test_skill_custom_prompt` |
| US-SKILL-08 | :white_check_mark: | Administrateur | Lister les skills via API | Integrer THERESE a d'autres systemes | `test_skills_list_api` |
| US-SKILL-09 | :white_check_mark: | Utilisateur | Style visuel Synoptia coherent | Presenter un travail professionnel | `test_skill_styling` |
| US-SKILL-10 | :white_check_mark: | Utilisateur | Acceder aux skills depuis Guided Prompts | Avoir un parcours fluide | `test_guided_prompts_skills` |

---

## 3. MCP Tool Calling (10 US)

| ID | Status | En tant que... | Je veux... | Afin de... | Test |
|----|--------|----------------|------------|------------|------|
| US-MCP-01 | :white_check_mark: | Utilisateur | Ajouter un serveur MCP personnalise | Etendre les capacites | `test_mcp_add_server` |
| US-MCP-02 | :white_check_mark: | Utilisateur | Installer un preset en un clic | Configurer rapidement | `test_mcp_install_preset` |
| US-MCP-03 | :white_check_mark: | Utilisateur | Voir la liste des tools par serveur | Comprendre ce que je peux demander | `test_mcp_list_tools` |
| US-MCP-04 | :white_check_mark: | Utilisateur | Demarrer/arreter/redemarrer un serveur | Gerer les ressources | `test_mcp_server_lifecycle` |
| US-MCP-05 | :white_check_mark: | Utilisateur | THERESE utilise les tools automatiquement | Effectuer des actions concretes | `test_mcp_auto_tools` |
| US-MCP-06 | :white_check_mark: | Utilisateur | Supprimer un serveur inutilise | Nettoyer ma configuration | `test_mcp_delete_server` |
| US-MCP-07 | :white_check_mark: | Utilisateur | Voir le statut global MCP | Savoir combien sont actifs | `test_mcp_global_status` |
| US-MCP-08 | :white_check_mark: | Administrateur | Serveurs enabled lances au demarrage | Ne pas relancer manuellement | `test_mcp_autostart` |
| US-MCP-09 | :white_check_mark: | Developpeur | Appeler un tool via API REST | Tester ou automatiser | `test_mcp_tool_api` |
| US-MCP-10 | :white_check_mark: | Utilisateur | Configurer des variables d'env | Fournir des tokens d'auth | `test_mcp_env_vars` |

---

## 4. Board de Decision (5 US)

| ID | Status | En tant que... | Je veux... | Afin de... | Test |
|----|--------|----------------|------------|------------|------|
| US-BOARD-01 | :white_check_mark: | Solopreneur | Soumettre une question au Board | Recevoir des perspectives variees | `test_board_submit` |
| US-BOARD-02 | :white_check_mark: | Decideur presse | Recevoir une synthese structuree | Avoir une recommandation claire | `test_board_synthesis` |
| US-BOARD-03 | :white_check_mark: | Entrepreneur | Consulter l'historique des decisions | Revoir les recommandations | `test_board_history` |
| US-BOARD-04 | :white_check_mark: | Utilisateur | Revoir le detail d'une deliberation | Relire les avis | `test_board_detail` |
| US-BOARD-05 | :white_check_mark: | Utilisateur RGPD | Supprimer une decision obsolete | Proteger mes donnees | `test_board_delete` |

---

## 5. Calculateurs Financiers (5 US)

| ID | Status | En tant que... | Je veux... | Afin de... | Test |
|----|--------|----------------|------------|------------|------|
| US-CALC-01 | :white_check_mark: | Solopreneur | Calculer le ROI | Decider si ca vaut le coup | `test_calc_roi` |
| US-CALC-02 | :white_check_mark: | Entrepreneur | Evaluer avec ICE | Prioriser objectivement | `test_calc_ice` |
| US-CALC-03 | :white_check_mark: | Product owner | Utiliser RICE | Maximiser l'impact | `test_calc_rice` |
| US-CALC-04 | :white_check_mark: | Investisseur | Calculer la NPV | Savoir si ca cree de la valeur | `test_calc_npv` |
| US-CALC-05 | :white_check_mark: | Createur | Calculer le break-even | Fixer des objectifs realistes | `test_calc_breakeven` |

---

## 6. Generation d'Images (5 US)

| ID | Status | En tant que... | Je veux... | Afin de... | Test |
|----|--------|----------------|------------|------------|------|
| US-IMG-01 | :white_check_mark: | Solopreneur | Generer une image depuis une description | Creer des visuels sans competences | `test_image_generate` |
| US-IMG-02 | :white_check_mark: | Createur | Fournir une image de reference | Guider le style | `test_image_reference` |
| US-IMG-03 | :white_check_mark: | Utilisateur avance | Choisir le provider et options | Optimiser qualite/cout | `test_image_provider_selection` |
| US-IMG-04 | :white_check_mark: | Utilisateur | Gerer mes images generees | Retrouver mes creations | `test_image_list` |
| US-IMG-05 | :white_check_mark: | Administrateur | Verifier la disponibilite providers | Configurer les cles manquantes | `test_image_status` |

---

## 7. Memoire Contacts/Projets (5 US)

| ID | Status | En tant que... | Je veux... | Afin de... | Test |
|----|--------|----------------|------------|------------|------|
| US-MEM-01 | :white_check_mark: | Solopreneur | Creer un contact avec infos pro | Le retrouver dans mes conversations | `test_memory_create_contact` |
| US-MEM-02 | :white_check_mark: | Utilisateur | Lister mes contacts | Avoir une vue d'ensemble | `test_memory_list_contacts` |
| US-MEM-03 | :white_check_mark: | Utilisateur | Rechercher par mots-cles | Retrouver sans le nom exact | `test_memory_search` |
| US-MEM-04 | :white_check_mark: | Consultant | Creer un projet lie a un contact | Organiser mes missions | `test_memory_create_project` |
| US-MEM-05 | :white_check_mark: | Utilisateur RGPD | Supprimer avec cascade | Exercer mon droit a l'oubli | `test_memory_delete_cascade` |

---

## 8. Voice Input (5 US)

| ID | Status | En tant que... | Je veux... | Afin de... | Test |
|----|--------|----------------|------------|------------|------|
| US-VOICE-01 | :white_check_mark: | Utilisateur | Enregistrer ma voix via bouton micro | Dicter mes messages | `test_voice_record` |
| US-VOICE-02 | :white_check_mark: | Utilisateur | Transcription Groq Whisper | Obtenir un texte exploitable | `test_voice_transcribe` |
| US-VOICE-03 | :white_check_mark: | Utilisateur | Indicateur de chargement | Savoir que c'est en cours | `test_voice_loading` |
| US-VOICE-04 | :white_check_mark: | Utilisateur | Message d'erreur clair | Comprendre le probleme | `test_voice_error` |
| US-VOICE-05 | :white_check_mark: | Utilisateur | Configurer cle API Groq | Activer la transcription | `test_voice_config` |

---

## 9. Onboarding Wizard (5 US)

| ID | Status | En tant que... | Je veux... | Afin de... | Test |
|----|--------|----------------|------------|------------|------|
| US-ONBOARD-01 | :white_check_mark: | Nouvel utilisateur | Ecran de bienvenue | Comprendre les fonctionnalites | `test_onboarding_welcome` |
| US-ONBOARD-02 | :white_check_mark: | Nouvel utilisateur | Configurer mon profil | Reponses personnalisees | `test_onboarding_profile` |
| US-ONBOARD-03 | :white_check_mark: | Nouvel utilisateur | Choisir mon provider LLM | Utiliser THERESE immediatement | `test_onboarding_llm` |
| US-ONBOARD-04 | :white_check_mark: | Nouvel utilisateur | Selectionner mon dossier de travail | THERESE sait ou chercher | `test_onboarding_workdir` |
| US-ONBOARD-05 | :white_check_mark: | Nouvel utilisateur | Resume avant de terminer | Verifier ma config | `test_onboarding_complete` |

---

## 10. File Browser (5 US)

| ID | Status | En tant que... | Je veux... | Afin de... | Test |
|----|--------|----------------|------------|------------|------|
| US-FILE-01 | :white_check_mark: | Utilisateur | Naviguer dans mes dossiers | Trouver facilement mes fichiers | `test_file_navigate` |
| US-FILE-02 | :white_check_mark: | Utilisateur | Boutons navigation (Home, Up, Refresh) | Me deplacer rapidement | `test_file_navigation_buttons` |
| US-FILE-03 | :white_check_mark: | Utilisateur | Icones par type de fichier | Identifier le contenu | `test_file_icons` |
| US-FILE-04 | :white_check_mark: | Utilisateur | Filtrer par recherche | Trouver un fichier specifique | `test_file_search` |
| US-FILE-05 | :white_check_mark: | Utilisateur | Indexer un fichier | L'ajouter a la memoire | `test_file_index` |

---

## 11. Web Search (5 US)

| ID | Status | En tant que... | Je veux... | Afin de... | Test |
|----|--------|----------------|------------|------------|------|
| US-WEB-01 | :white_check_mark: | Utilisateur | Activer/desactiver la recherche web | Controler l'acces internet | `test_websearch_toggle` |
| US-WEB-02 | :white_check_mark: | Utilisateur Gemini | Google Search Grounding natif | Integration optimale | `test_websearch_gemini` |
| US-WEB-03 | :white_check_mark: | Utilisateur Claude/GPT | DuckDuckGo via tool calling | Infos sans cle API | `test_websearch_duckduckgo` |
| US-WEB-04 | :white_check_mark: | Utilisateur | Statut web search via API | Comprendre le fonctionnement | `test_websearch_status` |
| US-WEB-05 | :white_check_mark: | Utilisateur | Resultats formates lisiblement | Exploitation efficace par le LLM | `test_websearch_format` |

---

## 12. Accessibilite (5 US)

| ID | Status | En tant que... | Je veux... | Afin de... | Test |
|----|--------|----------------|------------|------------|------|
| US-A11Y-01 | :construction: | Utilisateur clavier | Naviguer entierement au clavier | Utiliser THERESE sans souris | `test_a11y_keyboard` |
| US-A11Y-02 | :construction: | Utilisateur screen reader | Avoir des labels ARIA appropries | Comprendre l'interface | `test_a11y_aria` |
| US-A11Y-03 | :construction: | Utilisateur malvoyant | Avoir un contraste suffisant (4.5:1) | Lire sans effort | `test_a11y_contrast` |
| US-A11Y-04 | :construction: | Utilisateur photosensible | Desactiver les animations | Eviter les declencheurs | `test_a11y_motion` |
| US-A11Y-05 | :construction: | Utilisateur focus visible | Voir clairement ou je suis | Naviguer efficacement | `test_a11y_focus` |

---

## 13. Securite & Privacy (5 US)

| ID | Status | En tant que... | Je veux... | Afin de... | Test |
|----|--------|----------------|------------|------------|------|
| US-SEC-01 | :construction: | Utilisateur soucieux | Que mes cles API soient chiffrees | Proteger mes credentials | `test_sec_encryption` |
| US-SEC-02 | :construction: | Utilisateur RGPD | Exporter toutes mes donnees | Exercer mon droit de portabilite | `test_sec_export` |
| US-SEC-03 | :construction: | Utilisateur prudent | Etre averti des connexions externes | Controler mes donnees | `test_sec_external_warning` |
| US-SEC-04 | :construction: | Utilisateur entreprise | Configurer un proxy | Respecter la politique IT | `test_sec_proxy` |
| US-SEC-05 | :construction: | Administrateur | Voir les logs d'activite | Auditer l'utilisation | `test_sec_logs` |

---

## 14. Edge Cases & Erreurs (5 US)

| ID | Status | En tant que... | Je veux... | Afin de... | Test |
|----|--------|----------------|------------|------------|------|
| US-ERR-01 | :construction: | Utilisateur | Message d'erreur clair si API down | Comprendre le probleme | `test_err_api_down` |
| US-ERR-02 | :construction: | Utilisateur | Retry automatique en cas de timeout | Ne pas perdre mon message | `test_err_retry` |
| US-ERR-03 | :construction: | Utilisateur | Mode degrade si Qdrant indisponible | Continuer a utiliser le chat | `test_err_qdrant_fallback` |
| US-ERR-04 | :construction: | Utilisateur | Annuler une generation en cours | Arreter une reponse longue | `test_err_cancel` |
| US-ERR-05 | :construction: | Utilisateur | Recuperer une conversation apres crash | Ne pas perdre mon travail | `test_err_recovery` |

---

## 15. Performance & Optimisation (5 US)

| ID | Status | En tant que... | Je veux... | Afin de... | Test |
|----|--------|----------------|------------|------------|------|
| US-PERF-01 | :construction: | Utilisateur | Temps de reponse < 2s pour le premier token | Avoir un feedback rapide | `test_perf_ttft` |
| US-PERF-02 | :construction: | Utilisateur | Chargement progressif des conversations | Ne pas attendre | `test_perf_lazy_load` |
| US-PERF-03 | :construction: | Utilisateur longue session | Pas de memory leak apres 4h | Stabilite continue | `test_perf_memory` |
| US-PERF-04 | :construction: | Utilisateur avec historique | Recherche rapide sur 1000+ conversations | Retrouver efficacement | `test_perf_search` |
| US-PERF-05 | :construction: | Utilisateur mobile/laptop | Optimisation batterie | Economiser l'energie | `test_perf_battery` |

---

## 16. Backup & Donnees (5 US)

| ID | Status | En tant que... | Je veux... | Afin de... | Test |
|----|--------|----------------|------------|------------|------|
| US-BAK-01 | :construction: | Utilisateur | Exporter mes conversations en JSON/Markdown | Archiver mes echanges | `test_backup_export` |
| US-BAK-02 | :construction: | Utilisateur | Importer des conversations existantes | Migrer depuis un autre outil | `test_backup_import` |
| US-BAK-03 | :construction: | Utilisateur prudent | Backup automatique quotidien | Eviter la perte de donnees | `test_backup_auto` |
| US-BAK-04 | :construction: | Utilisateur | Restaurer une sauvegarde | Recuperer mes donnees | `test_backup_restore` |
| US-BAK-05 | :construction: | Utilisateur multi-device | Sync entre Mac et autre machine | Continuite de travail | `test_backup_sync` |

---

## 17. Personnalisation Avancee (5 US)

| ID | Status | En tant que... | Je veux... | Afin de... | Test |
|----|--------|----------------|------------|------------|------|
| US-PERS-01 | :construction: | Utilisateur | Configurer mes raccourcis clavier | Adapter a mon workflow | `test_pers_shortcuts` |
| US-PERS-02 | :construction: | Utilisateur | Creer mes propres prompts templates | Reutiliser mes patterns | `test_pers_templates` |
| US-PERS-03 | :construction: | Utilisateur | Choisir la taille de police | Confort de lecture | `test_pers_fontsize` |
| US-PERS-04 | :construction: | Utilisateur | Configurer le comportement par defaut du LLM | Personnaliser les reponses | `test_pers_llm_defaults` |
| US-PERS-05 | :construction: | Utilisateur | Masquer les fonctionnalites que je n'utilise pas | Interface epuree | `test_pers_hide_features` |

---

## 18. Escalation & Limites IA (5 US)

| ID | Status | En tant que... | Je veux... | Afin de... | Test |
|----|--------|----------------|------------|------------|------|
| US-ESC-01 | :construction: | Utilisateur | Savoir quand l'IA n'est pas sure | Evaluer la fiabilite | `test_esc_uncertainty` |
| US-ESC-02 | :construction: | Utilisateur | Indication du cout API par message | Controler mon budget | `test_esc_cost` |
| US-ESC-03 | :construction: | Utilisateur | Limite de tokens configurable | Eviter les surprises | `test_esc_token_limit` |
| US-ESC-04 | :construction: | Utilisateur | Historique des tokens consommes | Suivre ma consommation | `test_esc_token_history` |
| US-ESC-05 | :construction: | Utilisateur | Alerte si contexte tronque | Comprendre les limites | `test_esc_context_alert` |

---

## Legende

- :white_check_mark: = Implemente et teste
- :construction: = A implementer (nouveau)
- :x: = Non passe / Bug

---

## Fichiers de Tests

### Backend (pytest)

```
tests/
├── __init__.py
├── conftest.py                    # Fixtures partagees
├── test_routers_chat.py           # US-CHAT-01 a US-CHAT-10
├── test_routers_config.py         # US-ONBOARD, US-PERS
├── test_routers_memory.py         # US-MEM-01 a US-MEM-05
├── test_routers_mcp.py            # US-MCP-01 a US-MCP-10
├── test_routers_skills.py         # US-SKILL-01 a US-SKILL-10
├── test_routers_board.py          # US-BOARD-01 a US-BOARD-05
├── test_routers_calculators.py    # US-CALC-01 a US-CALC-05
├── test_routers_images.py         # US-IMG-01 a US-IMG-05
├── test_routers_voice.py          # US-VOICE-01 a US-VOICE-05
├── test_services_llm.py           # LLM multi-provider
├── test_services_web_search.py    # US-WEB-01 a US-WEB-05
├── test_services_mcp.py           # MCP service
├── test_security.py               # US-SEC-01 a US-SEC-05
├── test_error_handling.py         # US-ERR-01 a US-ERR-05
├── test_performance.py            # US-PERF-01 a US-PERF-05
├── test_backup.py                 # US-BAK-01 a US-BAK-05
└── test_llm_limits.py             # US-ESC-01 a US-ESC-05
```

### Frontend (vitest)

```
src/frontend/src/
├── stores/
│   └── chatStore.test.ts          # Store tests
├── hooks/
│   ├── useKeyboardShortcuts.test.ts
│   └── useVoiceRecorder.test.ts
├── components/
│   ├── chat/
│   │   └── ChatInput.test.tsx
│   ├── memory/
│   │   └── MemoryPanel.test.tsx
│   ├── settings/
│   │   └── SettingsModal.test.tsx
│   ├── onboarding/
│   │   └── OnboardingWizard.test.tsx
│   ├── board/
│   │   └── BoardPanel.test.tsx
│   ├── guided/
│   │   └── SkillExecutionPanel.test.tsx
│   └── files/
│       └── FileBrowser.test.tsx
└── lib/
    ├── utils.test.ts
    ├── accessibility.test.tsx     # US-A11Y
    ├── error-handling.test.ts     # US-ERR frontend
    └── performance.test.ts        # US-PERF frontend
```

---

## Commandes de Test

```bash
# Backend
cd src/backend
uv run pytest -v                           # Tous les tests
uv run pytest -v -k "chat"                 # Tests chat uniquement
uv run pytest --cov=app --cov-report=html  # Avec couverture

# Frontend
cd src/frontend
npm test                                    # Tous les tests
npm run test:watch                          # Mode watch
npm run test:coverage                       # Avec couverture
```

---

*Derniere mise a jour : 24 janvier 2026*
