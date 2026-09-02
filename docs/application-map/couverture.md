# Couverture et limites de la carte

- Couverture validee : 100.0 %
- Fichiers attendus : 1047
- Validation `passed` : True

## Fichiers non lus (0)


## Doubles lectures manquantes (0)


## Invariants divergents, a arbitrer (14)

- .github/workflows/ci.yml: aucun mot commun entre les invariants de lecteur-M15:c2-M15-WP-C-004, lecteur-R1 (seconde lecture indépendante des fichiers critiques):c2-R1 (seconde lecture indépendante des fichiers critiques)-WP-C-004, orchestrateur:wpc004-orchestrateur
- src/backend/app/models/board.py: aucun mot commun entre les invariants de lecteur-D09:c2-D09-WP-047, wp047-lecteur1:wp047-lecteur1
- src/backend/app/routers/voice.py: aucun mot commun entre les invariants de lecteur-D08:c2-D08-WP-051, wp051-lecteur1:wp051-lecteur1
- src/backend/app/skills_config/pptx/SKILL.md: aucun mot commun entre les invariants de lecteur-D02:c2-D02-WP-055, lecteur-cartographie-wp055:wp055-lecteur1
- src/frontend/src-tauri/gen/schemas/capabilities.json: aucun mot commun entre les invariants de lecteur-D10:c2-D10-WP-057, lecteur-wp057:wp057-lecteur1
- src/frontend/src/components/calendar/calendarErrors.ts: aucun mot commun entre les invariants de lecteur-D07:c2-D07-WP-061, lecteur-cartographie-wp061:wp061-lecteur1
- src/frontend/src/components/invoices/InvoicesPanel.test.tsx: aucun mot commun entre les invariants de lecteur-D01:c2-D01-WP-C-026, lecteur-cartographie-wpc026:wpc026-lecteur1-20260831
- src/frontend/src/components/memory/MemoryPanel.test.tsx: aucun mot commun entre les invariants de lecteur-D07:c2-D07-WP-064, lecteur-cartographie-wp064:wp064-lecteur1
- src/frontend/src/components/prototype/AccueilMoinsCharge.test.tsx: aucun mot commun entre les invariants de lecteur-D06:c2-D06-WP-065, wp065-lecteur1:wp065-lecteur1
- src/frontend/src/components/prototype/MeetingConversationCard.tsx: aucun mot commun entre les invariants de lecteur-D04:c2-D04-WP-066, lecteur-cartographie-wp066:wp066-lecteur1
- tests/e2e/stories/parcours-04-crm.spec.ts: aucun mot commun entre les invariants de lecteur-D11:c2-D11-WP-085, lecteur-M10:c2-M10-WP-085
- tests/e2e/stories/parcours-06-navigation.spec.ts: aucun mot commun entre les invariants de lecteur-D11:c2-D11-WP-085, lecteur-M10:c2-M10-WP-085
- tests/test_modeles_disponibles.py: aucun mot commun entre les invariants de lecteur-D08:c2-D08-WP-080, wp080-lecteur1:wp080-lecteur1
- tests/test_slash_commands.py: aucun mot commun entre les invariants de lecteur-D09:c2-D09-WP-084, wp084-lecteur1:wp084-lecteur1

## Disparus depuis l'inventaire (0)


## Lus sur une version anterieure (104)

- src/backend/app/__init__.py
- src/backend/app/config.py
- src/backend/app/models/database.py
- src/backend/app/models/entities.py
- src/backend/app/routers/calendar.py
- src/backend/app/routers/chat.py
- src/backend/app/routers/config.py
- src/backend/app/routers/dashboard.py
- src/backend/app/routers/data.py
- src/backend/app/routers/follow_ups.py
- src/backend/app/routers/invoices.py
- src/backend/app/routers/memory.py
- src/backend/app/routers/rgpd.py
- src/backend/app/services/agents/git_service.py
- src/backend/app/services/command_registry.py
- src/backend/app/services/crm_export.py
- src/backend/app/services/crm_import.py
- src/backend/app/services/email/imap_smtp_provider.py
- src/backend/app/services/email/provider_factory.py
- src/backend/app/services/mcp_service.py
- src/backend/app/services/path_security.py
- src/backend/app/services/relances.py
- src/backend/app/services/workspace_tools.py
- src/backend/tests/test_backup.py
- src/backend/tests/test_escalation.py
- src/backend/tests/test_personalisation.py
- src/backend/tests/test_services_security.py
- src/frontend/package-lock.json
- src/frontend/package.json
- src/frontend/src-tauri/Cargo.lock
- src/frontend/src-tauri/Cargo.toml
- src/frontend/src-tauri/capabilities/default.json
- src/frontend/src-tauri/tauri.conf.json
- src/frontend/src/components/atelier/AgentCatalog.tsx
- src/frontend/src/components/atelier/AtelierPanel.tsx
- src/frontend/src/components/board/AdvisorArcLayout.tsx
- src/frontend/src/components/calendar/CalendarView.tsx
- src/frontend/src/components/calendar/EventDetail.tsx
- src/frontend/src/components/chat/ChatInput.tsx
- src/frontend/src/components/chat/EntitySuggestion.tsx
- src/frontend/src/components/chat/MessageBubble.tsx
- src/frontend/src/components/chat/ToolConfirmationCard.tsx
- src/frontend/src/components/crm/PipelineView.tsx
- src/frontend/src/components/documents/DocumentsList.tsx
- src/frontend/src/components/documents/OutlineTree.tsx
- src/frontend/src/components/documents/SectionEditor.tsx
- src/frontend/src/components/email/EmailPanel.tsx
- src/frontend/src/components/email/wizard/VerifyStep.tsx
- src/frontend/src/components/guided/ActionCard.tsx
- src/frontend/src/components/guided/DynamicSkillForm.tsx
- src/frontend/src/components/guided/ImageGenerationPanel.tsx
- src/frontend/src/components/home/HomeCommands.tsx
- src/frontend/src/components/home/HomeHeader.tsx
- src/frontend/src/components/home/QuickActions.tsx
- src/frontend/src/components/invoices/InvoicesPanel.tsx
- src/frontend/src/components/memory/MemoryPanel.tsx
- src/frontend/src/components/memory/ProjectsKanban.tsx
- src/frontend/src/components/onboarding/OnboardingWizard.tsx
- src/frontend/src/components/prompts/PromptLibrary.tsx
- src/frontend/src/components/prototype/TodayDashboardCard.tsx
- src/frontend/src/components/prototype/prospectRelance.test.ts
- src/frontend/src/components/prototype/prototypeReadModels.ts
- src/frontend/src/components/rfc/RFCCapture.tsx
- src/frontend/src/components/sidebar/ConversationSidebar.tsx
- src/frontend/src/components/tasks/TaskKanban.tsx
- src/frontend/src/components/ui/NotificationCenter.tsx
- src/frontend/src/hooks/useAutosave.test.ts
- src/frontend/src/hooks/useAutosave.ts
- src/frontend/src/lib/civilDate.ts
- src/frontend/src/lib/demoMask.ts
- src/frontend/src/lib/purgeLocalData.test.ts
- src/frontend/src/lib/purgeLocalData.ts
- src/frontend/src/services/api/memory.ts
- src/frontend/src/stores/demoStore.ts
- src/frontend/src/styles/couleursDeDomaine.test.ts
- src/frontend/src/styles/globals.css
- tests/conftest.py
- tests/e2e/README.md
- tests/e2e/stories/parcours-01-premier-lancement.spec.ts
- tests/e2e/stories/parcours-02-memory.spec.ts
- tests/e2e/stories/parcours-03-email.spec.ts
- tests/e2e/stories/parcours-04-crm.spec.ts
- tests/e2e/stories/parcours-05-settings.spec.ts
- tests/e2e/stories/parcours-06-navigation.spec.ts
- tests/e2e/stories/parcours-07-rendez-vous-prototype.spec.ts
- tests/e2e/stories/parcours-08-capacites-prototype.spec.ts
- tests/protocols/app/personas/A1-sophie-freelance.md
- tests/protocols/shared/catastrophes.md
- tests/test_atelier_traitement.py
- tests/test_backup_encryption.py
- tests/test_cloison_agenda.py
- tests/test_invoice_currency_migration.py
- tests/test_profil_generation.py
- tests/test_profil_indexation_serialisee.py
- tests/test_regression.py
- tests/test_relance_une_seule_definition.py
- tests/test_routers_crm_full.py
- tests/test_routers_dashboard.py
- tests/test_routers_data.py
- tests/test_routers_invoices.py
- tests/test_routers_memory.py
- tests/test_routers_rgpd.py
- tests/test_services_web_search.py
- tests/test_workspace_search_invoices.py
