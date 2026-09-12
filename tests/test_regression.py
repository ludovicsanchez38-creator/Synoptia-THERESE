"""
THÉRÈSE v2 - Tests de non-régression : COMPORTEMENT seulement.

Réécrit le 08/09/2026 (B-039, B-332, cycle 4). Ce fichier comptait 8 531
lignes et 584 tests, dont 458 lisaient le texte du code source et y
cherchaient des chaînes : un renommage les faisait rougir sans régression,
une chaîne placée en commentaire suffisait à les satisfaire.

Ne restent ici que les 126 tests qui exercent le code. Les gardes textuelles
ont été remplacées par des tests de comportement (`test_regression_fournisseurs.py`,
`test_regression_facturation_agenda.py`, `test_regression_socle.py`, vitest
côté interface) ou par des sentinelles structurelles (`test_sentinelles_structure.py`,
pour ce que la suite ne peut pas exécuter : point d'entrée PyInstaller, spec,
coque Rust, configuration Tauri). Le détail, test par test :
`docs/tests/2026-09-08-gardes-textuelles-remplacees.md`.

Convention : un test par bug, nommé test_BUGXXX_description.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Chemins sources
SRC = Path(__file__).resolve().parent.parent / "src" / "backend"
MAIN_PY = SRC / "main.py"
APP_MAIN_PY = SRC / "app" / "main.py"
EMBEDDINGS_PY = SRC / "app" / "services" / "embeddings.py"
ENCRYPTION_PY = SRC / "app" / "services" / "encryption.py"
USER_PROFILE_PY = SRC / "app" / "services" / "user_profile.py"

FRONTEND = Path(__file__).resolve().parent.parent / "src" / "frontend" / "src"
API_CORE_TS = FRONTEND / "services" / "api" / "core.ts"



class TestBUG110_UpdateBloquee:
    """BUG-110 : Mise à jour auto bloquée depuis v0.24.3

    Problème : L'application reste en v0.24.3 après tentative de mise à jour,
    même si le téléchargement semble réussir et le redémarrage s'effectue.

    Cause probable d'après la recherche :
    1. Bug Tauri connu sur installations dans répertoires personnalisés (Windows)
    2. Configuration installMode incorrecte (quiet échoue silencieusement)
    3. Problème de format d'installateur (MSI vs NSIS)
    4. Redémarrage automatique qui échoue ou ne trouve pas la nouvelle version
    """
    def test_updater_config_has_windows_installmode_passive(self):
        """Test de régression : la configuration updater doit spécifier installMode passive

        Le mode 'quiet' peut échouer silencieusement sans permissions admin sur Windows.
        Le mode 'passive' (par défaut) ou 'basicUi' est plus robuste.
        """
        import json

        tauri_conf_path = Path(__file__).resolve().parent.parent / "src" / "frontend" / "src-tauri" / "tauri.conf.json"

        # Lire la configuration Tauri
        with open(tauri_conf_path, 'r', encoding='utf-8') as f:
            tauri_conf = json.load(f)

        # Vérifier que le plugin updater existe
        assert "updater" in tauri_conf["plugins"], "Plugin updater manquant"

        updater_config = tauri_conf["plugins"]["updater"]

        # Vérifier l'endpoint correct
        assert "endpoints" in updater_config, "Endpoints updater manquants"
        assert len(updater_config["endpoints"]) > 0, "Aucun endpoint configuré"
        assert "synoptia.fr/therese/alpha/latest.json" in updater_config["endpoints"][0], \
            "Endpoint incorrect, devrait pointer sur synoptia.fr"

        # Si windows est configuré, vérifier installMode
        if "windows" in updater_config:
            windows_config = updater_config["windows"]
            if "installMode" in windows_config:
                # Si installMode est défini, il ne doit pas être "quiet"
                assert windows_config["installMode"] != "quiet", \
                    "installMode 'quiet' peut échouer silencieusement - utiliser 'passive' ou 'basicUi'"
    def test_updater_endpoint_availability(self):
        """Test que l'endpoint de mise à jour est accessible et retourne du JSON valide"""
        pytest.skip("Test réseau désactivé - nécessite connectivité internet")
        import json

        import requests

        tauri_conf_path = Path(__file__).resolve().parent.parent / "src" / "frontend" / "src-tauri" / "tauri.conf.json"

        with open(tauri_conf_path, 'r', encoding='utf-8') as f:
            tauri_conf = json.load(f)

        endpoint = tauri_conf["plugins"]["updater"]["endpoints"][0]

        try:
            # Test de connectivité (timeout court pour ne pas bloquer les tests)
            response = requests.get(endpoint, timeout=10)

            # Si accessible, vérifier la structure JSON
            if response.status_code == 200:
                update_data = response.json()

                # Structure attendue d'un fichier latest.json Tauri
                expected_fields = ["version", "pub_date", "platforms"]
                for field in expected_fields:
                    assert field in update_data, f"Champ manquant dans latest.json: {field}"

                # Vérifier que les plateformes incluent Windows
                platforms = update_data.get("platforms", {})
                assert "windows-x86_64" in platforms, "Plateforme Windows manquante"

                # Vérifier que l'URL de téléchargement Windows existe
                windows_platform = platforms["windows-x86_64"]
                assert "url" in windows_platform, "URL de téléchargement Windows manquante"
                assert "signature" in windows_platform, "Signature Windows manquante"

        except requests.RequestException:
            # Si l'endpoint n'est pas accessible, c'est un warning, pas une erreur
            pytest.skip("Endpoint de mise à jour non accessible (normal en développement)")
    def test_tauri_pubkey_configured(self):
        """Test que la clé publique de signature est configurée"""
        import json

        tauri_conf_path = Path(__file__).resolve().parent.parent / "src" / "frontend" / "src-tauri" / "tauri.conf.json"

        with open(tauri_conf_path, 'r', encoding='utf-8') as f:
            tauri_conf = json.load(f)

        updater_config = tauri_conf["plugins"]["updater"]

        # Vérifier que pubkey est configurée et non vide
        assert "pubkey" in updater_config, "Clé publique de signature manquante"
        pubkey = updater_config["pubkey"]
        assert pubkey and len(pubkey) > 50, "Clé publique invalide ou vide"

        # Vérifier le format minisign (base64)
        import base64
        try:
            decoded = base64.b64decode(pubkey)
            assert len(decoded) > 30, "Clé publique trop courte"
        except Exception:
            pytest.fail("Clé publique mal encodée en base64")


class TestBUG012CrashMacM4Max:
    """Force CPU pour les embeddings (pas MPS/Metal)."""
    @patch("sentence_transformers.SentenceTransformer")
    def test_embeddings_constructor_receives_cpu(self, mock_st):
        """Vérifie que SentenceTransformer reçoit bien device='cpu' à l'exécution."""
        from app.services.embeddings import EmbeddingsService

        # Reset singleton
        EmbeddingsService._instance = None
        EmbeddingsService._model = None

        mock_st.return_value = MagicMock()
        mock_st.return_value.get_sentence_embedding_dimension.return_value = 768

        service = EmbeddingsService()
        _ = service.model

        mock_st.assert_called_once()
        call_kwargs = mock_st.call_args
        assert call_kwargs.kwargs.get("device") == "cpu" or (
            len(call_kwargs.args) >= 1 and "cpu" in str(call_kwargs)
        ), "SentenceTransformer doit recevoir device='cpu'"

        # Cleanup
        EmbeddingsService._instance = None
        EmbeddingsService._model = None


class TestBUG013KeychainLazy:
    """Init lazy du service de chiffrement (pas de Keychain au boot)."""
    def test_fernet_none_after_construction(self):
        """_fernet doit être None juste après la construction (avant premier usage)."""
        from app.services.encryption import EncryptionService

        # Reset singleton
        EncryptionService._instance = None
        EncryptionService._fernet = None
        EncryptionService._using_keychain = False

        service = EncryptionService()
        assert service._fernet is None, (
            "_fernet doit rester None après __new__() - "
            "l'init lazy ne se déclenche qu'au premier encrypt/decrypt"
        )

        # Cleanup
        EncryptionService._instance = None
        EncryptionService._fernet = None
        EncryptionService._using_keychain = False


class TestBUG028PricingEUR:
    """BUG-028 : prix EUR non-zéro pour les modèles connus (y compris OpenRouter)."""
    def test_estimate_cost_returns_nonzero_for_known_models(self):
        """estimate_cost() doit retourner un prix > 0 pour les modèles connus."""
        from app.services.token_tracker import TokenTracker

        tracker = TokenTracker()
        # Modèle direct
        cost_direct = tracker.estimate_cost("claude-opus-4-8", 1000, 500)
        assert cost_direct > 0, (
            "Le prix doit être > 0 pour claude-opus-4-8"
        )
        # Modèle avec préfixe OpenRouter
        cost_openrouter = tracker.estimate_cost("anthropic/claude-opus-4-8", 1000, 500)
        assert cost_openrouter > 0, (
            "Le prix doit être > 0 pour anthropic/claude-opus-4-8 (OpenRouter)"
        )
        # Les deux doivent être identiques
        assert cost_direct == cost_openrouter, (
            "Le prix doit être identique avec ou sans préfixe provider"
        )
    def test_estimate_cost_fallback_default_for_unknown(self):
        """estimate_cost() doit retourner 0 pour les modèles inconnus (Ollama)."""
        from app.services.token_tracker import TokenTracker

        tracker = TokenTracker()
        cost = tracker.estimate_cost("llama3:8b", 1000, 500)
        assert cost == 0.0, (
            "Le prix doit être 0 pour les modèles locaux (Ollama) inconnus"
        )
    def test_token_prices_has_major_models(self):
        """TOKEN_PRICES doit contenir les modèles majeurs."""
        from app.services.token_tracker import TOKEN_PRICES

        required = [
            "claude-opus-4-8",
            "claude-sonnet-4-6",
            "gpt-5.5",
            "gemini-3.1-pro-preview",
            "mistral-large-latest",
        ]
        for model in required:
            assert model in TOKEN_PRICES, (
                f"TOKEN_PRICES doit contenir {model}"
            )
            assert TOKEN_PRICES[model]["input"] > 0, (
                f"Le prix input de {model} doit être > 0"
            )


class TestBUG036_XlsxTruncatedCode:
    """Le code tronqué doit être réparé avec ajout automatique de .save()."""
    def test_ensure_save_call_adds_missing_save(self):
        """_ensure_save_call doit ajouter wb.save(output_path) si absent."""
        from app.services.skills.code_executor import _ensure_save_call

        code_without_save = 'wb = Workbook()\nws = wb.active\nws["A1"] = "test"'
        result = _ensure_save_call(code_without_save)
        assert ".save(output_path)" in result, (
            "_ensure_save_call doit ajouter .save(output_path) quand absent"
        )
    def test_ensure_save_call_keeps_existing_save(self):
        """_ensure_save_call ne doit pas dupliquer un .save() existant."""
        from app.services.skills.code_executor import _ensure_save_call

        code_with_save = 'wb = Workbook()\nwb.save(output_path)'
        result = _ensure_save_call(code_with_save)
        assert result.count(".save(output_path)") == 1, (
            "_ensure_save_call ne doit pas dupliquer le .save()"
        )
    def test_ensure_save_call_detects_load_workbook(self):
        """_ensure_save_call doit détecter load_workbook() et ajouter .save()."""
        from app.services.skills.code_executor import _ensure_save_call

        code = 'wb = load_workbook("template.xlsx")\nws = wb.active\nws["A1"] = "modifié"'
        result = _ensure_save_call(code)
        assert ".save(output_path)" in result, (
            "_ensure_save_call doit ajouter .save(output_path) pour load_workbook()"
        )
    def test_ensure_save_call_no_false_positive(self):
        """_ensure_save_call ne doit pas ajouter .save() si un .save(fichier) existe déjà."""
        from app.services.skills.code_executor import _ensure_save_call

        code = 'wb = Workbook()\nwb.save("mon_fichier.xlsx")'
        result = _ensure_save_call(code)
        assert result.count(".save") == 1, (
            "_ensure_save_call ne doit pas dupliquer un .save() existant (même avec un autre argument)"
        )
    def test_repair_truncated_code_adds_save(self):
        """repair_truncated_code doit ajouter .save() après réparation."""
        from app.services.skills.code_executor import repair_truncated_code

        # Code tronqué : syntaxe invalide à la fin, et pas de .save()
        truncated = 'wb = Workbook()\nws = wb.active\nws["A1"] = "test"\nws["A2'
        result = repair_truncated_code(truncated)
        assert result is not None, "repair_truncated_code doit réussir"
        assert ".save(output_path)" in result, (
            "repair_truncated_code doit ajouter .save(output_path) après réparation"
        )
    def test_repair_valid_code_adds_save(self):
        """repair_truncated_code doit ajouter .save() même si le code est déjà valide."""
        from app.services.skills.code_executor import repair_truncated_code

        # Code syntaxiquement valide mais sans .save()
        valid_no_save = 'wb = Workbook()\nws = wb.active\nws["A1"] = "test"'
        result = repair_truncated_code(valid_no_save)
        assert result is not None, "repair_truncated_code doit réussir"
        assert ".save(output_path)" in result, (
            "repair_truncated_code doit ajouter .save() même si le code est syntaxiquement valide"
        )


class TestBUG040_DocxTruncatedCode:
    """Le code DOCX tronqué doit être réparé avec ajout de .save()."""
    def test_ensure_save_call_detects_document(self):
        """_ensure_save_call doit détecter Document() et ajouter .save()."""
        from app.services.skills.code_executor import _ensure_save_call

        code = 'doc = Document()\ndoc.add_heading("Test", level=0)'
        result = _ensure_save_call(code)
        assert ".save(output_path)" in result, (
            "_ensure_save_call doit ajouter doc.save(output_path) pour Document()"
        )
    def test_ensure_save_call_detects_presentation(self):
        """_ensure_save_call doit détecter Presentation() et ajouter .save()."""
        from app.services.skills.code_executor import _ensure_save_call

        code = 'prs = Presentation()\nslide = prs.slides.add_slide(prs.slide_layouts[0])'
        result = _ensure_save_call(code)
        assert ".save(output_path)" in result, (
            "_ensure_save_call doit ajouter prs.save(output_path) pour Presentation()"
        )


class TestBUG032_ExcelFileFilter:
    """Les formats proposés à l'utilisateur doivent être ceux qu'on sait lire.

    RÉÉCRIT le 13/08/2026. Les tests précédents cherchaient des chaînes dans le
    source de `ChatInput.tsx`. Ils ont deux défauts que ce chantier a mis en
    évidence.

    D'abord ils ne tenaient que par la forme du code : la liste de formats est
    désormais partagée (`lib/formatsIndexables.ts`) et consommée par
    l'explorateur ET le sélecteur du chat, donc plus aucune extension n'est
    écrite en dur dans ce fichier — les tests cassaient sans qu'aucun
    comportement n'ait changé.

    Ensuite et surtout, ils ne surveillaient QU'UNE surface. `test_doc_removed`
    documentait depuis longtemps que python-docx ne lit pas le binaire `.doc`,
    et vérifiait son absence du seul filtre du chat : pendant ce temps `.doc`
    restait dans la liste blanche d'indexation ET dans le branchement du
    parseur, où il était indexé à vide. Un test qui grep une surface laisse le
    défaut vivre ailleurs.

    Le comportement est maintenant vérifié là où il vit :

    - `tests/test_extensions_promises_tenues.py` — aucune extension acceptée
      par le contrôle d'entrée n'est illisible par le parseur ;
    - `src/frontend/src/lib/formatsIndexables.test.ts` — la liste de l'interface
      et celle du serveur ne peuvent plus diverger, dans un sens ni dans l'autre.
    """
    def test_le_format_excel_est_lisible(self):
        """Objet historique du BUG-032 : .xlsx doit rester extractible."""
        from app.services.path_security import INDEXABLE_EXTENSIONS

        assert ".xlsx" in INDEXABLE_EXTENSIONS
    def test_le_binaire_doc_reste_refuse(self):
        """python-docx ne lit que l'OOXML : accepter .doc l'indexerait à vide."""
        from app.services.path_security import INDEXABLE_EXTENSIONS

        assert ".doc" not in INDEXABLE_EXTENSIONS


class TestBUG050_KeychainFallbackToFile:
    """BUG-050 : si la clé Keychain diffère du fichier backup, utiliser le fichier."""
    def test_bug050_functional_keychain_fallback(self):
        """Test fonctionnel : si le Keychain a une nouvelle clé, le fichier backup est utilisé."""
        import tempfile

        from app.services.encryption import EncryptionService
        from cryptography.fernet import Fernet

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            tmp_key_file = tmp_path / ".encryption_key"

            # Clé originale (dans le fichier backup)
            original_key = Fernet.generate_key()
            # Nouvelle clé (générée par un binaire avec une autre signature)
            new_keychain_key = Fernet.generate_key()

            # Écrire la clé originale dans le fichier backup
            with open(tmp_key_file, "wb") as f:
                f.write(original_key)

            # Simuler : le Keychain retourne la nouvelle clé, mais le fichier a l'ancienne
            mock_keyring = MagicMock()
            mock_keyring.set_password = MagicMock()

            with (
                patch("app.services.encryption._try_keyring_available", return_value=True),
                patch("app.services.encryption.KEY_FILE", tmp_key_file),
                patch("app.services.encryption.THERESE_DIR", tmp_path),
            ):
                svc = EncryptionService.__new__(EncryptionService)
                svc._using_keychain = False

                with (
                    patch.object(svc, "_get_key_from_keychain", return_value=new_keychain_key),
                    patch.dict("sys.modules", {"keyring": mock_keyring}),
                ):
                    key = svc._get_or_create_key()

            # La clé retournée doit être celle du fichier (pas du Keychain)
            assert key == original_key, (
                "Quand le Keychain a une clé différente du fichier backup, "
                "la clé fichier doit être utilisée (BUG-050)"
            )


class TestBUG098_OllamaDefaultModelDetection:
    """Le défaut Ollama doit être détecté parmi les modèles installés, pas 'mistral-nemo' codé en dur."""
    LLM_PY = SRC / "app" / "services" / "llm.py"
    BOARD_PY = SRC / "app" / "services" / "board.py"
    @staticmethod
    def _fake_httpx_get(models):
        class _Resp:
            status_code = 200

            @staticmethod
            def json():
                return {"models": [{"name": m} for m in models]}

        def _get(url, timeout=None):
            return _Resp()

        return _get
    def test_detect_returns_first_installed_chat_model(self, monkeypatch):
        import httpx
        from app.services.llm import detect_default_ollama_model

        monkeypatch.setattr(httpx, "get", self._fake_httpx_get(["gemma:2b", "llama3:8b"]))
        assert detect_default_ollama_model() == "gemma:2b"
    def test_detect_prefers_installed_over_mistral_nemo(self, monkeypatch):
        """Scénario exact lcjp : gemma:2b installé, mistral-nemo absent."""
        import httpx
        from app.services.llm import detect_default_ollama_model

        monkeypatch.setattr(httpx, "get", self._fake_httpx_get(["gemma:2b"]))
        assert detect_default_ollama_model() == "gemma:2b"
        assert detect_default_ollama_model() != "mistral-nemo"
    def test_detect_skips_embedding_models(self, monkeypatch):
        """Un modèle d'embedding (ex: nomic-embed-text, utilisé par Qdrant) ne doit pas être choisi comme modèle de chat."""
        import httpx
        from app.services.llm import detect_default_ollama_model

        monkeypatch.setattr(httpx, "get", self._fake_httpx_get(["nomic-embed-text:latest"]))
        assert detect_default_ollama_model(fallback="mistral-nemo") == "mistral-nemo"
    def test_detect_fallback_when_ollama_unreachable(self, monkeypatch):
        import httpx
        from app.services.llm import detect_default_ollama_model

        def _boom(url, timeout=None):
            raise httpx.ConnectError("connexion refusée")

        monkeypatch.setattr(httpx, "get", _boom)
        assert detect_default_ollama_model(fallback="mistral-nemo") == "mistral-nemo"


class TestL6_ContactScopeRoundtrip:
    """L6 pastille : le scope d'un contact doit round-tripper (create accepte, response expose).

    Bug trouvé en vérif d'intégration : ContactCreate/ContactResponse n'avaient pas
    scope/scope_id, donc le scope était jeté à la création ET jamais renvoyé -> le
    filtre 'Conv.' de la Mémoire et la pastille de glance ne pouvaient pas fonctionner.
    """
    MEMORY_ROUTER = SRC / "app" / "routers" / "memory.py"
    def test_contact_create_accepts_scope(self):
        from app.models.schemas import ContactCreate

        c = ContactCreate(first_name="X", scope="conversation", scope_id="conv-1")
        assert c.scope == "conversation"
        assert c.scope_id == "conv-1"
    def test_contact_response_exposes_scope(self):
        from app.models.schemas import ContactResponse

        assert "scope" in ContactResponse.model_fields, (
            "ContactResponse doit exposer scope (sinon filtre Conv. + pastille L6 cassés)"
        )
        assert "scope_id" in ContactResponse.model_fields


class TestF17_BoardSovereignMode:
    """Le backend doit supporter le mode souverain (séquentiel Ollama)."""
    BOARD_MODELS_PY = Path("src/backend/app/models/board.py")
    BOARD_SERVICE_PY = Path("src/backend/app/services/board.py")
    ENTITIES_PY = Path("src/backend/app/models/entities.py")
    def test_entities_has_mode(self):
        """B-042 : la garde cherchait « mode » dans TOUT entities.py.

        Retirer la seule déclaration du champ laissait l'assertion vraie,
        satisfaite par « model: », « sqlmodel » et « models » — six
        occurrences pour une seule qui compte. On interroge le modèle.
        """
        from app.models.entities import BoardDecisionDB

        assert "mode" in BoardDecisionDB.model_fields, (
            "BoardDecisionDB doit avoir un champ mode (F-17). "
            f"champs={sorted(BoardDecisionDB.model_fields)}"
        )


class TestBUG_MistralTools:
    """BUG MCP tools : Mistral ne transmettait pas les tools à l'API."""
    def test_mistral_sends_tools_in_json_body(self):
        """Le body JSON Mistral inclut tools + tool_choice=auto quand des tools sont fournis."""
        from app.services.llm import LLMConfig, LLMProvider
        from app.services.providers.mistral import MistralProvider

        provider = MistralProvider(
            LLMConfig(provider=LLMProvider.MISTRAL, model="mistral-large-latest", api_key="x"),
            client=None,
        )
        tools = [{"type": "function", "function": {"name": "read_contact"}}]
        body = provider._build_request_body([{"role": "user", "content": "hi"}], tools=tools)
        assert body["tools"] == tools
        assert body["tool_choice"] == "auto"
        # Sans tools : pas de clés tools/tool_choice
        body_no_tools = provider._build_request_body([{"role": "user", "content": "hi"}])
        assert "tools" not in body_no_tools and "tool_choice" not in body_no_tools


class TestBUGOpenRouterStrftimeWindows:
    """BUG openrouter-strftime : %-d non supporté sur Windows → ValueError crash."""
    def test_current_date_vient_du_prompt_reel(self, monkeypatch):
        """La date lue par le modèle vient de llm.py, et sans zéro de tête.

        B-041 : l'ancien test refabriquait `current_date` par f-string dans
        son propre corps, sans jamais importer llm.py — il ne pouvait donc
        rien détecter. Pire, son assertion `not current_date.startswith("0")`
        était vacante : `str(now.day)` ne commence JAMAIS par un zéro. On fige
        l'horloge au 5 du mois, le seul jour où un `%d` réintroduit se voit,
        et on lit le prompt réellement construit.
        """
        from datetime import UTC, datetime
        from unittest.mock import MagicMock, patch

        from app.services import llm as module
        from app.services.llm import LLMConfig, LLMProvider, LLMService

        class _Horloge(datetime):
            @classmethod
            def now(cls, tz=None):
                instant = cls(2026, 6, 5, 8, 30, tzinfo=UTC)
                return instant.astimezone(tz) if tz else instant.replace(tzinfo=None)

        monkeypatch.setattr(module, "datetime", _Horloge)

        config = LLMConfig(provider=LLMProvider.ANTHROPIC, model="claude-3-haiku-20240307")
        svc = LLMService(config)

        profil = MagicMock()
        profil.name = "Jérôme"
        profil.format_for_llm.return_value = "Prénom : Jérôme"

        with patch("app.services.llm.load_therese_md", return_value=""), patch(
            "app.services.user_profile.get_cached_profile", return_value=profil
        ):
            prompt = svc._get_system_prompt_with_identity()

        assert "{current_date}" not in prompt
        assert "5 juin 2026" in prompt, (
            "la date du prompt doit venir de llm.py, sans zéro de tête"
        )
        assert "05 juin" not in prompt, (
            "zéro de tête : un %d est revenu là où str(now.day) était requis"
        )
    def test_get_system_prompt_no_valueerror(self):
        """_get_system_prompt_with_identity ne lève pas ValueError (ex-bug strftime POSIX)."""
        from unittest.mock import MagicMock, patch

        from app.services.llm import LLMConfig, LLMProvider, LLMService

        config = LLMConfig(provider=LLMProvider.ANTHROPIC, model="claude-3-haiku-20240307")
        svc = LLMService(config)

        mock_profile = MagicMock()
        mock_profile.name = "Jérôme"
        mock_profile.format_for_llm.return_value = "Prénom : Jérôme"

        # _get_system_prompt_with_identity() appelle get_cached_profile() en interne
        # On patche get_cached_profile et load_therese_md
        with patch("app.services.llm.load_therese_md", return_value=""),              patch("app.services.user_profile.get_cached_profile", return_value=mock_profile):
            result = svc._get_system_prompt_with_identity()

        assert "{current_date}" not in result  # placeholder bien substitué
        assert result  # non vide


class TestBUGOpenRouter403MessageErreur:
    """BUG openrouter-403 : message d'erreur vide/opaque sur 403 Forbidden."""
    @staticmethod
    def _make_provider():
        """Crée un OpenRouterProvider avec un client httpx mock."""
        import httpx
        from app.services.llm import LLMConfig, LLMProvider
        from app.services.providers.openrouter import OpenRouterProvider
        config = LLMConfig(
            provider=LLMProvider.OPENROUTER,
            model="anthropic/claude-sonnet-4-6",
            api_key="test-key",
        )
        client = httpx.AsyncClient()
        return OpenRouterProvider(config, client)
    def test_openrouter_403_message_specifique(self):
        """Un 403 doit générer un message lisible sur les crédits, pas juste le code HTTP."""
        import asyncio
        from unittest.mock import MagicMock, patch

        import httpx

        provider = self._make_provider()

        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = '{"error":{"message":"You have exceeded your free tier limits. Please add a payment method at openrouter.ai/settings/billing","code":403}}'
        error = httpx.HTTPStatusError("403 Forbidden", request=MagicMock(), response=mock_response)

        async def run():
            with patch.object(provider.client, "stream", side_effect=error):
                events = []
                async for event in provider.stream(None, [{"role": "user", "content": "test"}]):
                    events.append(event)
                return events

        events = asyncio.new_event_loop().run_until_complete(run())
        assert events, "Aucun événement reçu"
        err_event = events[0]
        assert err_event.type == "error"
        msg = err_event.content or ""
        assert any(word in msg.lower() for word in ["crédit", "credit", "openrouter", "403", "paiement", "billing", "exceeded"]), (
            f"Message 403 non informatif : {msg!r}"
        )
        assert msg != "Erreur API OpenRouter (403)", (
            f"Message générique non informatif toujours présent : {msg!r}"
        )
    def test_openrouter_403_body_vide_fallback(self):
        """Un 403 avec body vide doit donner un message de fallback lisible."""
        import asyncio
        from unittest.mock import MagicMock, patch

        import httpx

        provider = self._make_provider()

        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = ""
        error = httpx.HTTPStatusError("403 Forbidden", request=MagicMock(), response=mock_response)

        async def run():
            with patch.object(provider.client, "stream", side_effect=error):
                events = []
                async for event in provider.stream(None, [{"role": "user", "content": "test"}]):
                    events.append(event)
                return events

        events = asyncio.new_event_loop().run_until_complete(run())
        err_event = events[0]
        assert err_event.type == "error"
        assert "403" in (err_event.content or "") or "crédit" in (err_event.content or "").lower()
    def test_openrouter_401_non_affecte(self):
        """La correction du 403 ne doit pas casser le handler 401."""
        import asyncio
        from unittest.mock import MagicMock, patch

        import httpx

        provider = self._make_provider()

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = '{"error":{"message":"Invalid API key"}}'
        error = httpx.HTTPStatusError("401 Unauthorized", request=MagicMock(), response=mock_response)

        async def run():
            with patch.object(provider.client, "stream", side_effect=error):
                events = []
                async for event in provider.stream(None, [{"role": "user", "content": "test"}]):
                    events.append(event)
                return events

        events = asyncio.new_event_loop().run_until_complete(run())
        err_event = events[0]
        assert err_event.type == "error"
        assert "invalid" in (err_event.content or "").lower() or "invalide" in (err_event.content or "").lower() or "clé" in (err_event.content or "").lower()
    def test_openrouter_429_rate_limit_message_without_unboundlocalerror(self):
        """Une 429 doit rester lisible et ne jamais se transformer en UnboundLocalError."""
        import asyncio
        from unittest.mock import MagicMock, patch

        import httpx

        provider = self._make_provider()

        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.text = '{"error":{"message":"Rate limit exceeded"}}'
        error = httpx.HTTPStatusError("429 Too Many Requests", request=MagicMock(), response=mock_response)

        async def run():
            with patch.object(provider.client, "stream", side_effect=error):
                events = []
                async for event in provider.stream(None, [{"role": "user", "content": "test"}]):
                    events.append(event)
                return events

        events = asyncio.new_event_loop().run_until_complete(run())
        assert events, "Une 429 doit produire un événement d erreur exploitable"
        err_event = events[0]
        assert err_event.type == "error"
        msg = err_event.content or ""
        assert "trop de requêtes" in msg.lower() or "429" in msg, (
            f"Message 429 non informatif : {msg!r}"
        )
        assert "unboundlocalerror" not in msg.lower(), (
            f"La 429 ne doit plus être masquée par une erreur locale : {msg!r}"
        )


class TestBUG73GoogleCalendarTZ:
    """v0.11.5 issue #73 - Google Calendar API recevait des timestamps
    invalides type '2026-04-22T00:00:00+02:00Z' (offset + Z) quand le
    datetime etait tz-aware, ce qui retournait une liste vide ou 400."""
    @pytest.mark.asyncio
    async def test_to_rfc3339_z_convertit_vraiment(self, monkeypatch):
        """La conversion doit être FAITE, pas récitée.

        B-041 : l'ancien test n'importait rien de l'application. Il écrivait
        `datetime(2026, 4, 22, 10, 0).isoformat() + "Z"` et le comparait à la
        chaîne attendue : il testait la bibliothèque standard. Supprimer
        `_to_rfc3339_z` de calendar_service.py le laissait vert. Le helper est
        une fonction imbriquée dans `list_events` : on l'exerce donc par le
        seul chemin qui existe, l'appel, en regardant ce qui part chez Google.
        """
        from datetime import datetime
        from zoneinfo import ZoneInfo

        from app.services import calendar_service as module

        captures: dict = {}

        class _Reponse:
            status_code = 200

            def raise_for_status(self):
                return None

            def json(self):
                return {"items": []}

        class _Client:
            async def get(self, url, headers=None, params=None, timeout=None):
                captures["params"] = dict(params or {})
                return _Reponse()

        async def _faux_client():
            return _Client()

        monkeypatch.setattr(module, "get_http_client", _faux_client)

        service = module.CalendarService("jeton-bidon")
        await service.list_events(
            "primary",
            time_min=datetime(2026, 4, 22, 10, 0, 0),
            time_max=datetime(2026, 4, 22, 12, 0, 0, tzinfo=ZoneInfo("Europe/Paris")),
        )

        # Naïf : déjà considéré UTC, on ajoute seulement le Z.
        assert captures["params"]["timeMin"] == "2026-04-22T10:00:00Z", captures["params"]
        # Aware Paris (été, UTC+2) : ramené en UTC AVANT le Z, jamais
        # « 12:00:00+02:00Z », la forme que Google refuse (issue #73).
        assert captures["params"]["timeMax"] == "2026-04-22T10:00:00Z", captures["params"]
        assert "+" not in captures["params"]["timeMax"]


class TestBUG69OllamaFallbackRespectsProvider:
    """v0.11.5 issue #69 - le fallback LLM ne doit plus retomber sur Ollama
    quand l utilisateur a explicitement choisi un provider cloud sans cle."""
    def test_default_config_no_silent_ollama_fallback_for_cloud_provider(self):
        """Si selected_provider est un provider cloud mais sans cle, la config
        retournee doit conserver le provider choisi (api_key=None) et non Ollama.
        Sinon l utilisateur voit 'Ollama non detecte' qui est un faux diagnostic."""
        from unittest.mock import patch

        from app.services.llm import LLMService
        from app.services.providers.base import LLMProvider

        with patch("app.services.llm._get_api_key_from_db", return_value=None), patch(
            "app.models.database.get_sync_connection"
        ) as mock_db, patch.dict(
            "os.environ",
            {k: "" for k in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY", "MISTRAL_API_KEY", "XAI_API_KEY", "OPENROUTER_API_KEY")},
            clear=False,
        ):
            class _FakeRow:
                def __init__(self, val):
                    self.val = val

                def __getitem__(self, i):
                    return self.val

            class _FakeResult:
                def __init__(self, val):
                    self._val = val

                def fetchone(self):
                    return _FakeRow(self._val) if self._val else None

            class _FakeConn:
                def execute(self, stmt, params):
                    key = params.get("key", "")
                    if key == "llm_provider":
                        return _FakeResult("openrouter")
                    if key == "llm_model":
                        return _FakeResult("anthropic/claude-opus-4-6")
                    return _FakeResult(None)

            class _FakeCtx:
                def __enter__(self):
                    return _FakeConn()

                def __exit__(self, *a):
                    return False

            mock_db.return_value = _FakeCtx()

            service = LLMService()
            assert service.config.provider == LLMProvider.OPENROUTER, (
                f"Le provider selectionne (openrouter) doit etre conserve meme sans cle. "
                f"Obtenu : {service.config.provider}"
            )
            assert service.config.api_key is None, (
                "api_key doit etre None pour laisser l appel API echouer proprement"
            )


class TestP0IA_GardesFousPromptSysteme:
    """Le prompt système doit poser deux garde-fous factuels non négociables."""
    def test_placeholder_guardrails_dans_les_deux_templates(self):
        """P0-IA : les 2 templates de prompt câblent le bloc {guardrails}."""
        from app.services.llm import LLMService

        for tmpl in (
            LLMService.DEFAULT_SYSTEM_PROMPT_TEMPLATE,
            LLMService.DEFAULT_SYSTEM_PROMPT_NO_PROFILE,
        ):
            assert "{guardrails}" in tmpl, (
                "Chaque template de prompt système doit référencer {guardrails} "
                "pour porter les garde-fous souveraineté + juridique."
            )
    def test_prompt_rendu_affirme_le_stockage_local(self):
        """P0-IA-1 : le prompt rendu affirme le stockage 100% local et nie tout serveur."""
        from app.services.llm import LLMService

        prompt = LLMService()._get_system_prompt_with_identity()
        assert "~/.therese/" in prompt, "Le prompt doit nommer le dossier de stockage local"
        # 0.54.0 : ce test exigeait la phrase « Aucun serveur THÉRÈSE n'existe ».
        # Elle est devenue fausse : l'application interroge
        # https://synoptia.fr/therese/alpha/latest.json pour ses mises à jour
        # (tauri.conf.json), donc un serveur Synoptïa existe bel et bien.
        # La propriété que ce garde-fou protège reste la même — le modèle ne
        # doit pas laisser croire à un hébergement des données — mais elle
        # s'exprime désormais sans nier un fait vérifiable.
        assert "AUCUN serveur THÉRÈSE qui héberge les données" in prompt, (
            "Le prompt doit nier tout hébergement des données par un serveur Thérèse"
        )
        # Relecture de diff (Soso) : nier l'hébergement ne suffit pas. La
        # propriété qui compte pour l'utilisateur est que ses données métier ne
        # partent pas chez l'éditeur — un serveur de mise à jour existe, il ne
        # reçoit pas ses contacts.
        assert "aucune donnée métier envoyée à Synoptïa" in prompt, (
            "Le prompt doit garantir qu'aucune donnée métier ne part chez l'éditeur"
        )
        assert "N'invente JAMAIS un lieu d'hébergement" in prompt, (
            "Le prompt doit interdire d'inventer un hébergeur/domaine tiers"
        )
    def test_prompt_rendu_interdit_l_hallu_juridique(self):
        """P0-IA-2 : le prompt rendu impose les placeholders et interdit d'inventer le droit."""
        from app.services.llm import LLMService

        prompt = LLMService()._get_system_prompt_with_identity()
        assert "[à vérifier]" in prompt, (
            "Le prompt doit imposer le placeholder [à vérifier] pour les références incertaines"
        )
        assert "N'invente JAMAIS un numéro d'article" in prompt, (
            "Le prompt doit interdire d'inventer article/SIRET/NDA/taux"
        )
        assert "relecture humaine" in prompt, (
            "Le prompt doit rappeler la relecture humaine sur les documents juridiques"
        )
        # Palier post-passage-2 : forcer le doute sur les numéros d'article même
        # "sûrs" (Mistral citait L441-6 abrogé avec aplomb).
        assert "à confirmer sur Légifrance" in prompt, (
            "Le prompt doit imposer le doute sur les numéros d'article (recodifications)"
        )


class TestP0RGPD_FantomeVectoriel:
    """L'anonymisation doit supprimer l'embedding Qdrant du contact."""
    @pytest.mark.asyncio
    async def test_helper_purge_contact_vector_supprime_le_vecteur(self, monkeypatch):
        """Le helper appelle async_delete_by_entity et retourne le nombre purgé."""
        from unittest.mock import AsyncMock, MagicMock

        import app.services.qdrant as qmod
        from app.services.rgpd_auto import purge_contact_vector

        fake = MagicMock()
        fake.async_delete_by_entity = AsyncMock(return_value=2)
        monkeypatch.setattr(qmod, "get_qdrant_service", lambda: fake)

        deleted = await purge_contact_vector("contact-xyz")

        fake.async_delete_by_entity.assert_awaited_once_with("contact-xyz")
        assert deleted == 2
    @pytest.mark.asyncio
    async def test_helper_purge_best_effort_si_qdrant_plante(self, monkeypatch):
        """Une panne Qdrant ne doit pas faire échouer l'anonymisation (best effort)."""
        from unittest.mock import AsyncMock, MagicMock

        import app.services.qdrant as qmod
        from app.services.rgpd_auto import purge_contact_vector

        fake = MagicMock()
        fake.async_delete_by_entity = AsyncMock(side_effect=RuntimeError("qdrant down"))
        monkeypatch.setattr(qmod, "get_qdrant_service", lambda: fake)

        # Ne doit pas lever, et retourne 0
        assert await purge_contact_vector("contact-xyz") == 0
    @pytest.mark.asyncio
    async def test_anonymize_endpoint_purge_le_vecteur(self, client, monkeypatch):
        """POST /api/rgpd/anonymize/{id} déclenche la purge du vecteur Qdrant."""
        from unittest.mock import AsyncMock, MagicMock

        import app.services.qdrant as qmod

        fake = MagicMock()
        fake.async_delete_by_entity = AsyncMock(return_value=1)
        monkeypatch.setattr(qmod, "get_qdrant_service", lambda: fake)

        resp = await client.post(
            "/api/memory/contacts",
            json={"first_name": "Karim", "last_name": "Benali", "email": "karim@x.fr"},
        )
        assert resp.status_code == 200, resp.text
        cid = resp.json()["id"]

        anon = await client.post(
            f"/api/rgpd/anonymize/{cid}", json={"reason": "Demande du client"}
        )
        assert anon.status_code == 200, anon.text

        # Le helper passe par app.services.qdrant.get_qdrant_service (import au call),
        # donc seul l'anonymize touche `fake` (la création passe par le mock global).
        fake.async_delete_by_entity.assert_awaited_once_with(cid)


class TestP0PROD_ScoringCRM:
    """Le scoring doit refléter les données et accepter un override manuel."""
    @pytest.mark.asyncio
    async def test_create_crm_contact_calcule_le_score(self, client):
        """Bug A : le score initial reflète email/phone/company, n'est plus figé."""
        from app.models.entities import Contact
        from app.services.scoring import calculate_base_score

        resp = await client.post(
            "/api/crm/contacts",
            json={
                "first_name": "Karim",
                "last_name": "Benali",
                "company": "Agence ABC",
                "email": "karim@abc.fr",
                "phone": "+33600000000",
                "stage": "contact",
            },
        )
        assert resp.status_code == 200, resp.text
        score = resp.json()["score"]

        expected = calculate_base_score(
            Contact(
                first_name="Karim",
                company="Agence ABC",
                email="karim@abc.fr",
                phone="+33600000000",
                source="THERESE",
                stage="contact",
            )
        )
        assert score == expected, (
            f"Le score créé ({score}) doit être calculé ({expected}), pas figé"
        )
        assert score != 50, "Le score ne doit plus être figé en dur à 50"
    @pytest.mark.asyncio
    async def test_patch_score_manuel_persiste(self, client):
        """Bug B : PATCH d'un score manuel doit être appliqué et persisté."""
        resp = await client.post(
            "/api/crm/contacts", json={"first_name": "Sofia", "company": "X"}
        )
        assert resp.status_code == 200, resp.text
        cid = resp.json()["id"]

        patch = await client.patch(
            f"/api/memory/contacts/{cid}", json={"score": 88}
        )
        assert patch.status_code == 200, patch.text
        assert patch.json()["score"] == 88

        got = await client.get(f"/api/memory/contacts/{cid}")
        assert got.json()["score"] == 88, "Le score manuel doit être persisté"
    @pytest.mark.asyncio
    async def test_patch_score_manuel_non_ecrase_par_changement_de_stage(self, client):
        """Bug C : un score fourni explicitement ne doit pas être recalculé/écrasé."""
        resp = await client.post(
            "/api/crm/contacts", json={"first_name": "Léa", "company": "Y"}
        )
        assert resp.status_code == 200, resp.text
        cid = resp.json()["id"]

        patch = await client.patch(
            f"/api/memory/contacts/{cid}",
            json={"score": 88, "stage": "signature"},
        )
        assert patch.status_code == 200, patch.text
        assert patch.json()["score"] == 88, (
            "Un score explicite ne doit pas être écrasé par le recalcul auto"
        )
        assert patch.json()["stage"] == "signature"


class TestQW_CADCurrency:
    """La devise CAD doit être acceptée de bout en bout (schéma + PDF + UI)."""
    @pytest.mark.asyncio
    async def test_invoice_accepts_cad_currency(self, client):
        """POST /api/invoices/ doit accepter currency='CAD' (Literal élargi)."""
        c = await client.post("/api/memory/contacts", json={"first_name": "Capov"})
        assert c.status_code == 200, c.text
        cid = c.json()["id"]

        resp = await client.post(
            "/api/invoices/",
            json={
                "contact_id": cid,
                "currency": "CAD",
                "lines": [
                    {
                        "description": "Conseil",
                        "quantity": 1.0,
                        "unit_price_ht": 100.0,
                        "tva_rate": 20.0,
                    }
                ],
            },
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["currency"] == "CAD"


class TestQW_EmailSignature:
    """Signature mail : contrat backend (round-trip + sanitisation) + câblage UI."""
    @pytest.mark.asyncio
    async def test_signature_roundtrip_and_sanitization(self, client):
        """PUT/GET signature : persiste, round-trip, et neutralise le HTML dangereux."""
        from unittest.mock import AsyncMock, MagicMock
        from unittest.mock import patch as _patch

        with _patch("app.routers.email.get_email_provider") as mock_provider:
            mock_instance = MagicMock()
            mock_instance.test_connection = AsyncMock(return_value={"success": True})
            mock_provider.return_value = mock_instance
            await client.post(
                "/api/email/auth/imap-setup",
                json={
                    "email": "sig@example.com",
                    "password": "app-password-test",
                    "imap_host": "imap.example.com",
                    "imap_port": 993,
                    "smtp_host": "smtp.example.com",
                    "smtp_port": 587,
                    "smtp_use_tls": True,
                },
            )

        status = await client.get("/api/email/auth/status")
        account_id = status.json()["accounts"][0]["id"]

        put = await client.put(
            f"/api/email/accounts/{account_id}/signature",
            json={"signature_html": "<p>Ludo</p><script>alert(1)</script>"},
        )
        assert put.status_code == 200, put.text
        assert "Ludo" in put.json()["signature_html"]
        assert "<script>" not in put.json()["signature_html"], "Le HTML doit être sanitisé (nh3)"

        got = await client.get(f"/api/email/accounts/{account_id}/signature")
        assert got.status_code == 200
        assert got.json()["account_id"] == account_id
        assert "<script>" not in (got.json()["signature_html"] or "")
    def test_signature_strips_inline_css(self):
        """Revue : nh3 ne filtre pas le CSS de style -> on retire style de l'allowlist
        (sinon background-image:url(remote) exfiltre, contraire au 100% local)."""
        from app.services.html_sanitizer import sanitize_html

        out = sanitize_html(
            '<div style="position:fixed;background-image:url(https://evil.com/x)">x</div>'
        )
        assert "style=" not in out
        assert "evil.com" not in out
        assert "position:fixed" not in out
        assert "x" in out  # le contenu textuel reste
    def test_signature_links_get_noopener_rel(self):
        """Revue : les liens target=_blank doivent recevoir rel=noopener (anti tab-nabbing)."""
        from app.services.html_sanitizer import sanitize_html

        out = sanitize_html('<a href="https://x.fr" target="_blank">lien</a>')
        assert "noopener" in out


class TestP0IA3_ProviderBadge:
    """Le provider LLM doit être stocké et exposé par message (badge local/cloud)."""
    @pytest.mark.asyncio
    async def test_message_provider_roundtrips_in_history(self, client, db_session):
        """Un message assistant persiste son provider, exposé dans l'historique."""
        from app.models.entities import Conversation, Message

        conv = Conversation(title="Test provider")
        db_session.add(conv)
        await db_session.commit()

        db_session.add(
            Message(
                conversation_id=conv.id,
                role="assistant",
                content="Tes données sont locales dans ~/.therese/.",
                model="mistral-small-latest",
                provider="mistral",
            )
        )
        await db_session.commit()

        resp = await client.get(f"/api/chat/conversations/{conv.id}/messages")
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert len(data) == 1
        assert data[0]["provider"] == "mistral"
        assert data[0]["model"] == "mistral-small-latest"


class TestBUG130_SkillFilePersistence:
    """Le fichier de skill doit être persisté sur le message et restauré."""
    @pytest.mark.asyncio
    async def test_skill_file_roundtrips_in_history(self, client, db_session):
        """extra_data {skill_file} persiste et revient dans l'historique."""
        import json as _json

        from app.models.entities import Conversation, Message

        conv = Conversation(title="Test skill file")
        db_session.add(conv)
        await db_session.commit()

        skill_file = {
            "skill_id": "xlsx-pro",
            "file_id": "abc-12345678",
            "file_name": "Offres.xlsx",
            "file_size": 4917,
            "download_url": "/api/skills/download/abc-12345678",
            "format": "xlsx",
        }
        db_session.add(
            Message(
                conversation_id=conv.id,
                role="assistant",
                content="```python\nwb.save(output_path)\n```",
                model="claude",
                provider="anthropic",
                extra_data=_json.dumps({"skill_file": skill_file}),
            )
        )
        await db_session.commit()

        resp = await client.get(f"/api/chat/conversations/{conv.id}/messages")
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert len(data) == 1
        assert data[0]["extra_data"], "extra_data doit être exposé dans l'historique"
        restored = _json.loads(data[0]["extra_data"])
        assert restored["skill_file"]["file_id"] == "abc-12345678"
        assert restored["skill_file"]["file_name"] == "Offres.xlsx"
        assert restored["skill_file"]["format"] == "xlsx"


class TestP0PROD2_BillingProfile:
    """Le profil émetteur (SIRET, identité) doit être stocké et bloquer une
    facture non conforme."""
    @pytest.mark.asyncio
    async def test_profile_siret_nda_roundtrip(self, client):
        """Le profil accepte et restitue SIRET / code APE / NDA."""
        resp = await client.post(
            "/api/config/profile",
            json={
                "name": "Camille Exemple",
                "company": "Exemple SARL",
                "address": "12 rue de l'Exemple, 04100 Manosque",
                "siret": "12345678900010",
                "code_ape": "0000Z",
                "nda": "11223344556",
            },
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["siret"] == "12345678900010"
        assert data["code_ape"] == "0000Z"
        assert data["nda"] == "11223344556"
    @pytest.mark.asyncio
    async def test_billing_status_complete_after_profile(self, client):
        """billing/profile-status passe à is_complete=True une fois le profil rempli."""
        await client.post(
            "/api/config/profile",
            json={
                "name": "Camille",
                "company": "Exemple SARL",
                "address": "12 rue de l'Exemple",
                "siret": "12345678900010",
            },
        )
        resp = await client.get("/api/invoices/billing/profile-status")
        assert resp.status_code == 200, resp.text
        assert resp.json()["is_complete"] is True
    @pytest.mark.asyncio
    async def test_pdf_generation_blocked_without_emitter(self, client):
        """La génération PDF est bloquée (400) si le profil émetteur est incomplet."""
        # Profil sans SIRET ni adresse -> incomplet
        await client.post("/api/config/profile", json={"name": "Camille"})

        c = await client.post("/api/memory/contacts", json={"first_name": "Client"})
        cid = c.json()["id"]
        inv = await client.post(
            "/api/invoices/",
            json={
                "contact_id": cid,
                "lines": [
                    {
                        "description": "Prestation",
                        "quantity": 1.0,
                        "unit_price_ht": 100.0,
                        "tva_rate": 20.0,
                    }
                ],
            },
        )
        assert inv.status_code == 200, inv.text
        invoice_id = inv.json()["id"]

        pdf = await client.get(f"/api/invoices/{invoice_id}/pdf")
        assert pdf.status_code == 400, pdf.text
        # Le handler HTTPException custom renvoie {"code", "message"} (pas "detail").
        body = pdf.json()
        msg = (body.get("message") or body.get("detail") or "").lower()
        assert "émetteur" in msg or "siret" in msg
    def test_profile_injects_legal_identity_for_llm(self):
        """format_for_llm doit injecter SIRET/NDA pour que le chat ne les invente pas."""
        from app.services.user_profile import UserProfile

        p = UserProfile(name="Camille", siret="12345678900010", nda="11223344556")
        out = p.format_for_llm()
        assert "12345678900010" in out
        assert "11223344556" in out
        assert "ne jamais inventer" in out.lower()


class TestP0PROD3_ChatTools:
    """Le chat doit pouvoir LIRE une fiche contact complète et un agenda large."""
    @pytest.mark.asyncio
    async def test_read_contact_tool_returns_full_fiche(self, db_session):
        """read_contact ne perd RIEN : coordonnées, stage, score, notes, interactions.

        29/08 : la forme a changé (tranche A). Les notes et les activités sont
        descendues dans `traces`, parce que les présenter comme des champs de
        fiche faisait affirmer au modèle un état que personne n'avait validé.
        La garantie d'origine — aucun contenu ne disparaît — est inchangée et
        vérifiée ci-dessous dans la nouvelle forme.
        """
        import json

        from app.models.entities import Activity, Contact
        from app.services.memory_tools import MEMORY_TOOL_NAMES, execute_memory_tool

        assert "read_contact" in MEMORY_TOOL_NAMES

        c = Contact(
            first_name="Karim",
            last_name="Benali",
            company="Agence ABC",
            email="karim@abc.fr",
            stage="proposition",
            score=85,
            notes="Cherche un T3 sous 250k",
        )
        db_session.add(c)
        await db_session.commit()
        db_session.add(Activity(contact_id=c.id, type="call", title="Appel découverte"))
        await db_session.commit()

        result = await execute_memory_tool("read_contact", {"query": "Benali"}, db_session)
        data = json.loads(result)

        assert data["found"] is True
        fiche = data["contacts"][0]
        assert fiche["score"] == 85
        assert fiche["stage"] == "proposition"
        textes = " ".join(
            (t.get("texte") or "") + " " + (t.get("titre") or "") for t in fiche["traces"]
        )
        assert "Cherche un T3 sous 250k" in textes
        assert "Appel découverte" in textes
        assert fiche["etat_courant"] is None, (
            "aucun objet métier ne porte encore l'état : l'app ne doit rien affirmer"
        )
    @pytest.mark.asyncio
    async def test_read_contact_not_found(self, db_session):
        """read_contact renvoie found=False plutôt que d'inventer un contact."""
        import json

        from app.services.memory_tools import execute_memory_tool

        result = await execute_memory_tool("read_contact", {"query": "Personne12345"}, db_session)
        assert json.loads(result)["found"] is False
    def test_read_contact_is_registered_as_tool(self):
        """read_contact doit être exposé au LLM dans MEMORY_TOOLS."""
        from app.services.memory_tools import MEMORY_TOOLS

        names = {t["function"]["name"] for t in MEMORY_TOOLS}
        assert "read_contact" in names


class TestQW_CRMNotesAndGet:
    """Le POST CRM doit persister notes/address/tags, et la fiche se relire par id."""
    @pytest.mark.asyncio
    async def test_crm_create_persists_notes(self, client):
        """QW1 : la note métier envoyée à la création doit être stockée et relue."""
        note = "Cherche un T3 sous 250k, tensions sur le prix"
        resp = await client.post(
            "/api/crm/contacts",
            json={"first_name": "Karim", "company": "ABC", "notes": note},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["notes"] == note, "La note ne doit plus être jetée"
        cid = resp.json()["id"]

        got = await client.get(f"/api/crm/contacts/{cid}")
        assert got.status_code == 200, got.text
        body = got.json()
        assert body["notes"] == note
        assert body["score"] is not None, "QW3 : le score doit être hydraté"
        assert body["stage"] == "contact"
    @pytest.mark.asyncio
    async def test_crm_get_contact_404(self, client):
        """QW3 : la route CRM par id existe et renvoie 404 si introuvable."""
        got = await client.get("/api/crm/contacts/inexistant-123")
        assert got.status_code == 404


class TestQW_PromptHardening:
    """QW2/QW4 : anti-hallu calendrier + distinction stockage/traitement."""
    def test_prompt_distinguishes_storage_vs_treatment(self):
        """QW4 : le prompt distingue stockage local et traitement cloud."""
        from app.services.llm import LLMService

        prompt = LLMService()._get_system_prompt_with_identity()
        assert "Distingue TOUJOURS deux couches" in prompt
        # Interdit explicitement la surpromesse observée au 2e passage
        assert "même pas pour traitement" in prompt
    def test_prompt_has_data_honesty_block(self):
        """QW2 : bloc anti-invention quand un outil renvoie un vide/une absence."""
        from app.services.llm import LLMService

        prompt = LLMService()._get_system_prompt_with_identity()
        assert "anti-invention" in prompt.lower()
        assert "N'invente JAMAIS d'événement" in prompt


class TestQW_GenerateDocumentTool:
    """Le LLM doit pouvoir générer un vrai fichier Office via un outil."""
    def test_generate_document_registered(self):
        """L'outil generate_document est exposé aux providers."""
        from app.services.workspace_tools import WORKSPACE_TOOL_NAMES, WORKSPACE_TOOLS

        assert "generate_document" in WORKSPACE_TOOL_NAMES
        names = {t["function"]["name"] for t in WORKSPACE_TOOLS}
        assert "generate_document" in names
    @pytest.mark.asyncio
    async def test_generate_document_produces_real_link(self, db_session, monkeypatch):
        """L'outil exécute le bon skill et annonce le fichier généré.

        BUG-173 (25/08) : le retour ne contient PLUS l'URL - le modèle la
        recopiait en lien markdown, mort en navigateur externe
        (tauri.localhost). La carte native est LE chemin de téléchargement.
        """
        from unittest.mock import AsyncMock, MagicMock

        import app.services.skills as skills_mod
        from app.services.workspace_tools import execute_workspace_tool

        fake_resp = MagicMock(
            success=True,
            file_name="rapport_ab12.docx",
            download_url="/api/skills/download/ab12",
            error=None,
        )
        fake_registry = MagicMock()
        fake_registry.execute = AsyncMock(return_value=fake_resp)
        monkeypatch.setattr(skills_mod, "get_skills_registry", lambda: fake_registry)

        result = await execute_workspace_tool(
            "generate_document",
            {"format": "docx", "title": "Rapport", "content": "# Titre\nContenu"},
            db_session,
        )

        assert "rapport_ab12.docx" in result
        assert "/api/skills/download" not in result, (
            "BUG-173 : une URL dans le texte devient un lien markdown mort"
        )
        assert "carte" in result
        assert fake_registry.execute.await_args[0][0] == "docx-pro"
    @pytest.mark.asyncio
    async def test_generate_document_rejects_empty_content(self, db_session):
        """Pas de contenu -> message clair, pas de génération fantôme."""
        from app.services.workspace_tools import execute_workspace_tool

        result = await execute_workspace_tool(
            "generate_document", {"format": "docx", "content": "   "}, db_session
        )
        assert "aucun contenu" in result.lower()


class TestBUG133_ChatCalendarLocalFallback:
    """Le calendrier du chat retombe sur le local sans compte Google (BUG-133).

    Avant : `_get_calendar_provider` ne cherchait qu'un compte gmail et renvoyait
    « Aucun compte Google connecte. Le calendrier necessite un compte Gmail »,
    masquant le calendrier local souverain.
    """
    @pytest.mark.asyncio
    async def test_get_calendar_provider_repli_local(self, db_session):
        """Sans compte Google, on obtient le provider LOCAL et un vrai id (pas 'primary')."""
        from app.services.calendar.local_provider import LocalCalendarProvider
        from app.services.workspace_tools import _get_calendar_provider

        provider, cal_id, error = await _get_calendar_provider(
            db_session, auto_create_local=True
        )
        assert error is None
        assert isinstance(provider, LocalCalendarProvider)
        assert cal_id and cal_id != "primary"
    @pytest.mark.asyncio
    async def test_lecture_sans_calendrier_message_honnete(self, db_session):
        """Lecture sans aucun calendrier : message honnête proposant le local,
        sans prétendre que Gmail est obligatoire."""
        from app.services.workspace_tools import _get_calendar_provider

        provider, cal_id, error = await _get_calendar_provider(db_session)
        assert provider is None and cal_id is None
        assert error is not None
        assert "local" in error.lower()
        assert "necessite un compte gmail" not in error.lower()
    @pytest.mark.asyncio
    async def test_create_event_sans_google_utilise_le_calendrier_local(self, db_session):
        """Créer un événement depuis le chat amorce et utilise le calendrier local."""
        from app.models.entities import Calendar
        from app.services.workspace_tools import execute_workspace_tool
        from sqlalchemy import select

        result = await execute_workspace_tool(
            "create_calendar_event",
            {
                "summary": "Point hebdo",
                "start": "2026-07-13T09:00:00",
                "end": "2026-07-13T10:00:00",
            },
            db_session,
        )

        assert "compte Google" not in result
        assert "cree" in result.lower() or "créé" in result.lower()

        cals = (
            await db_session.execute(select(Calendar).where(Calendar.provider == "local"))
        ).scalars().all()
        assert len(cals) >= 1


class TestGmailChatProviderRegression:
    """Branche gmail de _get_calendar_provider / _get_email_provider.

    ensure_valid_access_token renvoie le token DÉCHIFFRÉ (str). Le code
    réassignait `account` à ce token puis lisait `account.access_token`
    (AttributeError sur str) : outils chat email + calendrier cassés pour tout
    compte Google. Révélé par la revue adversariale de BUG-133 (branche gmail
    sans couverture de test). Verrou de non-régression.
    """
    @pytest.mark.asyncio
    async def test_calendar_provider_gmail_construit_sans_attribute_error(
        self, db_session, monkeypatch
    ):
        from app.models.entities import EmailAccount
        from app.services import workspace_tools
        from app.services.calendar.google_provider import GoogleCalendarProvider

        db_session.add(
            EmailAccount(email="g@gmail.com", provider="gmail", access_token="enc")
        )
        await db_session.commit()

        async def fake_ensure(account, session):
            # renvoie un token déjà déchiffré, comme la vraie fonction
            return "ya29.token-en-clair"

        monkeypatch.setattr("app.routers.email.ensure_valid_access_token", fake_ensure)

        provider, cal_id, error = await workspace_tools._get_calendar_provider(db_session)
        assert error is None
        assert cal_id == "primary"
        assert isinstance(provider, GoogleCalendarProvider)
    @pytest.mark.asyncio
    async def test_email_provider_gmail_construit_sans_attribute_error(
        self, db_session, monkeypatch
    ):
        from app.models.entities import EmailAccount
        from app.services import workspace_tools
        from app.services.email.gmail_provider import GmailProvider

        db_session.add(
            EmailAccount(email="g2@gmail.com", provider="gmail", access_token="enc")
        )
        await db_session.commit()

        async def fake_ensure(account, session):
            return "ya29.token-en-clair"

        monkeypatch.setattr("app.routers.email.ensure_valid_access_token", fake_ensure)

        provider, error = await workspace_tools._get_email_provider(db_session)
        assert error is None
        assert isinstance(provider, GmailProvider)


class TestRAG_LegalCorpus:
    """Le corpus juridique vérifié doit être chargé, cherché et injecté."""
    def test_corpus_loads_verified_entries(self):
        """Le corpus existe et ne contient que des entrées sourcées (Légifrance/service-public)."""
        from app.services.legal_corpus import _load_corpus

        entries = _load_corpus()
        assert len(entries) >= 10
        for e in entries:
            assert e.get("reference")
            url = e.get("source_url", "")
            assert "legifrance" in url or "service-public" in url
    def test_corpus_summaries_do_not_contain_tool_markup(self):
        """Une trace de tool calling ne doit jamais atteindre le contexte juridique."""
        from app.services.legal_corpus import _load_corpus

        for entry in _load_corpus():
            summary = entry.get("summary", "")
            assert "</summary>" not in summary
            assert "</invoke>" not in summary
    def test_lookup_late_payment_points_to_current_article(self):
        """'pénalités de retard' doit pointer L441-10 (et pas l'ancien L441-6)."""
        from app.services.legal_corpus import lookup_legal

        matches = lookup_legal(
            "Rédige une clause de pénalités de retard de paiement pour ma facture entre professionnels."
        )
        assert matches
        refs = " ".join(m["reference"] for m in matches)
        assert "L441-10" in refs
        assert "L441-6 " not in refs and "L441-6," not in refs
    def test_lookup_moral_interests_article(self):
        """'intérêts moratoires' doit retrouver l'article 1231-6 du Code civil (finding avocate)."""
        from app.services.legal_corpus import lookup_legal

        matches = lookup_legal("Quels sont les intérêts moratoires en cas de retard de paiement ?")
        refs = " ".join(m["reference"] for m in matches)
        assert "1231-6" in refs
    def test_lookup_no_match_returns_empty(self):
        """Aucun sujet juridique -> pas d'injection."""
        from app.services.legal_corpus import lookup_legal

        assert lookup_legal("Quelle est la météo à Manosque aujourd'hui ?") == []
    def test_format_legal_context_has_guardrail(self):
        """Le contexte formaté impose d'utiliser ces refs + [à confirmer] pour le reste."""
        from app.services.legal_corpus import get_legal_context

        ctx = get_legal_context("franchise en base de TVA mention sur facture")
        assert "VÉRIFIÉES" in ctx
        assert "à confirmer sur Légifrance" in ctx
        assert "293 B" in ctx
    @pytest.mark.asyncio
    async def test_memory_context_injects_legal_without_memory(self):
        """_get_memory_context injecte les réfs légales même sans résultat mémoire."""
        from app.routers.chat import _get_memory_context

        ctx = await _get_memory_context(
            "clause de pénalités de retard de paiement entre professionnels"
        )
        assert ctx is not None
        assert "L441-10" in ctx
        assert "VÉRIFIÉES" in ctx


class TestGlobal_Fixes:
    """Corrections issues du test exhaustif des fonctionnalités."""
    def _render_invoice_pdf(self, tmp_path, currency: str) -> str:
        """Rend un PDF de facture minimal dans la devise donnée, renvoie le texte extrait."""
        from app.services.invoice_pdf import InvoicePDFGenerator
        from pypdf import PdfReader

        gen = InvoicePDFGenerator(output_dir=str(tmp_path))
        invoice_data = {
            "invoice_number": f"FACT-2026-TEST-{currency}",
            "document_type": "facture",
            "tva_applicable": True,
            "validite_jours": 30,
            "issue_date": "2026-06-06T00:00:00",
            "due_date": "2026-07-06T00:00:00",
            "status": "draft",
            "subtotal_ht": 100.0,
            "total_tax": 20.0,
            "total_ttc": 120.0,
            "notes": "",
            "lines": [{
                "description": "Conseil",
                "quantity": 1,
                "unit_price_ht": 100.0,
                "tva_rate": 20.0,
                "total_ht": 100.0,
                "total_ttc": 120.0,
            }],
        }
        contact_data = {"name": "Client QC", "company": "", "email": "", "phone": "", "address": ""}
        profile = {
            "name": "Camille Exemple", "company": "Exemple SARL",
            "address": "Manosque", "siren": "", "siret": "12345678900010",
            "code_ape": "", "tva_intra": "",
        }
        path = gen.generate_invoice_pdf(
            invoice_data=invoice_data, contact_data=contact_data,
            user_profile=profile, currency=currency,
        )
        text = "".join(page.extract_text() for page in PdfReader(path).pages)
        return "".join(text.split()).lower()  # sans espaces pour robustesse extraction
    def test_legal_lookup_accent_insensitive(self):
        """Le matching juridique doit ignorer les accents (intérêts, commerçants...)."""
        from app.services.legal_corpus import lookup_legal

        assert lookup_legal("Quels sont les intérêts moratoires entre commerçants ?"), (
            "Une requête accentuée doit matcher le corpus"
        )
        refs = " ".join(x["reference"] for x in lookup_legal("clause de pénalités de retard"))
        assert "L441-10" in refs
    @pytest.mark.asyncio
    async def test_validation_422_exposes_field(self, client):
        """Hors debug, la 422 doit indiquer le champ manquant (details non vide)."""
        resp = await client.post("/api/crm/contacts", json={})
        assert resp.status_code == 422, resp.text
        details = resp.json().get("details", [])
        assert details, "details ne doit plus être vide"
        assert any("first_name" in d.get("field", "") for d in details)
    def test_legal_mentions_gated_on_currency(self):
        """Les mentions FR (40 EUR, L441-10) ne sortent qu'en EUR, pas en devise étrangère."""
        from app.routers.invoices import generate_legal_mentions

        eur = generate_legal_mentions(due_date_str="06/06/2026", currency="EUR")
        assert "40 EUR" in eur and "L441-10" in eur

        cad = generate_legal_mentions(due_date_str="06/06/2026", currency="CAD")
        assert "40 EUR" not in cad and "L441-10" not in cad
        # Une ligne générique reste présente (pas de vide juridique).
        assert "retard de paiement" in cad
    def test_pdf_drops_french_indemnity_for_foreign_currency(self, tmp_path):
        """Le PDF (vrai livrable) ne doit PAS imprimer l'indemnité FR (40 / L441,
        'frais de recouvrement') sur une facture en devise étrangère (CAD)."""
        cad = self._render_invoice_pdf(tmp_path, "CAD")
        assert "recouvrement" not in cad, "L'indemnité FR (frais de recouvrement) ne doit pas figurer en CAD"
        assert "tauxlegal" not in cad, "La pénalité 'au taux légal' (droit FR) ne doit pas figurer en CAD"
        assert "convenues" in cad, "Une ligne neutre doit prendre le relais en devise étrangère"
    def test_pdf_keeps_french_indemnity_in_eur(self, tmp_path):
        """Régression inverse : en EUR, l'indemnité forfaitaire FR reste bien présente."""
        eur = self._render_invoice_pdf(tmp_path, "EUR")
        assert "recouvrement" in eur, "En EUR, l'indemnité forfaitaire (frais de recouvrement) doit rester"
    def test_collection_routes_have_no_slash_variant(self):
        """invoices/tasks : routes collection exposées sans slash final (anti-redirection 307)."""
        from app.main import app

        paths = {getattr(r, "path", None) for r in app.routes}
        # Avant le fix, seuls "/api/invoices/" et "/api/tasks/" existaient -> 307.
        assert "/api/invoices" in paths and "/api/invoices/" in paths
        assert "/api/tasks" in paths and "/api/tasks/" in paths
    @pytest.mark.asyncio
    async def test_available_models_symmetric_for_cloud_provider(self):
        """_available_models_for renvoie la liste complète (source unique GET/POST)."""
        from app.routers.config import _available_models_for

        models = await _available_models_for("anthropic")
        # Le POST renvoyait avant une liste vide pour les providers cloud.
        assert len(models) >= 3
        assert "claude-opus-4-8" in models
    def test_board_profile_brief_omits_legal_identity(self):
        """format_brief (Board) garde le nom/métier mais retire SIRET/TVA/NDA."""
        from app.services.user_profile import UserProfile

        profile = UserProfile(
            name="Claire Fontaine",
            role="consultante-formatrice",
            siret="123 456 789 00010",
            nda="11223344556",
            tva_intra="FR00123456789",
        )
        brief = profile.format_brief()
        assert "Claire Fontaine" in brief
        assert "123 456 789 00010" not in brief
        assert "11223344556" not in brief
        # Le format complet, lui, doit toujours porter l'identité légale (anti-hallu chat).
        assert "123 456 789 00010" in profile.format_for_llm()
    @pytest.mark.asyncio
    async def test_quick_add_local_returns_clear_error(self, client):
        """Quick-add sans compte Google : 400 explicite (plus de 404 'Account not found')."""
        resp = await client.post(
            "/api/calendar/events/quick-add",
            json={"text": "Déjeuner demain à 12h30", "calendar_id": "local-cal"},
        )
        assert resp.status_code == 400, resp.text
        assert "Google" in resp.json().get("message", "") + resp.text


class TestMistralToolLoop:
    """Mistral : boucle d'outils réparée (NO-GO Syn 0.20.0).

    Avant : tout appel d'outil renvoyait une réponse VIDE (le done annonçait
    'end_turn' au lieu de 'tool_calls' donc l'outil n'était jamais exécuté, et
    continue_with_tool_results était un stub).
    """
    def _provider(self, lines):
        from app.services.llm import LLMConfig, LLMProvider
        from app.services.providers.mistral import MistralProvider

        class _Resp:
            def raise_for_status(self):
                return None

            async def aiter_lines(self):
                for ln in lines:
                    yield ln

        class _Ctx:
            async def __aenter__(self):
                return _Resp()

            async def __aexit__(self, *a):
                return False

        class _Client:
            def stream(self, *a, **k):
                return _Ctx()

        config = LLMConfig(provider=LLMProvider.MISTRAL, model="mistral-large-latest", api_key="x")
        return MistralProvider(config, _Client())
    @pytest.mark.asyncio
    async def test_stream_emits_tool_call_and_tool_calls_stop_reason(self):
        """Un tool_call streamé en fragments est reconstruit, avec done(stop_reason=tool_calls)."""
        import json

        def sse(obj):
            return "data: " + json.dumps(obj)

        lines = [
            sse({"choices": [{"delta": {"tool_calls": [
                {"index": 0, "id": "call_1", "function": {"name": "read_contact", "arguments": '{"na'}}
            ]}}]}),
            sse({"choices": [{"delta": {"tool_calls": [
                {"index": 0, "function": {"arguments": 'me":"Dupont"}'}}
            ]}}]}),
            sse({"choices": [{"delta": {}, "finish_reason": "tool_calls"}]}),
            "data: [DONE]",
        ]
        provider = self._provider(lines)
        events = [
            e async for e in provider.stream(
                None, [{"role": "user", "content": "qui est Dupont ?"}], tools=[{"type": "function"}]
            )
        ]
        tool_calls = [e for e in events if e.type == "tool_call"]
        assert len(tool_calls) == 1
        assert tool_calls[0].tool_call.name == "read_contact"
        assert tool_calls[0].tool_call.arguments == {"name": "Dupont"}
        dones = [e for e in events if e.type == "done"]
        assert any(e.stop_reason == "tool_calls" for e in dones), (
            "done doit signaler tool_calls pour déclencher l'exécution + la continuation"
        )
    @pytest.mark.asyncio
    async def test_continue_with_tool_results_appends_messages_and_restreams(self):
        """continue_with_tool_results n'est plus un stub : il renvoie les résultats et re-stream."""
        from app.services.providers.base import StreamEvent, ToolCall, ToolResult

        provider = self._provider([])
        captured = {}

        async def fake_stream(system_prompt, messages, tools=None):
            captured["messages"] = messages
            yield StreamEvent(type="text", content="Dupont travaille chez ACME.")

        provider.stream = fake_stream

        events = [
            e async for e in provider.continue_with_tool_results(
                system_prompt=None,
                messages=[{"role": "user", "content": "qui est Dupont ?"}],
                assistant_content="",
                tool_calls=[ToolCall(id="call_1", name="read_contact", arguments={"name": "Dupont"})],
                tool_results=[ToolResult(tool_call_id="call_1", result={"company": "ACME"})],
            )
        ]

        # Re-stream effectif (plus de réponse vide)
        assert any(e.type == "text" and "ACME" in (e.content or "") for e in events)
        msgs = captured["messages"]
        assistant = [m for m in msgs if m["role"] == "assistant" and m.get("tool_calls")]
        assert assistant, "le message assistant portant les tool_calls doit être ajouté"
        assert assistant[0]["tool_calls"][0]["function"]["name"] == "read_contact"
        tool_msgs = [m for m in msgs if m["role"] == "tool"]
        assert tool_msgs and tool_msgs[0]["tool_call_id"] == "call_1"
        assert "ACME" in tool_msgs[0]["content"]


class TestSovereigntyHonesty:
    """Souveraineté : le bloc doit dire la VÉRITÉ sur le chiffrement.

    Histoire de ce test, à ne pas rejouer à l'envers. En 0.20.0, la base
    n'était pas chiffrée et une revue (NO-GO Syn) a exigé qu'on cesse de le
    prétendre : le test imposait alors la phrase « n'est PAS chiffrée au
    repos ». Puis US-014 a livré SQLCipher (AES-256) — et ni le prompt ni ce
    test ne l'ont su. Le produit a donc passé plusieurs versions à ORDONNER à
    son assistante d'affirmer une contre-vérité sur sa propre sécurité, avec un
    test vert pour la garantir. Trouvé par la campagne dix personas du 28/08,
    quand un médecin a posé la question.

    Inversé en 0.54.0 : le test exige désormais la vérité. Les deux moitiés
    comptent — dire que la base est chiffrée, ET rester honnête sur ce qui ne
    l'est pas, sinon on remplace un mensonge par un autre.
    """
    def test_le_prompt_dit_que_la_base_est_chiffree(self):
        from app.services.llm import LLMService

        block = LLMService.SOVEREIGNTY_BLOCK
        assert "n'est PAS chiffrée au repos" not in block, (
            "la base EST chiffrée depuis US-014 (SQLCipher AES-256) : "
            "ne plus ordonner au modèle d'affirmer le contraire"
        )
        assert "SQLCipher" in block and "AES-256" in block
    def test_le_prompt_reste_honnete_sur_ce_qui_n_est_pas_chiffre(self):
        """Dire « tout est chiffré » serait le mensonge symétrique."""
        from app.services.llm import LLMService

        block = LLMService.SOVEREIGNTY_BLOCK
        # L'index vectoriel garde le texte en clair (payloads Qdrant).
        assert "Qdrant" in block and "clair" in block
        # Les secrets : Fernet AES-128, pas AES-256.
        assert "AES-128" in block and "clés API" in block
    def test_le_prompt_ne_promet_pas_que_rien_ne_sort_avec_un_modele_local(self):
        """Le mensonge jumeau, relevé par la relecture de design.

        Même avec Ollama, deux sorties partent sans que l'utilisateur les
        demande : la vérification de mise à jour (vers synoptia.fr) et le
        téléchargement du modèle d'embeddings au démarrage. Et `web_search`
        part sur simple décision du modèle, sans confirmation, tant que le lot
        A-mécanique n'est pas livré.
        """
        from app.services.llm import LLMService

        block = LLMService.SOVEREIGNTY_BLOCK
        assert "rien ne sort" not in block, (
            "faux : mise à jour, téléchargement de modèles et recherche web "
            "sortent même avec un modèle local"
        )


class TestChatNonStreamP1:
    """Régressions P1 du chemin chat NON-STREAM (rapport Syn 14/06/2026) :
    - le filtre anti-injection n'etait applique qu'en streaming (injection + exfiltration
      du system prompt possibles en stream=false) ;
    - le token tracker n'etait pas alimente et tokens_in/out remontaient null en non-stream."""
    CHAT_PY = SRC / "app" / "routers" / "chat.py"
    def _nonstream_branch(self) -> str:
        content = self.CHAT_PY.read_text(encoding="utf-8")
        start = content.find("Non-streaming response using LLM service")
        assert start > 0, "la branche non-stream doit exister dans send_message"
        end = content.find("async def _stream_response", start)
        return content[start:end if end > 0 else start + 4000]
    def test_nonstream_applies_prompt_safety(self):
        branch = self._nonstream_branch()
        assert "check_prompt_safety" in branch, (
            "le filtre anti-injection doit etre applique sur le chemin non-stream "
            "(et plus seulement dans _stream_response)"
        )
    def test_nonstream_tracks_tokens(self):
        branch = self._nonstream_branch()
        assert "record_usage" in branch, (
            "le chemin non-stream doit alimenter le token tracker (BUG-027)"
        )
        assert "tokens_in=input_tokens" in branch and "tokens_out=output_tokens" in branch, (
            "Message et ChatResponse non-stream doivent porter tokens_in/tokens_out"
        )
    def test_nonstream_prefere_usage_reel_a_l_estimation(self):
        """Dette 14/06/2026 : le chemin non-stream doit utiliser l'usage réel du
        provider (usage_sink) quand disponible, pas seulement l'estimation."""
        branch = self._nonstream_branch()
        assert "usage_sink=usage_sink" in branch, (
            "stream_response doit recevoir usage_sink pour capter l'usage réel"
        )
        assert 'usage_sink.get("input_tokens")' in branch and 'usage_sink.get("output_tokens")' in branch, (
            "input_tokens/output_tokens doivent primer sur l'estimation quand usage_sink est rempli"
        )


class TestEscalationZeroDivision:
    """Régression : des limites a 0 (POST /escalation/limits) provoquaient une
    ZeroDivisionError -> 500 sur /usage/daily, /usage/monthly, /status, /check-limits
    (rapport Syn 14/06). Double defense : validation Pydantic gt=0 + guards token_tracker."""
    def test_token_tracker_guards_zero_limits(self):
        from app.services.token_tracker import TokenLimits, TokenTracker

        t = TokenTracker()
        t.set_limits(TokenLimits(daily_input_limit=0, daily_output_limit=0, monthly_budget_eur=0.0))
        daily = t.get_daily_usage()
        assert daily["input_usage_pct"] == 0.0
        assert daily["output_usage_pct"] == 0.0
        assert t.get_monthly_usage()["budget_usage_pct"] == 0.0
    def test_limits_request_rejects_zero(self):
        import pytest
        from app.models.schemas_escalation import TokenLimitsRequest
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            TokenLimitsRequest(daily_input_limit=0)
        with pytest.raises(ValidationError):
            TokenLimitsRequest(monthly_budget_eur=0.0)


class TestInstalledToolMarkdownPrompt:
    """Régression : InstalledToolSkill n'avait pas get_markdown_prompt_addition() ->
    POST /api/skills/execute/tool:{id} plantait en 500 (AttributeError) avec un modele
    non code-capable comme Gemini (provider par defaut). (rapport Syn 14/06)"""
    def test_installed_tool_has_markdown_prompt_addition(self):
        from app.services.skills.installed_tool import InstalledToolSkill

        assert hasattr(InstalledToolSkill, "get_markdown_prompt_addition"), (
            "InstalledToolSkill doit exposer get_markdown_prompt_addition (appelee par "
            "skills.py quand la capacite du modele n'est pas 'code')"
        )


class TestOAuthRedirectPort:
    """Régression : oauth.py utilisait RUNTIME_PORT = THERESE_PORT ou "8000" par défaut.
    Quand le sidecar Tauri n'exporte pas THERESE_PORT (dev/desktop), les redirect_uri OAuth
    pointaient sur :8000 alors que le backend écoute sur settings.port (17293) -> Google
    rejetait le redirect_uri (mismatch whitelist). (rapport Syn 14/06).
    Fix : fallback sur settings.port au lieu de "8000"."""
    def test_runtime_port_defaults_to_settings_port_not_8000(self):
        import os

        # Sans THERESE_PORT exporté, le défaut doit être settings.port, pas 8000.
        # (le module est déjà importé sans THERESE_PORT dans l'environnement de test)
        if "THERESE_PORT" in os.environ:
            import pytest
            pytest.skip("THERESE_PORT exporté dans l'env de test, cas couvert ailleurs")

        from app.config import settings
        from app.services.oauth import RUNTIME_PORT

        assert str(settings.port) == RUNTIME_PORT
        assert RUNTIME_PORT != "8000"
    def test_allowed_redirect_uris_use_runtime_port(self):
        from app.services.oauth import ALLOWED_REDIRECT_URIS, RUNTIME_PORT

        assert ALLOWED_REDIRECT_URIS, "la whitelist ne doit pas être vide"
        # Toutes les URIs autorisées portent le port runtime, aucune ne reste sur 8000.
        for uri in ALLOWED_REDIRECT_URIS:
            assert f":{RUNTIME_PORT}/" in uri, f"{uri} devrait porter le port {RUNTIME_PORT}"
            assert ":8000/" not in uri, f"{uri} ne doit plus pointer sur :8000"


class TestStreamResponseRaiseOnError:
    """Régression : stream_response (wrapper texte) avalait silencieusement un
    StreamEvent(type="error") d'un provider. En non-stream, assistant_content
    restait vide -> message assistant VIDE renvoyé au lieu d'une erreur (rapport
    Syn 14/06). Fix : flag opt-in raise_on_error (défaut False = compat appelants
    existants ; chat.py non-stream passe True)."""
    @staticmethod
    def _fake_self_yielding(*events):
        from app.services.llm import LLMService

        class _FakeLLM:
            async def stream_response_with_tools(self, context, tools=None, enable_grounding=True):
                for ev in events:
                    yield ev

        # On appelle le wrapper réel de LLMService avec un self minimal : il
        # n'utilise que self.stream_response_with_tools.
        fake = _FakeLLM()
        return lambda **kw: LLMService.stream_response(fake, context=None, **kw)
    async def _collect(self, gen):
        return [chunk async for chunk in gen]
    def test_default_swallows_error_event(self):
        import asyncio

        from app.services.providers.base import StreamEvent

        call = self._fake_self_yielding(
            StreamEvent(type="text", content="bonjour"),
            StreamEvent(type="error", content="boom provider"),
        )
        # Défaut raise_on_error=False : l'erreur est avalée, on garde le texte.
        chunks = asyncio.get_event_loop().run_until_complete(self._collect(call()))
        assert chunks == ["bonjour"]
    def test_raise_on_error_propagates(self):
        import asyncio

        import pytest
        from app.services.providers.base import StreamEvent

        call = self._fake_self_yielding(
            StreamEvent(type="error", content="boom provider"),
        )
        with pytest.raises(RuntimeError, match="boom provider"):
            asyncio.get_event_loop().run_until_complete(self._collect(call(raise_on_error=True)))


class TestMCPToolCallServerId:
    """Régression : /api/mcp/tools/call ne respectait pas un server_id explicite.
    Deux serveurs MCP exposant un outil de même nom -> la recherche linéaire renvoyait
    le PREMIER trouvé (mauvais serveur). Rapport Syn 14/06. Fix : champ server_id
    optionnel sur MCPToolCall + routage prioritaire dans l'endpoint."""
    def test_schema_accepts_server_id(self):
        from app.models.schemas_mcp import MCPToolCall

        call = MCPToolCall(tool_name="search", arguments={}, server_id="srv-b")
        assert call.server_id == "srv-b"
        # Rétrocompat : sans server_id -> None (ancien comportement préservé).
        assert MCPToolCall(tool_name="search").server_id is None
    async def test_endpoint_routes_to_explicit_server(self, monkeypatch):
        from types import SimpleNamespace

        from app.models.schemas_mcp import MCPToolCall
        from app.routers import mcp as mcp_router

        called = {}

        def _tool(name, server_id):
            return SimpleNamespace(name=name, server_id=server_id)

        srv_a = SimpleNamespace(id="srv-a", tools=[_tool("search", "srv-a")])
        srv_b = SimpleNamespace(id="srv-b", tools=[_tool("search", "srv-b")])

        class _FakeService:
            servers = {"srv-a": srv_a, "srv-b": srv_b}

            def get_all_tools(self):
                return srv_a.tools + srv_b.tools  # srv-a listé en premier

            async def call_tool(self, server_id, tool_name, arguments):
                called["server_id"] = server_id
                return SimpleNamespace(
                    tool_name=tool_name, server_id=server_id, success=True,
                    result={}, error=None, execution_time_ms=1.0,
                )

            async def execute_tool_call(self, name, args):
                raise AssertionError("ne doit pas passer par la branche nom qualifié")

        monkeypatch.setattr(mcp_router, "get_mcp_service", lambda: _FakeService())

        # server_id explicite -> srv-b, et NON srv-a (le premier homonyme).
        await mcp_router.call_tool(MCPToolCall(tool_name="search", server_id="srv-b"))
        assert called["server_id"] == "srv-b"
    async def test_endpoint_unknown_server_raises_404(self, monkeypatch):
        import pytest
        from app.models.schemas_mcp import MCPToolCall
        from app.routers import mcp as mcp_router
        from fastapi import HTTPException

        class _FakeService:
            servers: dict = {}

            def get_all_tools(self):
                return []

            async def call_tool(self, *a, **k):
                raise AssertionError("ne doit pas être appelé pour un serveur inconnu")

        monkeypatch.setattr(mcp_router, "get_mcp_service", lambda: _FakeService())

        with pytest.raises(HTTPException) as exc:
            await mcp_router.call_tool(MCPToolCall(tool_name="search", server_id="ghost"))
        assert exc.value.status_code == 404


class TestBoardTokenTracking:
    """Régression BUG-027 (volet board) : les délibérations du board faisaient de vrais
    appels LLM sans jamais alimenter le token tracker -> usage quotidien/mensuel
    sous-compté (rapport Syn 14/06). Fix : BoardService._track_usage aux 3 points de
    génération (conseiller souverain, conseiller cloud, synthèse)."""
    def test_board_has_track_usage(self):
        from app.services.board import BoardService

        assert hasattr(BoardService, "_track_usage")
    def test_track_usage_feeds_token_tracker(self):
        from types import SimpleNamespace

        from app.services.board import BoardService
        from app.services.token_tracker import get_token_tracker

        tracker = get_token_tracker()
        before = tracker.get_daily_usage()

        fake_llm = SimpleNamespace(
            config=SimpleNamespace(model="claude-sonnet-4-6", provider=SimpleNamespace(value="anthropic"))
        )
        # BoardService accepte une session optionnelle (None ici, _track_usage ne l'utilise pas).
        board = BoardService(session=None)
        board._track_usage(fake_llm, "un deux trois quatre", "cinq six")

        after = tracker.get_daily_usage()
        # 4 mots d'entrée * 2 = 8 tokens in, 2 mots * 2 = 4 tokens out.
        assert after["input_tokens"] == before["input_tokens"] + 8
        assert after["output_tokens"] == before["output_tokens"] + 4
    def test_track_usage_prefere_usage_sink_a_l_estimation(self):
        """Dette 14/06/2026 : quand le provider a fourni l'usage réel
        (usage_sink, cf llm.py stream_response), il doit primer sur
        l'estimation ~2 tokens/mot, même si le texte est court."""
        from types import SimpleNamespace

        from app.services.board import BoardService
        from app.services.token_tracker import get_token_tracker

        tracker = get_token_tracker()
        before = tracker.get_daily_usage()

        fake_llm = SimpleNamespace(
            config=SimpleNamespace(model="claude-sonnet-4-6", provider=SimpleNamespace(value="anthropic"))
        )
        board = BoardService(session=None)
        board._track_usage(fake_llm, "un", "deux", usage_sink={"input_tokens": 123, "output_tokens": 45})

        after = tracker.get_daily_usage()
        assert after["input_tokens"] == before["input_tokens"] + 123
        assert after["output_tokens"] == before["output_tokens"] + 45


class TestDeepResearchSurfacesSynthesisError:
    """Régression : la synthèse deep-research avalait les erreurs provider (ex Gemini
    400 tool_config) -> rapport "done" VIDE silencieux (rapport Syn 14/06). Fix :
    raise_on_error sur le stream de synthèse + remontée en ResearchProgress type='error'.
    Le mécanisme raise_on_error est prouvé fonctionnellement dans
    TestStreamResponseRaiseOnError ; ici on vérifie son câblage côté synthèse."""
    DR_PY = SRC / "app" / "services" / "deep_research.py"
    def _synthesis_section(self) -> str:
        content = self.DR_PY.read_text(encoding="utf-8")
        start = content.find("Étape 3")
        assert start > 0, "la section synthèse (Étape 3) doit exister"
        return content[start:]
    def test_synthesis_stream_raises_on_error(self):
        synth = self._synthesis_section()
        assert "raise_on_error=True" in synth, (
            "le stream de synthèse doit passer raise_on_error=True pour ne plus avaler "
            "les erreurs provider"
        )
    def test_synthesis_emits_error_event(self):
        synth = self._synthesis_section()
        assert 'type="error"' in synth, "une erreur de synthèse doit émettre un ResearchProgress type='error'"
        # Panel 0.48 : le message passe par la frontière d'erreurs - plus
        # d'interpolation de str(e) brut dans l'évènement d'écran.
        assert "message_pour_ecran" in synth
        assert "La synthèse a échoué : {e}" not in synth


class TestDocumentsDraftSurfacesProviderErrors:
    """Régression (revue adversariale lot B, finding 4) : verrou source sur
    raise_on_error=True dans la route de rédaction (draft) de l'atelier
    documentaire. Sans ce flag, `LLMService.stream_response` avale
    silencieusement les `StreamEvent(type="error")` du provider - la route
    ne verrait alors jamais d'erreur (juste un stream vide), ce qui casse
    l'exigence "chunk error" du design. Les mocks des tests draft ignorent
    les kwargs, donc sa suppression ne casserait aucun test fonctionnel -
    même précédent exact que TestDeepResearchSurfacesSynthesisError
    ci-dessus, verrouillé ici par assertion sur le code source."""
    DOCUMENTS_PY = SRC / "app" / "routers" / "documents.py"
    def _draft_stream_section(self) -> str:
        content = self.DOCUMENTS_PY.read_text(encoding="utf-8")
        start = content.find("async def _draft_stream")
        assert start > 0, "la fonction _draft_stream doit exister"
        return content[start:]
    def test_draft_stream_raises_on_error(self):
        section = self._draft_stream_section()
        assert "raise_on_error=True" in section, (
            "la route de rédaction (draft) doit passer raise_on_error=True à "
            "stream_response pour ne plus avaler les erreurs provider"
        )


class TestBUGB_CrmSyncChoixFeuille:
    """BUG-B : synchro CRM doit proposer le choix d'une feuille existante avant création automatique.

    À la première connexion Google sans ID de feuille renseigné, le système créait automatiquement
    une feuille vide et synchronisait dessus, résultant en un CRM vide sans explication.
    La solution : proposer de choisir une feuille existante AVANT toute création.
    """
    @pytest.mark.asyncio
    async def test_backend_api_lister_feuilles_google_disponible(self, client):
        """Le backend doit exposer un endpoint pour lister les feuilles Google.

        B-042, deux défauts sur la même ligne. (1) `!= 404` n'avait aucune
        borne haute : un endpoint entièrement cassé, rendu en 500, passait la
        garde qui prétend vérifier qu'il RÉPOND. La plage est désormais
        FERMÉE. (2) Le `TestClient(app)` construit ici n'entre pas dans le
        lifespan : lancé seul, ce test échouait en « Database not initialized »
        et n'était vert que grâce à l'`init_db` laissé par un autre test de la
        suite. On passe par la fixture `client`, qui démarre l'application.
        """
        # Sans compte Google connecté, la réponse attendue est un refus
        # d'authentification, jamais une absence de route ni une panne.
        response = await client.get("/api/crm/google-sheets/list")
        assert response.status_code in (200, 401, 403), (
            "L'endpoint /api/crm/google-sheets/list doit exister ET répondre "
            f"(reçu {response.status_code}) : 404 = absent, 5xx = cassé"
        )
    def test_frontend_interface_choix_feuille_existante(self):
        """L'interface CRMSyncPanel doit permettre de choisir parmi les feuilles existantes."""
        import os
        crm_panel_path = os.path.join(
            os.path.dirname(__file__),
            "..", "src", "frontend", "src", "components", "settings", "CRMSyncPanel.tsx"
        )

        with open(crm_panel_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Doit avoir une fonctionnalité pour lister les feuilles existantes
        has_list_functionality = (
            "list" in content.lower() and
            ("spreadsheet" in content.lower() or "feuille" in content.lower()) and
            ("existing" in content.lower() or "existant" in content.lower() or "choisir" in content.lower())
        )

        assert has_list_functionality, (
            "CRMSyncPanel doit proposer de choisir parmi les feuilles existantes, "
            "pas seulement permettre la saisie manuelle d'un ID"
        )


class TestBUG111_UninstallDeleteData:
    """BUG-111 : la désinstallation Windows avec « supprimer les données » cochée
    ne supprimait pas le dossier de données backend (~/.therese), laissant
    paramétrages et projets en place. Fix : hook NSIS POSTUNINSTALL conditionnel.
    """
    def _src_tauri(self):
        import os
        return os.path.join(
            os.path.dirname(__file__), "..", "src", "frontend", "src-tauri"
        )
    def test_hook_nsis_supprime_dossier_therese(self):
        import os
        hook_path = os.path.join(self._src_tauri(), "installer-hooks.nsh")
        assert os.path.exists(hook_path), (
            "Le hook NSIS installer-hooks.nsh doit exister (BUG-111)"
        )
        with open(hook_path, encoding="utf-8") as f:
            content = f.read()
        assert "NSIS_HOOK_POSTUNINSTALL" in content, (
            "Le hook doit definir la macro NSIS_HOOK_POSTUNINSTALL"
        )
        assert "DeleteAppDataCheckboxState" in content, (
            "Le hook ne doit supprimer que si la case 'supprimer les donnees' est cochee"
        )
        assert ".therese" in content and "RMDir /r" in content, (
            "Le hook doit supprimer recursivement le dossier de donnees ~/.therese"
        )
    def test_tauri_conf_reference_le_hook(self):
        import json
        import os
        conf_path = os.path.join(self._src_tauri(), "tauri.conf.json")
        with open(conf_path, encoding="utf-8") as f:
            conf = json.load(f)
        hooks = (
            conf.get("bundle", {})
            .get("windows", {})
            .get("nsis", {})
            .get("installerHooks")
        )
        assert hooks == "installer-hooks.nsh", (
            "tauri.conf.json doit referencer installer-hooks.nsh "
            "via bundle.windows.nsis.installerHooks"
        )


class TestBUG113_RaccourciBureauLegacyDoublon:
    """BUG-113 : après une MAJ Windows, deux icônes bureau pointent sur la même
    cible. Cause : jusqu'à la v0.1.15 le productName était « THÉRÈSE » (accentué),
    le renommage en « THERESE » (v0.1.16) a laissé l'ancien .lnk orphelin que
    chaque installation recrée à côté. Fix : hook NSIS POSTINSTALL qui purge les
    raccourcis legacy (accentué + bureau commun).
    """
    def _hook_path(self):
        import os
        return os.path.join(
            os.path.dirname(__file__), "..", "src", "frontend", "src-tauri",
            "installer-hooks.nsh",
        )
    def test_hook_postinstall_purge_raccourci_legacy(self):
        with open(self._hook_path(), encoding="utf-8-sig") as f:
            content = f.read()
        assert "NSIS_HOOK_POSTINSTALL" in content, (
            "Le hook doit définir NSIS_HOOK_POSTINSTALL (purge raccourcis legacy)"
        )
        assert 'Delete "$DESKTOP\\THÉRÈSE.lnk"' in content, (
            "Le hook doit supprimer le raccourci legacy accentué THÉRÈSE.lnk"
        )
        assert "SetShellVarContext all" in content and "SetShellVarContext current" in content, (
            "Le hook doit aussi purger le bureau commun puis restaurer le contexte user"
        )
    def test_hook_fichier_utf8_avec_bom(self):
        # makensis lit le .nsh en codepage ANSI sans BOM : les littéraux
        # accentués seraient corrompus et le Delete viserait un mauvais nom.
        with open(self._hook_path(), "rb") as f:
            raw = f.read(3)
        assert raw == b"\xef\xbb\xbf", (
            "installer-hooks.nsh doit être encodé en UTF-8 AVEC BOM "
            "(littéraux accentués dans les macros NSIS)"
        )


class TestBUG180_RaccourciBureauMultiContexte:
    """BUG-180 : une MAJ currentUser ne peut pas toujours supprimer le
    raccourci THERESE.lnk du bureau commun sans élévation. Windows affiche alors
    le raccourci commun et le raccourci utilisateur comme deux icônes.
    """

    def _hook_content(self):
        hook_path = (
            Path(__file__).resolve().parent.parent
            / "src"
            / "frontend"
            / "src-tauri"
            / "installer-hooks.nsh"
        )
        return hook_path.read_text(encoding="utf-8-sig")

    def test_hook_garde_un_seul_raccourci_si_la_purge_commune_est_refusee(self):
        content = self._hook_content()
        common_context = content.index("SetShellVarContext all")
        common_delete = content.index(
            'Delete "$DESKTOP\\THERESE.lnk"', common_context
        )
        target_check = content.index(
            '!insertmacro IsShortcutTarget "$DESKTOP\\THERESE.lnk" '
            '"$INSTDIR\\${MAINBINARYNAME}.exe"',
            common_delete,
        )
        user_context = content.index("SetShellVarContext current", target_check)
        user_delete = content.index(
            'Delete "$DESKTOP\\THERESE.lnk"', user_context
        )

        assert common_context < common_delete < target_check < user_context < user_delete
        assert "Pop $0" in content[target_check:user_context], (
            "Le résultat du contrôle de cible doit alimenter la condition de repli"
        )
        assert "${If} $0 = 1" in content[target_check:user_delete], (
            "Le raccourci utilisateur ne doit être supprimé que si le raccourci "
            "commun restant vise exactement le binaire installé"
        )


class TestVoiceLocalOption:
    """Voix locale souveraine STT/TTS, OPTIONNELLE (faster-whisper + Piper).

    Les dépendances ne sont pas installées par défaut : les tests vérifient la
    structure (modèles + prérequis RAM), la disponibilité, le message clair quand
    c'est indisponible, le groupe pip optionnel et la doc.
    """
    def test_status_structure_et_prerequis_ram(self):
        from app.services.voice_local import WHISPER_MODELS, voice_local_status

        st = voice_local_status()
        for k in ("stt_available", "tts_available", "whisper_models", "tts_ram_mb", "install_hint"):
            assert k in st, f"voice_local_status doit exposer '{k}'"
        # chaque modèle Whisper expose taille disque + prérequis RAM
        assert WHISPER_MODELS, "WHISPER_MODELS ne doit pas être vide"
        for _name, info in WHISPER_MODELS.items():
            assert info.get("ram_mb", 0) > 0, "chaque modèle doit indiquer sa RAM nécessaire"
            assert info.get("size_mb", 0) > 0
        assert st["tts_ram_mb"] > 0
    def test_availability_renvoie_bool(self):
        from app.services.voice_local import stt_available, tts_available

        assert isinstance(stt_available(), bool)
        assert isinstance(tts_available(), bool)
    def test_transcribe_local_leve_erreur_claire_si_indisponible(self):
        import pytest
        from app.services import voice_local

        if voice_local.stt_available():
            pytest.skip("faster-whisper installé localement : cas indisponible non testable")
        with pytest.raises(RuntimeError):
            voice_local.transcribe_local("/tmp/inexistant.wav")
    def test_groupe_optionnel_voice_local_dans_pyproject(self):
        import os

        root = os.path.join(os.path.dirname(__file__), "..")
        with open(os.path.join(root, "pyproject.toml"), encoding="utf-8") as f:
            content = f.read()
        assert "voice-local" in content, "le groupe optionnel voice-local doit exister"
        assert "faster-whisper" in content and "piper-tts" in content
    def test_doc_voice_local_existe_avec_ram(self):
        import os

        root = os.path.join(os.path.dirname(__file__), "..")
        doc = os.path.join(root, "docs", "VOICE-LOCAL.md")
        assert os.path.exists(doc), "docs/VOICE-LOCAL.md doit documenter la voix locale"
        with open(doc, encoding="utf-8") as f:
            content = f.read().lower()
        assert "ram" in content
        assert "faster-whisper" in content and "piper" in content


class TestBUG126_NotificationsNaiveDatetime:
    """BUG-126 : génération de notifications automatiques cassée par des dates naïves.

    Les dates relues depuis SQLite (DateTime sans timezone) sont naïves. Les
    fonctions ``_check_*`` de ``notification_service`` soustrayaient ces valeurs
    à ``datetime.now(UTC)`` (aware) -> ``TypeError: can't subtract offset-naive
    and offset-aware datetimes``. Résultat : aucune notif de retard/inactivité,
    l'erreur étant avalée par le ``try/except`` de ``generate_automatic_notifications``.
    Fix : helper ``_as_aware_utc`` appliqué avant chaque soustraction.
    """
    def test_as_aware_utc_rend_naif_comparable(self):
        from datetime import UTC, datetime

        from app.services.notification_service import _as_aware_utc

        naive = datetime(2020, 1, 1, 12, 0, 0)  # sans tzinfo (comme relu de SQLite)
        aware = _as_aware_utc(naive)
        assert aware.tzinfo is not None
        # Ne doit plus lever en soustrayant à un datetime aware
        assert (datetime.now(UTC) - aware).days > 0
    def test_as_aware_utc_preserve_un_datetime_deja_aware(self):
        from datetime import UTC, datetime

        from app.services.notification_service import _as_aware_utc

        already = datetime(2020, 1, 1, 12, 0, 0, tzinfo=UTC)
        assert _as_aware_utc(already) is already  # inchangé, pas de double conversion
    async def test_check_overdue_invoices_avec_due_date_naive(self, db_session):
        from datetime import datetime

        from app.models.entities import Contact, Invoice
        from app.services.notification_service import _check_overdue_invoices

        contact = Contact(first_name="Client", stage="active")
        db_session.add(contact)
        await db_session.flush()

        # due_date NAÏVE et largement > 30 jours dans le passé (reproduit BUG-126)
        db_session.add(
            Invoice(
                invoice_number="FACT-BUG126-001",
                contact_id=contact.id,
                due_date=datetime(2020, 1, 1, 12, 0, 0),
                status="sent",
                total_ttc=1200.0,
            )
        )
        await db_session.flush()

        # Ne doit pas lever (avant le fix : TypeError sur la soustraction) et créer 1 notif
        count = await _check_overdue_invoices(db_session)
        assert count == 1
    async def test_check_inactive_prospects_avec_date_de_relance_naive(self, db_session):
        from datetime import datetime

        from app.models.entities import Contact
        from app.services.notification_service import _check_inactive_prospects

        # 29/08 : la relance n'est plus deduite de `last_interaction` mais lue
        # dans `next_follow_up`. La GARANTIE de BUG-126 est inchangee : une
        # date naive ne doit pas faire tomber la cloche. Elle porte simplement
        # sur le champ qui declenche desormais la notification.
        db_session.add(
            Contact(
                first_name="Prospect",
                stage="discovery",
                next_follow_up=datetime(2020, 1, 1, 12, 0, 0),  # naif, echu
            )
        )
        await db_session.flush()

        count = await _check_inactive_prospects(db_session)
        assert count == 1
    async def test_check_overdue_tasks_avec_due_date_naive(self, db_session):
        from datetime import datetime

        from app.models.entities import Task
        from app.services.notification_service import _check_overdue_tasks

        db_session.add(
            Task(
                title="Relancer le prospect",
                status="todo",
                due_date=datetime(2020, 1, 1, 12, 0, 0),  # naïf, dans le passé
            )
        )
        await db_session.flush()

        count = await _check_overdue_tasks(db_session)
        assert count == 1


class TestLaPromesseDePermissionsEstVraieSurToutesLesPlateformes:
    """
    Le bloc de souveraineté promettait un fichier de clé « à accès restreint
    (0600) », sans condition.

    Le runner Windows l'a démenti par l'exécution : `os.chmod(f, 0o600)` n'y
    bascule que le bit lecture seule, et le mode se relit `0o666`. La copie de
    secours de la clé n'est donc PAS restreinte sur Windows, et THÉRÈSE
    l'affirmait quand même - à un utilisateur, sur son propre fichier de clé.

    C'est le motif exact que le lot A devait fermer, dans le lot A lui-même.
    Deux tests le rendaient visible depuis longtemps, sur un workflow que
    personne ne regardait.
    """
    def test_le_bloc_ne_promet_pas_0600_sans_condition(self):
        from app.services.llm import LLMService

        SOVEREIGNTY_BLOCK = LLMService.SOVEREIGNTY_BLOCK

        if "0600" not in SOVEREIGNTY_BLOCK:
            return  # la mention a disparu : rien à qualifier
        alentours = SOVEREIGNTY_BLOCK[
            max(0, SOVEREIGNTY_BLOCK.index("0600") - 320) : SOVEREIGNTY_BLOCK.index("0600") + 120
        ].lower()
        assert any(mot in alentours for mot in ("windows", "unix", "macos", "selon")), (
            "0600 est une notion POSIX : sur Windows le fichier se relit 0o666. "
            "La promettre sans nommer la plateforme est faux pour une partie "
            "des testeurs."
        )
