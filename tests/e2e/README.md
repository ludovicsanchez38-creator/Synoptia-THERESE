# THÉRÈSE v2 - Tests E2E

Tests end-to-end automatisés avec Playwright.

## Installation

```bash
# Installer les dépendances E2E
cd /Users/synoptia/Desktop/Dev\ Synoptia/THERESE\ V2
uv pip install -e ".[e2e]"

# Installer les navigateurs Playwright
uv run playwright install chromium
```

## Lancer les tests

### Mode headless (CI)

```bash
# Tous les tests
uv run pytest tests/e2e/ -v

# Un fichier spécifique
uv run pytest tests/e2e/test_onboarding.py -v

# Un test spécifique
uv run pytest tests/e2e/test_chat.py::test_chat_send_message_and_receive_response -v
```

### Mode headed (voir le navigateur)

```bash
# Avec slowmo pour debug
uv run pytest tests/e2e/ -v --headed --slowmo 1000
```

## Structure

```
tests/e2e/
├── conftest.py              # Fixtures (backend, browser, page, reset_db)
├── test_onboarding.py       # Wizard 6 étapes
├── test_chat.py             # Chat, messages, streaming
├── test_guided_prompts.py   # Navigation actions/sous-options
├── test_skills.py           # TODO: Génération DOCX/PPTX/XLSX
├── test_images.py           # TODO: Génération images GPT/Gemini
├── screenshots/             # Captures d'écran des tests
└── README.md
```

## Fixtures disponibles

| Fixture | Scope | Description |
|---------|-------|-------------|
| `sandbox_env` | session | Environnement isolé (`~/.therese-test-sandbox`) |
| `backend_server` | session | Lance le backend FastAPI |
| `reset_db` | function | Reset la DB entre chaque test |
| `browser_context` | function | Browser Playwright (headed, slowmo) |
| `page` | function | Page navigateur pointant sur http://localhost:1420 |
| `skip_onboarding` | function | Marque l'onboarding comme complété |

## Tests implémentés

### Onboarding (5 tests)
- ✅ `test_onboarding_wizard_complete_flow` - Flux complet 6 étapes
- ✅ `test_onboarding_validation_profile_required` - Validation champs obligatoires
- ✅ `test_onboarding_llm_validation` - Validation format clé API
- ✅ `test_onboarding_security_acknowledgement_required` - Checkbox obligatoire
- ✅ `test_onboarding_navigation_back` - Navigation arrière dans stepper

### Chat (7 tests)
- ✅ `test_chat_send_message_and_receive_response` - Envoi/réception message
- ✅ `test_chat_new_conversation` - Créer nouvelle conversation
- ✅ `test_chat_conversations_sidebar` - Toggle sidebar Cmd+B
- ✅ `test_chat_keyboard_shortcuts` - Raccourcis Cmd+K, Cmd+M
- ✅ `test_chat_guided_prompts_navigation` - Navigation actions
- ✅ `test_chat_guided_prompt_fills_textarea` - Remplissage textarea
- ✅ `test_chat_message_persistence` - Persistance après reload

### Guided Prompts (6 tests)
- ✅ `test_guided_action_displays_suboptions` - Affichage sous-options (x3)
- ✅ `test_guided_back_navigation` - Bouton retour
- ✅ `test_guided_prompt_template_structure` - Structure prompts
- ✅ `test_guided_skills_trigger_prompt_panel` - Panel skills
- ✅ `test_guided_images_trigger_prompt_panel` - Panel images
- ✅ `test_guided_animations_smooth` - Animations fluides

**Total : 18 tests implémentés**

## TODO

- [ ] `test_skills.py` - Génération documents Office
- [ ] `test_images.py` - Génération images
- [ ] `test_memory.py` - CRUD contacts/projets
- [ ] `test_board.py` - Board de décision
- [ ] `test_settings.py` - Configuration paramètres

## Screenshots

Les screenshots sont automatiquement capturés pendant les tests dans `tests/e2e/screenshots/`.

Utiles pour :
- Debug visuel
- Documentation
- Régression UI

## Notes

### Prérequis

1. **Backend doit tourner** sur http://localhost:8000
2. **Frontend Tauri dev** doit tourner sur http://localhost:1420
3. **Sandbox isolé** : Les tests n'affectent pas `~/.therese` principal

### Performance

- Les tests utilisent `slow_mo=500` pour être observables
- Pour CI, retirer `slow_mo` et mettre `headless=True`

### Debugging

```bash
# Mode interactif avec pause
uv run pytest tests/e2e/ -v --headed --slowmo 2000 -k test_onboarding_wizard

# Voir les logs backend
tail -f /tmp/therese-e2e-backend.log
```

## CI/CD Integration

Exemple GitHub Actions :

```yaml
- name: Run E2E tests
  run: |
    # Lancer backend en arrière-plan
    uv run uvicorn app.main:app --port 8000 &

    # Lancer frontend en arrière-plan
    cd src/frontend && npm run tauri dev &

    # Attendre que les services démarrent
    sleep 10

    # Lancer les tests
    uv run pytest tests/e2e/ -v --headed=false
```
