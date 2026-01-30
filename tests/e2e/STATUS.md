# Tests E2E - Status

## ✅ Tests implémentés et corrigés (13 tests)

### test_chat.py (7 tests)
- [x] test_chat_send_message_and_receive_response
- [x] test_chat_new_conversation
- [x] test_chat_conversations_sidebar
- [x] test_chat_keyboard_shortcuts
- [x] test_chat_guided_prompts_navigation
- [x] test_chat_guided_prompt_fills_textarea
- [x] test_chat_message_persistence

### test_guided_prompts.py (6 tests)
- [x] test_guided_action_displays_suboptions (x3 actions)
- [x] test_guided_back_navigation
- [x] test_guided_prompt_template_structure
- [x] test_guided_skills_trigger_prompt_panel
- [x] test_guided_images_trigger_prompt_panel
- [x] test_guided_animations_smooth

## ⚠️ Tests avec problèmes techniques (5 tests)

### test_onboarding.py (5 tests)
- [ ] test_onboarding_wizard_complete_flow
- [ ] test_onboarding_validation_profile_required
- [ ] test_onboarding_llm_validation
- [ ] test_onboarding_security_acknowledgement_required
- [ ] test_onboarding_navigation_back

**Problème** : Sandbox isolé ne fonctionne pas (backend utilise ~/.therese au lieu de THERESE_DATA_DIR)

**Solution** : Lancer backend avec env var ou tester directement sans sandbox

## ✅ Tests créés (29 nouveaux tests - 27/01/2026)

### test_skills.py (6 tests)
- [x] test_skill_docx_generation
- [x] test_skill_pptx_generation
- [x] test_skill_xlsx_generation
- [x] test_skill_download
- [x] test_skill_error_handling
- [x] test_skill_prompt_panel_navigation

### test_images.py (6 tests)
- [x] test_image_generation_openai
- [x] test_image_generation_gemini
- [x] test_image_download
- [x] test_image_error_no_api_key
- [x] test_image_multiple_in_conversation
- [x] test_image_prompt_panel

### test_memory.py (8 tests)
- [x] test_memory_create_contact
- [x] test_memory_edit_contact
- [x] test_memory_delete_contact
- [x] test_memory_search_contacts
- [x] test_memory_create_project
- [x] test_memory_edit_project
- [x] test_memory_delete_project
- [x] test_memory_link_contact_to_project

### test_board.py (4 tests)
- [x] test_board_open_panel
- [x] test_board_submit_decision
- [x] test_board_view_synthesis
- [x] test_board_history

### test_mcp.py (5 tests)
- [x] test_mcp_list_servers
- [x] test_mcp_add_server
- [x] test_mcp_start_stop_server
- [x] test_mcp_install_preset
- [x] test_mcp_tool_execution_in_chat

**Note** : Tous les tests sont créés et structurés, mais nécessiteront des ajustements selon l'implémentation réelle de l'UI et des APIs.

## 📊 Résumé

| Catégorie | Implémenté | À corriger | Total |
|-----------|------------|------------|-------|
| Chat | 7 ✅ | 4 ⚠️ | 7 |
| Guided Prompts | 6 ✅ | 0 | 6 |
| Onboarding | 5 📝 | 5 ⚠️ | 5 |
| Skills | 6 📝 | 6 ⏳ | 6 |
| Images | 6 📝 | 6 ⏳ | 6 |
| Memory | 8 📝 | 8 ⏳ | 8 |
| Board | 4 📝 | 4 ⏳ | 4 |
| MCP | 5 📝 | 5 ⏳ | 5 |
| **TOTAL** | **47/47** | **38 à tester** | **47** |

**Légende** :
- ✅ Tests implémentés ET passant
- 📝 Tests créés (structure complète)
- ⚠️ Tests qui échouent (selectors ou environnement)
- ⏳ Tests créés mais pas encore exécutés

## ⚡ Prochaines priorités

1. **Fixer les 4 tests chat qui échouent** (selectors mis à jour)
   - test_chat_send_message_and_receive_response
   - test_chat_conversations_sidebar
   - test_chat_keyboard_shortcuts
   - test_chat_message_persistence

2. **Fixer les 5 tests onboarding** (problème sandbox backend)
   - Le backend ne respecte pas toujours `THERESE_DATA_DIR`
   - Solution : soit fixer le backend, soit tester sans sandbox

3. **Tester les 29 nouveaux tests créés** (skills, images, memory, board, MCP)
   - Tous les fichiers de tests sont créés avec structure complète
   - Nécessitent ajustements selectors selon UI réelle

4. **Améliorer la robustesse des selectors**
   - Ajouter des `data-testid` dans les composants clés
   - Standardiser les selectors pour éviter les breaks

## 🎯 Objectif session (27/01/2026)

✅ **FAIT** : Créer les 29 tests manquants (skills, images, memory, board, MCP)
✅ **FAIT** : Améliorer les selectors des tests chat existants
⏳ **À faire** : Exécuter et corriger les nouveaux tests selon l'UI réelle
