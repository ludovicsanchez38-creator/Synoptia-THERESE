# Gardes textuelles de `tests/test_regression.py` remplacées ou retirées (B-039, B-332, 08/09/2026)

> 458 tests lisaient le texte du code (`read_text`, `inspect.getsource`) et y cherchaient des chaînes :
> un renommage les faisait rougir sans régression, un commentaire suffisait à les satisfaire. Chaque
> ligne dit ce qui remplace la garde. « retirée » signifie qu'aucun test de comportement équivalent
> n'a été écrit : la garde ne prouvait rien de plus que la présence d'une chaîne, et la surface
> concernée est couverte, quand elle l'est, par les tests vitest cités. Les 126 tests de comportement
> de `test_regression.py` sont conservés tels quels.

| Classe | Test | Ce qu'il lisait | Remplacement |
|---|---|---|---|
| `TestBUG112_EmailManuelAutreFournisseur` | `test_bug112_password_visibility_toggle_present` | SMTP_TSX : showPassword | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestBUG112_EmailManuelAutreFournisseur` | `test_bug112_manual_can_save_logic_present` | SMTP_TSX : canSave; hasCompleteConfiguration | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestBUG114_CalendarOverlappingEvents` | `test_bug114_week_view_uses_overlap_layout` | CALENDAR_VIEW_TSX : getTimedEventLayout; left: `${layout.leftPercent}%` | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestBUG114_CalendarOverlappingEvents` | `test_bug114_day_view_uses_overlap_layout` | CALENDAR_VIEW_TSX : width: `${layout.widthPercent}%`; layoutByEventId | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestBUG002PortDynamique` | `test_main_accepts_port_argument` | MAIN_PY : --port | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestBUG002PortDynamique` | `test_main_default_port_17293` | MAIN_PY : default=17293 | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestBUG002PortDynamique` | `test_main_accepts_host_argument` | MAIN_PY : --host | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestBUG002PortDynamique` | `test_api_core_singleton_init` | API_CORE_TS : _initPromise; if (_initPromise) return _initPromise | retirée (garde textuelle sur l'interface) ; vitest : core.portEtSingleton.test.ts |
| `TestBUG002PortDynamique` | `test_api_core_retry_ipc` | API_CORE_TS : MAX_RETRIES; RETRY_DELAY | retirée (garde textuelle sur l'interface) ; vitest : core.portEtSingleton.test.ts |
| `TestBUG003QdrantLock` | `test_qdrant_lock_cleanup_in_main` | MAIN_PY : .lock; lock_file.unlink() | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestBUG005DLLWindows` | `test_backend_spec_no_strip_windows` | (chemin composé) : strip=False; win32 | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestBUG007Zombies` | `test_zombie_cleanup_exists` | MAIN_PY : _kill_zombie_backends | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestBUG007Zombies` | `test_zombie_cleanup_skips_self` | MAIN_PY : current_pid; pid != current_pid | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestBUG007Zombies` | `test_zombie_cleanup_skips_parent` | MAIN_PY : parent_pid | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestBUG008FreezeSupport` | `test_freeze_support_before_app_import` | MAIN_PY :  | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestBUG011IPCMacM1` | `test_retry_ipc_mechanism` | API_CORE_TS : MAX_RETRIES; RETRY_DELAY | retirée (garde textuelle sur l'interface) ; vitest : core.portEtSingleton.test.ts |
| `TestBUG012CrashMacM4Max` | `test_embeddings_force_cpu` | EMBEDDINGS_PY :  | comportement : `tests/test_regression_socle.py` |
| `TestBUG012CrashMacM4Max` | `test_embeddings_no_mps` | EMBEDDINGS_PY :  | comportement : `tests/test_regression_socle.py` |
| `TestBUG013KeychainLazy` | `test_encryption_new_does_not_initialize` | ENCRYPTION_PY : _initialize | comportement : `tests/test_regression_socle.py` |
| `TestBUG013KeychainLazy` | `test_encryption_has_ensure_initialized` | ENCRYPTION_PY : _ensure_initialized | comportement : `tests/test_regression_socle.py` |
| `TestBUG013KeychainLazy` | `test_encrypt_calls_ensure_initialized` | ENCRYPTION_PY : _ensure_initialized | comportement : `tests/test_regression_socle.py` |
| `TestBUG013KeychainLazy` | `test_decrypt_calls_ensure_initialized` | ENCRYPTION_PY : _ensure_initialized | comportement : `tests/test_regression_socle.py` |
| `TestBUG013KeychainLazy` | `test_startup_profile_no_decrypt` | APP_MAIN_PY : allow_decrypt=False | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestXSSEmailSanitization` | `test_email_html_sanitized` | (chemin composé) : dangerouslySetInnerHTML; sanitize | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestBUG015PortMismatchPanels` | `test_api_core_reads_url_port` | API_CORE_TS : urlParams; URLSearchParams | retirée (garde textuelle sur l'interface) ; vitest : core.portEtSingleton.test.ts |
| `TestBUG015PortMismatchPanels` | `test_url_port_checked_before_ipc` | API_CORE_TS :  | retirée (garde textuelle sur l'interface) ; vitest : core.portEtSingleton.test.ts |
| `TestBUG009RustTasklistFallback` | `test_rust_has_wmic` | TAURI_LIB_RS : wmic | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestBUG009RustTasklistFallback` | `test_rust_has_tasklist_fallback` | TAURI_LIB_RS : tasklist | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestBUG009RustTasklistFallback` | `test_rust_tasklist_after_wmic` | TAURI_LIB_RS :  | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestBUG009RustTasklistFallback` | `test_rust_windows_handle_wait` | TAURI_LIB_RS : from_secs(3); from_secs(2) | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestScrollStreaming` | `test_virtuoso_handles_scroll` | MESSAGE_LIST_TSX : Virtuoso; followOutput | retirée (garde textuelle sur l'interface) ; vitest : MessageList.tronquee.test.tsx |
| `TestScrollStreaming` | `test_user_scroll_detection` | MESSAGE_LIST_TSX : atBottomThreshold | retirée (garde textuelle sur l'interface) ; vitest : MessageList.tronquee.test.tsx |
| `TestScrollStreaming` | `test_smooth_scroll_only_when_at_bottom` | MESSAGE_LIST_TSX, followOutput.ts : isStreaming; return false | retirée (garde textuelle sur l'interface) ; vitest : MessageList.tronquee.test.tsx, followOutput.test.ts |
| `TestBUG017TempSidecarRedirect` | `test_rust_sets_tmpdir` | TAURI_LIB_RS :  | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestBUG017TempSidecarRedirect` | `test_rust_sets_temp` | TAURI_LIB_RS :  | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestBUG017TempSidecarRedirect` | `test_rust_sets_tmp` | TAURI_LIB_RS :  | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestBUG017TempSidecarRedirect` | `test_rust_runtime_dir_created` | TAURI_LIB_RS : runtime; create_dir_all | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestBUG018DegradedStatus` | `test_probe_accepts_degraded` | SPLASH_SCREEN_TSX : degraded | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBUG018DegradedStatus` | `test_probe_accepts_healthy` | SPLASH_SCREEN_TSX : healthy | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBUG020SplashTimeout` | `test_timeout_at_least_600s` | SPLASH_SCREEN_TSX :  | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBUG020SplashTimeout` | `test_poll_interval_at_least_2s` | SPLASH_SCREEN_TSX :  | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBUG020SplashTimeout` | `test_adaptive_messages` | SPLASH_SCREEN_TSX : 60_000; 60000 | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBUG020SplashTimeout` | `test_logarithmic_progress` | SPLASH_SCREEN_TSX : log1p; Math.log | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBUG020LazyLoading` | `test_preload_not_awaited_directly_in_lifespan` | APP_MAIN_PY :  | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestBUG020LazyLoading` | `test_preload_uses_create_task` | APP_MAIN_PY : create_task; preload_embedding | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestBUG021StreamingScroll` | `test_virtuoso_replaces_raf_scroll` | MESSAGE_LIST_TSX : requestAnimationFrame; Virtuoso | retirée (garde textuelle sur l'interface) ; vitest : MessageList.tronquee.test.tsx |
| `TestBUG021StreamingScroll` | `test_virtuoso_ref_present` | MESSAGE_LIST_TSX : computeFollowOutput | retirée (garde textuelle sur l'interface) ; vitest : MessageList.tronquee.test.tsx |
| `TestUXSidebarDefault` | `test_sidebar_default_false` | PrototypeConversationDrawer.tsx, panelStore.ts : showConversationSidebar: false; usePanelStore | retirée (garde textuelle sur l'interface) ; vitest : PrototypeConversationDrawer.test.tsx |
| `TestUXNamingConsistency` | `test_no_espace_de_travail` | MEMORY_PANEL_TSX : Espace de travail | retirée (garde textuelle sur l'interface) ; vitest : MemoryPanel.etatVide.test.tsx, MemoryPanel.test.tsx |
| `TestUXTokenTooltip` | `test_usage_has_title_attribute` | MESSAGE_BUBBLE_TSX : tokens; pas une facture | retirée (garde textuelle sur l'interface) ; vitest : MessageBubble.markdownBrut.test.tsx, MessageBubble.test.tsx |
| `TestUXLogoClickable` | `test_logo_has_onclick` | CHAT_HEADER_TSX : createConversation; THÉRÈSE | retirée (garde textuelle sur l'interface) ; vitest : ChatHeader.test.tsx |
| `TestUXEmailDisconnect` | `test_disconnect_button_present` | EMAIL_PANEL_TSX : handleDisconnectAccount; LogOut | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestUXEmailDisconnect` | `test_disconnect_calls_api` | EMAIL_PANEL_TSX : disconnectEmailAccount | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestPortFixe17293` | `test_rust_uses_fixed_port` | TAURI_LIB_RS : 17293; find_free_port | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestPortFixe17293` | `test_rust_no_tcplistener_bind` | TAURI_LIB_RS : TcpListener::bind | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestPortFixe17293` | `test_main_py_default_port_17293` | MAIN_PY : default=17293 | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestPortFixe17293` | `test_config_py_port_17293` | CONFIG_PY : port: int = 17293 | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestPortFixe17293` | `test_core_ts_fallback_17293` | API_CORE_TS : VITE_THERESE_BACKEND_PORT ?? 17293 | retirée (garde textuelle sur l'interface) ; vitest : core.portEtSingleton.test.ts |
| `TestPortFixe17293` | `test_pas_de_config_playwright_secondaire` | playwright.config.ts :  | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestPortFixe17293` | `test_core_ts_no_port_8000_check` | API_CORE_TS : port !== 8000; port != 8000 | retirée (garde textuelle sur l'interface) ; vitest : core.portEtSingleton.test.ts |
| `TestBUG022CORSWindowsOrigin` | `test_cors_has_http_tauri_localhost` | APP_MAIN_PY : http://tauri.localhost | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestBUG022CORSWindowsOrigin` | `test_cors_has_all_three_origins` | APP_MAIN_PY : tauri://localhost; https://tauri.localhost | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestBUG022CORSWindowsOrigin` | `test_probe_health_has_error_logging` | SPLASH_SCREEN_TSX : console.error | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBUG022CORSWindowsOrigin` | `test_probe_health_timeout_at_least_5s` | SPLASH_SCREEN_TSX : createTimeoutSignal(5000) | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBUG022CORSWindowsOrigin` | `test_private_network_access_header` | APP_MAIN_PY : Access-Control-Allow-Private-Network | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestBUG023EmailRaceCondition` | `test_abort_controller_present` | EMAIL_LIST_TSX : AbortController; abortControllerRef | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestBUG023EmailRaceCondition` | `test_loading_guard_present` | EMAIL_LIST_TSX : isLoadingRef | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestBUG023EmailRaceCondition` | `test_no_stale_closure` | EMAIL_LIST_TSX : useEmailStore.getState() | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestBUG023EmailRaceCondition` | `test_abort_on_cleanup` | EMAIL_LIST_TSX : abortControllerRef.current; .abort() | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestOpenRouterProvider` | `test_openrouter_file_exists` | OPENROUTER_PY :  | comportement : `tests/test_regression_fournisseurs.py` |
| `TestOpenRouterProvider` | `test_openrouter_in_init` | PROVIDERS_INIT_PY : OpenRouterProvider | comportement : `tests/test_regression_fournisseurs.py` |
| `TestOpenRouterProvider` | `test_openrouter_in_provider_map` | LLM_PY : OPENROUTER; OpenRouterProvider | comportement : `tests/test_regression_fournisseurs.py` |
| `TestOpenRouterProvider` | `test_openrouter_api_url` | OPENROUTER_PY : openrouter.ai/api/v1 | comportement : `tests/test_regression_fournisseurs.py` |
| `TestFalImageProvider` | `test_fal_in_image_provider_enum` | IMAGE_GENERATOR_PY : fal-flux-pro | comportement : `tests/test_regression_socle.py` |
| `TestFalImageProvider` | `test_fal_generation_method` | IMAGE_GENERATOR_PY : _generate_fal; fal.run | comportement : `tests/test_regression_socle.py` |
| `TestAboutVersionDisplay` | `test_about_tab_fetches_version` | ABOUT_TAB_TSX : checkHealth | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBUG024ProfileSave` | `test_profile_schema_has_billing_fields` | SCHEMAS_PY : address; siren | comportement : `tests/test_regression_socle.py` |
| `TestBUG024ProfileSave` | `test_profile_response_has_billing_fields` | SCHEMAS_PY : address; siren | comportement : `tests/test_regression_socle.py` |
| `TestBUG024DocxPptxTemplates` | `test_backend_spec_includes_docx_data_files` | (chemin composé) :  | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestBUG024DocxPptxTemplates` | `test_backend_spec_includes_pptx_data_files` | (chemin composé) :  | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestWindowControlsPlatform` | `test_platform_detection_in_header` | CHAT_HEADER_TSX : isMac; navigator.platform | retirée (garde textuelle sur l'interface) ; vitest : ChatHeader.test.tsx |
| `TestStreamingAntiFlicker` | `test_message_bubble_has_css_containment` | MESSAGE_BUBBLE_TSX : contain | retirée (garde textuelle sur l'interface) ; vitest : MessageBubble.markdownBrut.test.tsx, MessageBubble.test.tsx |
| `TestStreamingAntiFlicker` | `test_streaming_sentence_flush` | CHAT_INPUT_TSX : SENTENCE_ENDINGS; flushToDisplay | retirée (garde textuelle sur l'interface) ; vitest : ChatInput.annulation.test.tsx, ChatInput.image.test.tsx, ChatInput.indexation.test.tsx, ChatInput.rattachement.test.tsx |
| `TestBUG025OllamaSystemPrompt` | `test_ollama_system_prompt_as_message` | ollama.py :  | comportement : `tests/test_regression_fournisseurs.py` |
| `TestBUG025OllamaSystemPrompt` | `test_ollama_no_top_level_system_in_json` | ollama.py :  | comportement : `tests/test_regression_fournisseurs.py` |
| `TestBUG025OllamaSystemPrompt` | `test_ollama_base_url_trailing_slash` | ollama.py :  | comportement : `tests/test_regression_fournisseurs.py` |
| `TestBUG025OllamaSystemPrompt` | `test_ollama_filters_system_messages` | ollama.py : chat_messages | comportement : `tests/test_regression_fournisseurs.py` |
| `TestBUG026ProfileSave` | `test_set_profile_uses_category` | USER_PROFILE_PY :  | comportement : `tests/test_regression_socle.py` |
| `TestBUG026ProfileSave` | `test_delete_profile_uses_category` | USER_PROFILE_PY : PROFILE_CATEGORY | comportement : `tests/test_regression_socle.py` |
| `TestXLSXSupport` | `test_xlsx_extract_function_exists` | FILE_PARSER_PY : _extract_xlsx | comportement : `tests/test_regression_socle.py` |
| `TestXLSXSupport` | `test_xlsx_extension_handled` | FILE_PARSER_PY :  | comportement : `tests/test_regression_socle.py` |
| `TestUploadEndpoint` | `test_upload_endpoint_exists` | FILES_ROUTER_PY : upload; UploadFile | comportement : `tests/test_regression_socle.py` |
| `TestUploadEndpoint` | `test_upload_validates_extension` | FILES_ROUTER_PY : ALLOWED_UPLOAD_EXTENSIONS | comportement : `tests/test_regression_socle.py` |
| `TestSkillIdInChat` | `test_backend_schema_has_skill_id` | SCHEMAS_PY : skill_id | comportement : `tests/test_regression_socle.py` |
| `TestSkillIdInChat` | `test_backend_injects_skill_system_prompt` | CHAT_ROUTER_PY : get_skills_registry; get_system_prompt_addition | comportement : `tests/test_regression_socle.py` |
| `TestSkillIdInChat` | `test_frontend_chat_api_has_skill_id` | CHAT_TS : skill_id | retirée (garde textuelle sur l'interface) ; vitest : ChatGardeLeCanevas.test.tsx, ChatHeader.test.tsx, ChatInput.annulation.test.tsx, ChatInput.image.test.tsx |
| `TestSaveAsCommand` | `test_message_bubble_has_bookmark` | MESSAGE_BUBBLE_TSX : Bookmark; onSaveAsCommand | retirée (garde textuelle sur l'interface) ; vitest : MessageBubble.markdownBrut.test.tsx, MessageBubble.test.tsx |
| `TestSaveAsCommand` | `test_message_list_has_save_as_command` | MessageList.tsx : onSaveAsCommand | retirée (garde textuelle sur l'interface) ; vitest : MessageList.tronquee.test.tsx |
| `TestSaveAsCommand` | `test_panel_container_has_save_command_modal` | ConversationCanvasPrototype.tsx, PanelContainer.tsx : CreateCommandForm; showSaveCommand | retirée (garde textuelle sur l'interface) ; vitest : ConversationCanvasPrototype.palette.focus.test.tsx, ConversationCanvasPrototype.palette.raccourcis.test.tsx, ConversationCanvasPrototype.palette.sections.test.tsx, ConversationCanvasPrototype.parite.test.tsx |
| `TestSaveAsCommand` | `test_create_command_form_accepts_initial_values` | CreateCommandForm.tsx : initialContent; initialDescription | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestImageUseButton` | `test_image_panel_has_onuse_prop` | IMAGE_GENERATION_PANEL_TSX : onUse | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestImageUseButton` | `test_image_panel_has_utiliser_button` | IMAGE_GENERATION_PANEL_TSX : Utiliser | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBUG033FileBrowserAccent` | `test_no_repertoire_without_accent` | FILE_BROWSER_TSX :  | retirée (garde textuelle sur l'interface) ; vitest : FileBrowser.guide066.test.tsx, fileBrowserPaths.test.ts |
| `TestBUG034MicrophonePluginReady` | `test_hook_exports_plugin_ready` | VOICE_RECORDER_TS : pluginReady | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBUG034MicrophonePluginReady` | `test_chat_input_disables_mic_when_not_ready` | CHAT_INPUT_TSX, VOICE_DICTATION_BUTTON_TSX : VoiceDictationButton; pluginReady | retirée (garde textuelle sur l'interface) ; vitest : ChatInput.annulation.test.tsx, ChatInput.image.test.tsx, ChatInput.indexation.test.tsx, ChatInput.rattachement.test.tsx |
| `TestCalendarWeekDayViews` | `test_week_view_exists` | CALENDAR_VIEW_TSX : function WeekView; WEEK_START_HOUR | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestCalendarWeekDayViews` | `test_day_view_exists` | CALENDAR_VIEW_TSX : function DayView; DAY_START_HOUR | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestCalendarWeekDayViews` | `test_week_view_has_current_time_indicator` | CALENDAR_VIEW_TSX : nowLineTop; bg-instant | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestCRMProjectsTabRemoved` | `test_no_projects_tab` | CRM_PANEL_TSX :  | retirée (garde textuelle sur l'interface) ; vitest : CRMPanel.activitesEnPanne.test.tsx, CRMPanel.activitesNommees.test.tsx, CRMPanel.contactSansSource.test.tsx, CRMPanel.echap.test.tsx |
| `TestCRMProjectsTabRemoved` | `test_global_activity_view_exists` | CRM_PANEL_TSX : GlobalActivityView | retirée (garde textuelle sur l'interface) ; vitest : CRMPanel.activitesEnPanne.test.tsx, CRMPanel.activitesNommees.test.tsx, CRMPanel.contactSansSource.test.tsx, CRMPanel.echap.test.tsx |
| `TestCRMProjectsTabRemoved` | `test_activity_filter_chips` | CRM_PANEL_TSX : ACTIVITY_FILTER_CHIPS | retirée (garde textuelle sur l'interface) ; vitest : CRMPanel.activitesEnPanne.test.tsx, CRMPanel.activitesNommees.test.tsx, CRMPanel.contactSansSource.test.tsx, CRMPanel.echap.test.tsx |
| `TestBUG035TemplatesPathResolution` | `test_runtime_hook_file_exists` | (chemin composé) :  | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestBUG035TemplatesPathResolution` | `test_runtime_hook_creates_docx_parts` | (chemin composé) : docx/parts | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestBUG035TemplatesPathResolution` | `test_runtime_hook_creates_pptx_oxml` | (chemin composé) : pptx/oxml | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestBUG035TemplatesPathResolution` | `test_runtime_hook_creates_pptx_shapes` | (chemin composé) : pptx/shapes | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestBUG035TemplatesPathResolution` | `test_backend_spec_references_runtime_hook` | (chemin composé) : runtime_hook_templates | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestBUG035TemplatesPathResolution` | `test_runtime_hook_checks_meipass` | (chemin composé) : _MEIPASS | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestBUG028PricingEUR` | `test_estimate_cost_strips_provider_prefix` | TOKEN_TRACKER_PY : , 1) | comportement : `tests/test_regression_socle.py` |
| `TestStreamingRawText` | `test_message_bubble_has_streaming_condition` | MESSAGE_BUBBLE_TSX : message.isStreaming; whitespace-pre-wrap | retirée (garde textuelle sur l'interface) ; vitest : MessageBubble.markdownBrut.test.tsx, MessageBubble.test.tsx |
| `TestStreamingRawText` | `test_message_bubble_raw_text_before_markdown` | MESSAGE_BUBBLE_TSX :  | retirée (garde textuelle sur l'interface) ; vitest : MessageBubble.markdownBrut.test.tsx, MessageBubble.test.tsx |
| `TestStreamingRawText` | `test_message_bubble_has_min_height` | MESSAGE_BUBBLE_TSX : minHeight | retirée (garde textuelle sur l'interface) ; vitest : MessageBubble.markdownBrut.test.tsx, MessageBubble.test.tsx |
| `TestBUG025_DropdownContraste` | `test_option_has_explicit_colors` | LLM_TAB_TSX : option; #0B1226 | retirée (garde textuelle sur l'interface) ; vitest : LLMTab.qwen.test.tsx, LLMTab.refusAnnonce.test.tsx, LLMTab.test.tsx |
| `TestBUG127_AgentBubbleContrast` | `test_message_utilise_le_token_de_theme_pas_un_blanc_fige` | BUBBLE_TSX : text-text; #E6EDF7 | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBUG038_StopStreaming` | `test_abort_controller_in_chat_input` | CHAT_INPUT_TSX : AbortController | retirée (garde textuelle sur l'interface) ; vitest : ChatInput.annulation.test.tsx, ChatInput.image.test.tsx, ChatInput.indexation.test.tsx, ChatInput.rattachement.test.tsx |
| `TestBUG038_StopStreaming` | `test_stop_button_visible_during_streaming` | CHAT_INPUT_TSX : Square; stopStreaming | retirée (garde textuelle sur l'interface) ; vitest : ChatInput.annulation.test.tsx, ChatInput.image.test.tsx, ChatInput.indexation.test.tsx, ChatInput.rattachement.test.tsx |
| `TestBUG038_StopStreaming` | `test_stream_message_accepts_signal` | CHAT_API_TS : signal | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBUG038_StopStreaming` | `test_abort_error_shows_partial_content` | CHAT_INPUT_TSX : AbortError | retirée (garde textuelle sur l'interface) ; vitest : ChatInput.annulation.test.tsx, ChatInput.image.test.tsx, ChatInput.indexation.test.tsx, ChatInput.rattachement.test.tsx |
| `TestUX_ReponsesLegeres` | `test_system_prompt_forbids_markdown_tables` | LLM_PY : tableau | comportement : `tests/test_regression_fournisseurs.py` |
| `TestUX_ReponsesLegeres` | `test_system_prompt_prefers_bullet_lists` | LLM_PY : puces; listes | comportement : `tests/test_regression_fournisseurs.py` |
| `TestBUG039_EmailButton` | `test_mail_icon_removed` | (chemin composé) : openInMailClient | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBUG026_EmailUtiliserButton` | `test_use_response_calls_start_composing` | EMAIL_DETAIL_TSX : startComposing | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestBUG026_EmailUtiliserButton` | `test_reply_uses_start_composing` | EMAIL_DETAIL_TSX : startComposing([message.from_email] | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestBUG026_EmailUtiliserButton` | `test_store_has_start_composing` | EMAIL_DETAIL_TSX, emailStore.ts : startComposing:; isComposing: true | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestBUG037_ScrollJumpStreaming` | `test_virtuoso_follow_output_present` | (chemin composé) : followOutput | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBUG037_ScrollJumpStreaming` | `test_align_to_bottom_prevents_jump` | followOutput.ts :  | retirée (garde textuelle sur l'interface) ; vitest : followOutput.test.ts |
| `TestBUG041_LayoutShiftStreaming` | `test_layout_disabled_during_streaming` | (chemin composé) : layout={!message.isStreaming}; layout\n | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBUG041_LayoutShiftStreaming` | `test_contain_always_includes_layout` | (chemin composé) :  | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBUG041_LayoutShiftStreaming` | `test_min_height_fixed_during_streaming` | (chemin composé) : Math.ceil(message.content.length | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBUG040_OllamaErrorMessages` | `test_ollama_catches_connect_error` | OLLAMA_PY : httpx.ConnectError | comportement : `tests/test_regression_fournisseurs.py` |
| `TestBUG040_OllamaErrorMessages` | `test_ollama_catches_read_timeout` | OLLAMA_PY : httpx.ReadTimeout | comportement : `tests/test_regression_fournisseurs.py` |
| `TestBUG040_OllamaErrorMessages` | `test_ollama_catches_http_status_error` | OLLAMA_PY : response.status_code != 200; aread() | comportement : `tests/test_regression_fournisseurs.py` |
| `TestBUG040_OllamaErrorMessages` | `test_ollama_404_mentions_ollama_pull` | OLLAMA_PY : ollama pull | comportement : `tests/test_regression_fournisseurs.py` |
| `TestBUG040_OllamaErrorMessages` | `test_ollama_connect_error_mentions_serve` | OLLAMA_PY : ollama serve | comportement : `tests/test_regression_fournisseurs.py` |
| `TestBUG040_OllamaErrorMessages` | `test_ollama_checks_error_in_stream` | OLLAMA_PY :  | comportement : `tests/test_regression_fournisseurs.py` |
| `TestBUG040_OllamaErrorMessages` | `test_no_unknown_error_fallback` | chat.py : Unknown error | comportement : `tests/test_regression_socle.py` |
| `TestBUG039_ListboxContrast` | `test_global_css_styles_select_options` | GLOBALS_CSS : select option | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBUG039_ListboxContrast` | `test_select_option_has_background` | GLOBALS_CSS : background-color; --color-surface | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBUG038_LineBreaksChat` | `test_user_messages_not_through_react_markdown` | (chemin composé) : isUser | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBUG026_BoutonUtiliserEmail` | `test_modal_uses_portal` | (chemin composé) : createPortal; document.body | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBUG026_BoutonUtiliserEmail` | `test_modal_z_index_above_email_panel` | (chemin composé) : Z_LAYER.MODAL_NESTED | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBUG026_BoutonUtiliserEmail` | `test_handle_use_stops_propagation` | (chemin composé) : stopPropagation | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBUG026_BoutonUtiliserEmail` | `test_handle_use_response_uses_start_composing` | (chemin composé) : startComposing | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBUG026_BoutonUtiliserEmail` | `test_delete_optimistic_removal` | (chemin composé) : removeMessage(messageId); | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBUG041_OllamaAdminError` | `test_ollama_500_mentions_admin` | OLLAMA_PY : if status == 500:; error | comportement : `tests/test_regression_fournisseurs.py` |
| `TestBUG041_OllamaAdminError` | `test_ollama_empty_response_yields_error` | OLLAMA_PY : has_content; gelé | comportement : `tests/test_regression_fournisseurs.py` |
| `TestBUG041_OllamaAdminError` | `test_error_messages_persisted_in_db` | CHAT_PY : session.add(err_msg); await session.commit() | comportement : `tests/test_regression_socle.py` |
| `TestBatchV0211_OllamaAdminWindows` | `test_ollama_500_admin_message` | OLLAMA_PY : if status == 500: | comportement : `tests/test_regression_fournisseurs.py` |
| `TestBatchV0211_OllamaAdminWindows` | `test_ollama_empty_response_error_event` | OLLAMA_PY : gelé | comportement : `tests/test_regression_fournisseurs.py` |
| `TestBatchV0211_OllamaAdminWindows` | `test_error_messages_persisted` | CHAT_PY : session.add(err_msg) | comportement : `tests/test_regression_socle.py` |
| `TestBatchV0211_EmailWizardPortal` | `test_create_portal_imported` | WIZARD_TSX : createPortal | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBatchV0211_EmailWizardPortal` | `test_higher_z_index` | WIZARD_TSX : Z_LAYER.WIZARD | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBatchV0211_EmailWizardPortal` | `test_portal_to_body` | WIZARD_TSX : document.body | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBatchV0211_SmtpFailedToFetch` | `test_failed_to_fetch_intercepted` | SMTP_TSX : Failed to fetch | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestBatchV0211_SmtpFailedToFetch` | `test_user_friendly_error_message` | SMTP_TSX : Impossible de joindre le serveur | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestBatchV0211_GmailRedirectUri` | `test_redirect_uri_stored` | VERIFY_TSX : redirectUri | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBatchV0211_GmailRedirectUri` | `test_redirect_uri_displayed_on_error` | VERIFY_TSX : redirect_uri_mismatch | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBatchV0211_AppleIconWindows` | `test_shortcuts_modal_adapts_to_platform` | SHORTCUTS_TSX : adaptKey | retirée (garde textuelle sur l'interface) ; vitest : ShortcutsModal.test.tsx, ShortcutsModal.verite.test.tsx |
| `TestBatchV0211_AppleIconWindows` | `test_skill_prompt_panel_platform_aware` | SKILL_TSX : navigator.platform | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBatchV0211_LinuxCategory` | `test_linux_desktop_category_set` | (chemin composé) :  | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestBatchV0211_LinuxCategory` | `test_splash_screen_windows_message_platform_aware` | SplashScreen.tsx :  | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBUG031_ContextMessageOrder` | `test_desc_order_on_history_load` | CHAT_PY : Message.created_at.desc() | comportement : `tests/test_regression_socle.py` |
| `TestBUG031_ContextMessageOrder` | `test_list_reversed_applied` | CHAT_PY : list(reversed(history_result.scalars().all())) | comportement : `tests/test_regression_socle.py` |
| `TestBUGNEW_PutToPatchCRM` | `test_update_contact_uses_patch` | MEMORY_TS : updateContact; async function | retirée (garde textuelle sur l'interface) ; vitest : MemoryPanel.etatVide.test.tsx, MemoryPanel.test.tsx, memory.recherche.test.ts, memory.test.ts |
| `TestBUGNEW_PutToPatchCRM` | `test_update_project_uses_patch` | MEMORY_TS :  | retirée (garde textuelle sur l'interface) ; vitest : MemoryPanel.etatVide.test.tsx, MemoryPanel.test.tsx, memory.recherche.test.ts, memory.test.ts |
| `TestBUGNEW_PutToPatchCRM` | `test_no_put_for_update_functions` | MEMORY_TS :  | retirée (garde textuelle sur l'interface) ; vitest : MemoryPanel.etatVide.test.tsx, MemoryPanel.test.tsx, memory.recherche.test.ts, memory.test.ts |
| `TestBUG048_OllamaNumPredict` | `test_options_block_present` | OLLAMA_PY :  | comportement : `tests/test_regression_fournisseurs.py` |
| `TestBUG048_OllamaNumPredict` | `test_num_predict_transmitted` | OLLAMA_PY : num_predict | comportement : `tests/test_regression_fournisseurs.py` |
| `TestBUG048_OllamaNumPredict` | `test_num_ctx_transmitted` | OLLAMA_PY : num_ctx | comportement : `tests/test_regression_fournisseurs.py` |
| `TestBUGNEW_AsyncioPython313` | `test_no_get_event_loop` | IMAP_SMTP_PY : get_event_loop() | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestBUGNEW_AsyncioPython313` | `test_get_running_loop_used` | IMAP_SMTP_PY : get_running_loop() | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestBUGNEW_GoogleRefreshTokenRotation` | `test_refresh_token_rotation_handled` | EMAIL_PY :  | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestBUGNEW_GoogleRefreshTokenRotation` | `test_refresh_token_encrypted_and_saved` | EMAIL_PY :  | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestBUGNEW_FilesExtractText` | `test_todo_removed` | FILES_PY : TODO: Implement proper file parsing | comportement : `tests/test_regression_socle.py` |
| `TestBUGNEW_FilesExtractText` | `test_extract_text_called` | FILES_PY : content = await extract_text_async(file_path) | comportement : `tests/test_regression_socle.py` |
| `TestBUGNEW_FilesExtractText` | `test_none_guard_present` | FILES_PY : if content is None | comportement : `tests/test_regression_socle.py` |
| `TestBUG031_TriDeterministeChat` | `test_order_by_has_two_keys` | CHAT_PY : Message.created_at.desc(), Message.id.desc() | comportement : `tests/test_regression_socle.py` |
| `TestBUG031_TriDeterministeChat` | `test_order_by_not_single_key` | CHAT_PY :  | comportement : `tests/test_regression_socle.py` |
| `TestAsyncioGetRunningLoop` | `test_no_get_event_loop_in_backend` | (chemin composé) : get_event_loop() | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestAsyncioGetRunningLoop` | `test_caldav_uses_get_running_loop` | caldav_provider.py : get_running_loop() | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestBUG049_OllamaRetestButton` | `test_retest_prop_in_interface` | LLM_TAB_TSX : onRetestOllama | retirée (garde textuelle sur l'interface) ; vitest : LLMTab.qwen.test.tsx, LLMTab.refusAnnonce.test.tsx, LLMTab.test.tsx |
| `TestBUG049_OllamaRetestButton` | `test_refresh_icon_used` | LLM_TAB_TSX : RefreshCw | retirée (garde textuelle sur l'interface) ; vitest : LLMTab.qwen.test.tsx, LLMTab.refusAnnonce.test.tsx, LLMTab.test.tsx |
| `TestBUG049_OllamaRetestButton` | `test_retest_function_in_settings_modal` | SETTINGS_MODAL_TSX : retestOllama | retirée (garde textuelle sur l'interface) ; vitest : SettingsModal.fermeture.test.tsx, SettingsModal.fournisseurIA.test.tsx, SettingsModal.test.ts |
| `TestBUG049_OllamaRetestButton` | `test_retest_passed_to_llmtab` | SETTINGS_MODAL_TSX : onRetestOllama={retestOllama} | retirée (garde textuelle sur l'interface) ; vitest : SettingsModal.fermeture.test.tsx, SettingsModal.fournisseurIA.test.tsx, SettingsModal.test.ts |
| `TestBUG050_OllamaSkillsTimeout` | `test_no_fixed_read_timeout` | OLLAMA_PY : timeout=120.0 | comportement : `tests/test_regression_fournisseurs.py` |
| `TestBUG050_OllamaSkillsTimeout` | `test_read_timeout_none` | OLLAMA_PY : read=None | comportement : `tests/test_regression_fournisseurs.py` |
| `TestBUG050_OllamaSkillsTimeout` | `test_connect_timeout_preserved` | OLLAMA_PY : connect=5.0 | comportement : `tests/test_regression_fournisseurs.py` |
| `TestBUGGmail403_AccessDenied` | `test_access_denied_special_case` | EMAIL_PY : access_denied | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestBUGGmail403_AccessDenied` | `test_test_users_tip_shown` | EMAIL_PY : Test; Utilisateurs de test | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestBUGGmail403_AccessDenied` | `test_apis_activation_tip_shown` | EMAIL_PY : Gmail API | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestBUGGmail403_AccessDenied` | `test_verify_step_has_403_tips` | VERIFY_TSX :  | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBUG042_SkillsMaxTokens` | `test_max_tokens_at_least_16384` | SKILLS_PY :  | comportement : `tests/test_regression_socle.py` |
| `TestBUG043_DocumentContentValidation` | `test_validate_document_content_exists` | (chemin composé) : _validate_document_content | comportement : `tests/test_regression_socle.py` ou couverture existante (voir docstring) |
| `TestBUG043_DocumentContentValidation` | `test_validation_called_after_code_execution` | (chemin composé) : _validate_document_content; fallback vers parser legacy | comportement : `tests/test_regression_socle.py` ou couverture existante (voir docstring) |
| `TestBUG043_DocumentContentValidation` | `test_min_content_elements_defined` | (chemin composé) : MIN_CONTENT_ELEMENTS | comportement : `tests/test_regression_socle.py` ou couverture existante (voir docstring) |
| `TestBUG043_DocumentContentValidation` | `test_retry_markdown_in_router` | skills.py : retry; markdown | comportement : `tests/test_regression_socle.py` |
| `TestBUG044_FilePathsInChat` | `test_chat_request_has_file_paths_field` | SCHEMAS_PY : file_paths | comportement : `tests/test_regression_socle.py` |
| `TestBUG044_FilePathsInChat` | `test_frontend_sends_file_paths` | (chemin composé) : file_paths | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBUG044_FilePathsInChat` | `test_backend_processes_file_paths` | CHAT_PY : file_paths; _get_file_context | comportement : `tests/test_regression_socle.py` |
| `TestBUG044_FilePathsInChat` | `test_frontend_chat_request_type_has_file_paths` | CHAT_TS : file_paths | retirée (garde textuelle sur l'interface) ; vitest : ChatGardeLeCanevas.test.tsx, ChatHeader.test.tsx, ChatInput.annulation.test.tsx, ChatInput.image.test.tsx |
| `TestBUG044_LinuxOnedirPyInstaller` | `test_backend_spec_has_collect_for_linux` | (chemin composé) : COLLECT(; exclude_binaries=True | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestBUG044_LinuxOnedirPyInstaller` | `test_release_yml_linux_uses_wrapper_script` | RELEASE_YML : THERESE_BACKEND_LIBS; backend-libs | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestBUG044_LinuxOnedirPyInstaller` | `test_lib_rs_passes_backend_libs_env_on_linux` | LIB_RS : THERESE_BACKEND_LIBS; resource_dir() | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestBUG044_LinuxOnedirPyInstaller` | `test_release_yml_injects_backend_libs_resources_linux` | RELEASE_YML : backend-libs | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestBUG044_LinuxOnedirPyInstaller` | `test_release_yml_cp_copies_content_not_folder` | RELEASE_YML : dist/backend/.; dist/backend/* | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestBUG049_CalendarDropdownOverflow` | `test_calendar_select_has_zindex_wrapper` | (chemin composé) : relative ${Z_LAYER.ONBOARDING} | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBUG050_EncryptionKeyBackupFile` | `test_create_key_calls_write_key_backup` | ENCRYPTION_PY : _write_key_backup; self._write_key_backup(key) | comportement : `tests/test_regression_socle.py` |
| `TestBUG050_EncryptionKeyBackupFile` | `test_write_key_backup_method_exists` | ENCRYPTION_PY : def _write_key_backup(self, key: bytes); KEY_FILE | comportement : `tests/test_regression_socle.py` |
| `TestBUG050_EncryptionKeyBackupFile` | `test_migrate_does_not_delete_file` | ENCRYPTION_PY : KEY_FILE.unlink() | comportement : `tests/test_regression_socle.py` |
| `TestBUG050_KeychainFallbackToFile` | `test_get_or_create_key_checks_file_coherence` | ENCRYPTION_PY : file_key != keychain_key | comportement : `tests/test_regression_socle.py` |
| `TestBUG050_KeychainFallbackToFile` | `test_get_or_create_key_restores_file_key_to_keychain` | ENCRYPTION_PY : file_key.decode; return file_key | comportement : `tests/test_regression_socle.py` |
| `TestBUG050_KeychainFallbackToFile` | `test_keychain_key_synced_to_backup_file` | ENCRYPTION_PY : self._write_key_backup(keychain_key) | comportement : `tests/test_regression_socle.py` |
| `TestBUG051_CorruptedKeysDetection` | `test_config_has_check_key_decryptable_helper` | CONFIG_ROUTER_PY : _check_key_decryptable | comportement : `tests/test_regression_socle.py` |
| `TestBUG051_CorruptedKeysDetection` | `test_config_uses_decrypt_value_in_check` | CONFIG_ROUTER_PY : decrypt_value | comportement : `tests/test_regression_socle.py` |
| `TestBUG051_CorruptedKeysDetection` | `test_config_response_has_corrupted_keys` | SCHEMAS_PY : corrupted_keys | comportement : `tests/test_regression_socle.py` |
| `TestBUG051_CorruptedKeysDetection` | `test_get_config_returns_corrupted_keys` | CONFIG_ROUTER_PY : corrupted_keys=corrupted_keys | comportement : `tests/test_regression_socle.py` |
| `TestBUG052_OllamaModelPreference` | `test_fallback_uses_selected_model` | LLM_PY : selected_model or detect_default_ollama_model() | comportement : `tests/test_regression_fournisseurs.py` |
| `TestBUG052_OllamaModelPreference` | `test_get_llm_service_reads_db_model` | LLM_PY : llm_model | comportement : `tests/test_regression_fournisseurs.py` |
| `TestBUG098_OllamaDefaultModelDetection` | `test_llm_fallbacks_use_detection_not_hardcoded` | LLM_PY :  | comportement : `tests/test_regression_fournisseurs.py` |
| `TestBUG098_OllamaDefaultModelDetection` | `test_board_sovereign_uses_detection` | BOARD_PY : detect_default_ollama_model | comportement : `tests/test_regression_socle.py` |
| `TestBUG099_GeminiKeyPrefixRelaxed` | `test_backend_no_longer_requires_aiza_prefix` | CONFIG_PY :  | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestBUG099_GeminiKeyPrefixRelaxed` | `test_frontend_image_gemini_no_aiza_prefix` | (chemin composé) :  | comportement : `tests/test_regression_socle.py` ou couverture existante (voir docstring) |
| `TestBUG100_OnboardingProviderListVisible` | `test_provider_list_not_height_capped` | (chemin composé) : max-h-48 | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBUG102_UnifiedContactQdrantEmbed` | `test_crm_create_embeds_qdrant` | CRM_PY : _embed_contact | comportement : `tests/test_regression_socle.py` |
| `TestBUG102_UnifiedContactQdrantEmbed` | `test_update_contact_reembeds` | MEMORY_PY : _embed_contact | comportement : `tests/test_regression_socle.py` |
| `TestChantierA_VeriteExecution` | `test_create_tools_deduplicate` | (chemin composé) : _find_existing_contact; _find_existing_project | comportement : `tests/test_regression_socle.py` ou couverture existante (voir docstring) |
| `TestChantierA_VeriteExecution` | `test_create_tools_return_honest_errors` | (chemin composé) :  | comportement : `tests/test_regression_socle.py` ou couverture existante (voir docstring) |
| `TestChantierA_VeriteExecution` | `test_chat_enforces_create_cap_and_recap` | CHAT_PY : enforce_create_cap; summarize_executions | comportement : `tests/test_regression_socle.py` |
| `TestPhase1_CRMAsView` | `test_navigation_store_exists` | (chemin composé) : activeView; setView | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestPhase1_CRMAsView` | `test_panel_window_system_removed` | (chemin composé) :  | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestPhase1_CRMAsView` | `test_la_coque_route_les_vues` | (chemin composé) : useNavigationStore | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestL6_MemoryAsView` | `test_memory_panel_supports_standalone` | (chemin composé) : standalone | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestL6_MemoryAsView` | `test_la_coque_route_la_vue_memoire` | (chemin composé) : <MemoryPanel standalone | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestL6_MemoryAsView` | `test_memory_drawer_removed_from_panelcontainer` | (chemin composé) : isOpen={showMemoryPanel} | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestL6_MemoryAsView` | `test_panelstore_memory_toggle_debt_removed` | panelStore.ts :  | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestL6_ContactScopeRoundtrip` | `test_create_handler_persists_and_exposes_scope` | (chemin composé) : scope=request.scope; scope=contact.scope | comportement : `tests/test_regression_socle.py` ou couverture existante (voir docstring) |
| `TestL7_UnifiedEscape` | `test_echap_ramene_en_arriere_depuis_une_vue` | (chemin composé) : consommeEchapUnifie; collapseEmbeddedView | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestL7_UnifiedEscape` | `test_la_coque_gere_echap` | (chemin composé) : Escape | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestL7_UnifiedEscape` | `test_panelstore_handle_escape_removed` | (chemin composé) : handleEscape | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestL8_ActionRegistry` | `test_registry_exposes_run_action` | (chemin composé) : export function runAction; export function getActions | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestL8_ActionRegistry` | `test_command_palette_reads_from_registry` | (chemin composé) : getActions(); runAction( | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestL8_ActionRegistry` | `test_la_coque_expose_le_pont_de_recette` | ConversationCanvasPrototype.tsx : __therese; runAction | retirée (garde textuelle sur l'interface) ; vitest : ConversationCanvasPrototype.palette.focus.test.tsx, ConversationCanvasPrototype.palette.raccourcis.test.tsx, ConversationCanvasPrototype.palette.sections.test.tsx, ConversationCanvasPrototype.parite.test.tsx |
| `TestArbitrage_FilesView` | `test_files_is_an_app_view` | (chemin composé) :  | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestArbitrage_FilesView` | `test_files_action_in_registry` | (chemin composé) : files.open | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestArbitrage_FilesView` | `test_la_coque_route_la_vue_fichiers` | (chemin composé) : FileBrowser | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestArbitrage_FilesView` | `test_memory_no_longer_hosts_files` | (chemin composé) : FileBrowser | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestSynKO_NavFixes` | `test_la_pile_d_overlays_passe_avant_tout` | (chemin composé) : runTopEscapeHandler; pushEscapeHandler | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestSynKO_NavFixes` | `test_memory_modals_register_escape` | (chemin composé) : pushEscapeHandler | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestSynKO_NavFixes` | `test_slash_menu_uses_escape_stack_not_local` | (chemin composé) : pushEscapeHandler | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestSynKO_NavFixes` | `test_prompt_library_mounted_globally` | (chemin composé) : PromptLibrary; openPromptLibrary | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestSynKO_NavFixes` | `test_guided_inserts_chat_prompt` | (chemin composé) : insert-prompt | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestF12_ModelIndicator` | `test_chat_input_imports_get_llm_config` | CHAT_INPUT_TSX : getLLMConfig | retirée (garde textuelle sur l'interface) ; vitest : ChatInput.annulation.test.tsx, ChatInput.image.test.tsx, ChatInput.indexation.test.tsx, ChatInput.rattachement.test.tsx |
| `TestF12_ModelIndicator` | `test_chat_input_has_current_model_state` | CHAT_INPUT_TSX : currentModel | retirée (garde textuelle sur l'interface) ; vitest : ChatInput.annulation.test.tsx, ChatInput.image.test.tsx, ChatInput.indexation.test.tsx, ChatInput.rattachement.test.tsx |
| `TestF12_ModelIndicator` | `test_chat_input_listens_to_config_changed` | CHAT_INPUT_TSX : therese:llm-config-changed | retirée (garde textuelle sur l'interface) ; vitest : ChatInput.annulation.test.tsx, ChatInput.image.test.tsx, ChatInput.indexation.test.tsx, ChatInput.rattachement.test.tsx |
| `TestF13_CRMCredentials` | `test_crm_has_credentials_endpoint` | CRM_PY : /sync/credentials | comportement : `tests/test_regression_socle.py` |
| `TestF13_CRMCredentials` | `test_crm_validates_client_id_format` | CRM_PY : apps.googleusercontent.com | comportement : `tests/test_regression_socle.py` |
| `TestF13_CRMCredentials` | `test_frontend_has_credentials_form` | CRM_SYNC_PANEL_TSX : showCredentialsForm | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBUG044b_LinuxDebBackendLibs` | `test_tauri_linux_conf_has_backend_libs_resource` | (chemin composé) : backend-libs | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestBUG044b_LinuxDebBackendLibs` | `test_tauri_linux_conf_uses_recursive_glob` | (chemin composé) :  | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestBUG044b_LinuxDebBackendLibs` | `test_release_yml_copies_backend_libs` | RELEASE_YML : backend-libs | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestBUG044b_LinuxDebBackendLibs` | `test_release_yml_uses_linux_config` | RELEASE_YML, tauri.linux.conf.json : tauri.linux.conf.json | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestBUG057_CSPImagePreview` | `test_img_src_allows_localhost` | (chemin composé) : http://localhost:* | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestBUG057_CSPImagePreview` | `test_img_src_allows_127` | (chemin composé) : http://127.0.0.1:* | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestBUG058_EmailRefresh` | `test_store_has_refresh_counter` | EMAIL_STORE_TS : refreshCounter | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestBUG058_EmailRefresh` | `test_store_has_trigger_refresh` | EMAIL_STORE_TS : triggerRefresh | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestBUG058_EmailRefresh` | `test_email_panel_calls_trigger_refresh` | EMAIL_PANEL_TSX : triggerRefresh | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestBUG058_EmailRefresh` | `test_email_list_watches_refresh_counter` | EMAIL_LIST_TSX : refreshCounter | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestBUG059_SMTPTestTimeout` | `test_smtp_test_present` | IMAP_SMTP_PY : aiosmtplib | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestBUG059_SMTPTestTimeout` | `test_timeout_present` | IMAP_SMTP_PY : wait_for | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestBUG059_SMTPTestTimeout` | `test_returns_dict` | IMAP_SMTP_PY : imap_ok; smtp_ok | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestBUG060_CRMHeaderHomogeneity` | `test_tint_badge_present` | CRM_PANEL_TSX : bg-accent-tint border-[1.5px] border-[var(--btn-ink)]; bg-gradient-to-br from-ac | retirée (garde textuelle sur l'interface) ; vitest : CRMPanel.activitesEnPanne.test.tsx, CRMPanel.activitesNommees.test.tsx, CRMPanel.contactSansSource.test.tsx, CRMPanel.echap.test.tsx |
| `TestBUG060_CRMHeaderHomogeneity` | `test_icon_in_badge` | CRM_PANEL_TSX : w-10 h-10 rounded-sm | retirée (garde textuelle sur l'interface) ; vitest : CRMPanel.activitesEnPanne.test.tsx, CRMPanel.activitesNommees.test.tsx, CRMPanel.contactSansSource.test.tsx, CRMPanel.echap.test.tsx |
| `TestBUG062_MCPNodePath` | `test_nvm_path_added` | MCP_SERVICE_PY : .nvm | comportement : `tests/test_regression_socle.py` |
| `TestBUG062_MCPNodePath` | `test_homebrew_path_added` | MCP_SERVICE_PY : /opt/homebrew/bin | comportement : `tests/test_regression_socle.py` |
| `TestBUG062_MCPNodePath` | `test_volta_path_added` | MCP_SERVICE_PY : .volta | comportement : `tests/test_regression_socle.py` |
| `TestBUG064_MCPPresetTooltip` | `test_alertcircle_has_tooltip` | TOOLS_PANEL_TSX : Installé mais inactif | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBUG065_SettingsErrorClear` | `test_error_cleared_on_tab_switch` | SETTINGS_TSX : setError(null) | retirée (garde textuelle sur l'interface) ; vitest : SettingsModal.fermeture.test.tsx, SettingsModal.fournisseurIA.test.tsx, SettingsModal.test.ts |
| `TestBUG066_ContexteAdditionnel` | `test_description_present` | PROFILE_TAB_TSX : personnaliser ses réponses | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestF14_OllamaModelListing` | `test_ollama_branch_in_get_llm` | CONFIG_PY : _available_models_for | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestF14_OllamaModelListing` | `test_ollama_fetches_api_tags` | CONFIG_PY : api/tags | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestF15_ModelIndicatorUI` | `test_pill_badge_styling` | CHAT_INPUT_TSX : rounded-sm bg-accent-cyan/10 | retirée (garde textuelle sur l'interface) ; vitest : ChatInput.annulation.test.tsx, ChatInput.image.test.tsx, ChatInput.indexation.test.tsx, ChatInput.rattachement.test.tsx |
| `TestF15_ModelIndicatorUI` | `test_model_selector_dropdown` | CHAT_INPUT_TSX : handleModelChange | retirée (garde textuelle sur l'interface) ; vitest : ChatInput.annulation.test.tsx, ChatInput.image.test.tsx, ChatInput.indexation.test.tsx, ChatInput.rattachement.test.tsx |
| `TestBUG056_ImageLoadingIndicator` | `test_loading_message_in_command_executor` | COMMAND_EXECUTOR_TSX : isStreaming: true | retirée (garde textuelle sur l'interface) ; vitest : CommandExecutor.reessayer.test.tsx, CommandExecutor.test.tsx |
| `TestBUG056_ImageLoadingIndicator` | `test_update_message_replaces_loading` | COMMAND_EXECUTOR_TSX : updateMessage | retirée (garde textuelle sur l'interface) ; vitest : CommandExecutor.reessayer.test.tsx, CommandExecutor.test.tsx |
| `TestBUG056_ImageLoadingIndicator` | `test_chat_store_update_message_accepts_meta` | CHAT_STORE_TS : meta | retirée (garde textuelle sur l'interface) ; vitest : chatStore.navigation.test.ts, chatStore.test.ts |
| `TestF16_CredentialsJsonImport` | `test_file_input_in_credentials_step` | CREDENTIALS_STEP_TSX :  | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestF16_CredentialsJsonImport` | `test_json_parsing_in_credentials_step` | CREDENTIALS_STEP_TSX : client_id; client_secret | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestF16_CredentialsJsonImport` | `test_file_input_in_crm_sync_panel` | CRM_SYNC_PANEL_TSX :  | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestF16_CredentialsJsonImport` | `test_json_parsing_in_crm_sync_panel` | CRM_SYNC_PANEL_TSX : client_id; client_secret | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestF17_BoardSovereignMode` | `test_board_mode_enum_exists` | BOARD_MODELS_PY : BoardMode | comportement : `tests/test_regression_socle.py` |
| `TestF17_BoardSovereignMode` | `test_board_mode_values` | BOARD_MODELS_PY : CLOUD; SOVEREIGN | comportement : `tests/test_regression_socle.py` |
| `TestF17_BoardSovereignMode` | `test_board_request_has_mode` | BOARD_MODELS_PY : mode; ollama_models | comportement : `tests/test_regression_socle.py` |
| `TestF17_BoardSovereignMode` | `test_sovereign_sequential_path` | BOARD_SERVICE_PY : sovereign | comportement : `tests/test_regression_socle.py` |
| `TestF17_BoardArcLayout` | `test_file_exists` | ARC_LAYOUT_TSX :  | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestF17_BoardArcLayout` | `test_arc_angles` | ARC_LAYOUT_TSX : ARC_ANGLES | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestF17_BoardArcLayout` | `test_responsive_fallback` | ARC_LAYOUT_TSX : md:hidden; grid | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestF17_BoardModeSelector` | `test_file_exists` | MODE_SELECTOR_TSX :  | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestF17_BoardModeSelector` | `test_cloud_sovereign_toggle` | MODE_SELECTOR_TSX : cloud; souverain | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestF17_BoardModeSelector` | `test_framer_motion_animation` | MODE_SELECTOR_TSX : layoutId; motion | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBUG057_BoardCancelDeliberation` | `test_abort_controller_in_board_panel` | BOARD_PANEL_TSX : AbortController | retirée (garde textuelle sur l'interface) ; vitest : BoardPanel.robustesse.test.tsx |
| `TestBUG057_BoardCancelDeliberation` | `test_signal_in_stream_deliberation` | BOARD_TS : signal | retirée (garde textuelle sur l'interface) ; vitest : BoardConversationCard.test.tsx, BoardPanel.robustesse.test.tsx |
| `TestBUG057_BoardCancelDeliberation` | `test_cancel_button_in_deliberation_view` | DELIBERATION_TSX : onCancel | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBUG057_BoardCancelDeliberation` | `test_annuler_label` | DELIBERATION_TSX : Annuler | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBUG058_BoardCloudProviderModel` | `test_provider_match_check` | LLM_PY : user_provider == provider_name | comportement : `tests/test_regression_fournisseurs.py` |
| `TestBUG058_BoardCloudProviderModel` | `test_llm_provider_read_from_db` | LLM_PY : llm_provider | comportement : `tests/test_regression_fournisseurs.py` |
| `TestBUG063_OllamaModelDefaultConfig` | `test_default_config_has_warning_logging` | LLM_PY : logger.warning; Could not read LLM preferences | comportement : `tests/test_regression_fournisseurs.py` |
| `TestBUG063_OllamaModelDefaultConfig` | `test_default_config_logs_preferences_read` | LLM_PY : LLM preferences from DB: | comportement : `tests/test_regression_fournisseurs.py` |
| `TestBUG063_OllamaModelDefaultConfig` | `test_default_config_uses_singleton` | LLM_PY : get_sync_connection | comportement : `tests/test_regression_fournisseurs.py` |
| `TestBUG064_BoardFirstMount` | `test_animate_presence_initial_false` | BOARD_TSX : initial={false} | retirée (garde textuelle sur l'interface) ; vitest : BoardConversationCard.test.tsx, BoardPanel.robustesse.test.tsx |
| `TestBUG065_PPTXTitleColor` | `test_no_blanc_in_title_prompt` | (chemin composé) : Titre de slide; blanc | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBUG062b_MCPToolCallTimeout` | `test_default_timeout_increased` | MCP_PY : timeout: float = 60.0 | comportement : `tests/test_regression_socle.py` |
| `TestBUG062b_MCPToolCallTimeout` | `test_tools_call_timeout_increased` | MCP_PY : timeout=120.0 | comportement : `tests/test_regression_socle.py` |
| `TestBUG061b_EmailRefreshDiag` | `test_backend_logs_enrichment_errors` | EMAIL_PY : Email enrichment: | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestBUG061b_EmailRefreshDiag` | `test_frontend_logs_error_messages` | EMAIL_LIST_TSX : BUG-061b | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestBUG059_EmailReAuthPolling` | `test_updated_at_in_email_account` | EMAIL_TS : updated_at | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestBUG059_EmailReAuthPolling` | `test_initial_accounts_ref` | VERIFY_STEP_TSX : initialAccountsRef | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBUG059_EmailReAuthPolling` | `test_updated_at_comparison` | VERIFY_STEP_TSX : updated_at | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBUG070_ConversationGhost404` | `test_chat_input_imports_delete_conversation` | ChatInput.tsx : deleteConversation, | retirée (garde textuelle sur l'interface) ; vitest : ChatInput.annulation.test.tsx, ChatInput.image.test.tsx, ChatInput.indexation.test.tsx, ChatInput.rattachement.test.tsx |
| `TestBUG070_ConversationGhost404` | `test_ghost_conversation_reset_on_404` | ChatInput.tsx : isConversationGhost; deleteConversation(currentConversationId | retirée (garde textuelle sur l'interface) ; vitest : ChatInput.annulation.test.tsx, ChatInput.image.test.tsx, ChatInput.indexation.test.tsx, ChatInput.rattachement.test.tsx |
| `TestBUG070_ConversationGhost404` | `test_ghost_message_is_user_friendly` | ChatInput.tsx : nouveau chat a été créé automatiquement | retirée (garde textuelle sur l'interface) ; vitest : ChatInput.annulation.test.tsx, ChatInput.image.test.tsx, ChatInput.indexation.test.tsx, ChatInput.rattachement.test.tsx |
| `TestBUG053_DateActuelleSubstituee` | `test_llm_imports_datetime` | llm.py : from datetime import | comportement : `tests/test_regression_fournisseurs.py` |
| `TestBUG053_DateActuelleSubstituee` | `test_system_prompt_template_has_current_date` | llm.py : {current_date} | comportement : `tests/test_regression_fournisseurs.py` |
| `TestBUG053_DateActuelleSubstituee` | `test_system_prompt_no_profile_has_current_date` | llm.py :  | comportement : `tests/test_regression_fournisseurs.py` |
| `TestBUG053_DateActuelleSubstituee` | `test_get_system_prompt_injects_date` | llm.py : , current_date | comportement : `tests/test_regression_fournisseurs.py` |
| `TestBUG053_DateActuelleSubstituee` | `test_recap_rule_restricted_to_chat` | llm.py : chat uniquement; JAMAIS pour la génération de documents | comportement : `tests/test_regression_fournisseurs.py` |
| `TestBUG_DocxPptxXlsxGuardrails` | `test_docx_no_recap_guardrail` | docx_generator.py : récapitulatif; récap | comportement : `tests/test_regression_socle.py` |
| `TestBUG_DocxPptxXlsxGuardrails` | `test_docx_watermark_accent` | docx_generator.py : THÉRÈSE - Synoptïa | comportement : `tests/test_regression_socle.py` |
| `TestBUG_DocxPptxXlsxGuardrails` | `test_pptx_no_markdown_guardrail` | pptx_generator.py : Markdown | comportement : `tests/test_regression_socle.py` |
| `TestBUG_DocxPptxXlsxGuardrails` | `test_pptx_nb_slides_variable` | pptx_generator.py : nb_slides; RESPECTE exactement ce nombre | comportement : `tests/test_regression_socle.py` |
| `TestBUG_DocxPptxXlsxGuardrails` | `test_pptx_no_recap_guardrail` | pptx_generator.py : récapitulatif; INTERDIT | comportement : `tests/test_regression_socle.py` |
| `TestBUG_DocxPptxXlsxGuardrails` | `test_xlsx_no_hallucination_guardrail` | xlsx_generator.py : NE PAS inventer; RÈGLE ABSOLUE | comportement : `tests/test_regression_socle.py` |
| `TestBUG_DocxPptxXlsxGuardrails` | `test_xlsx_no_recap_guardrail` | xlsx_generator.py : récapitulatif; INTERDIT | comportement : `tests/test_regression_socle.py` |
| `TestBUG_CommandPaletteProduire` | `test_produce_document_action_in_registry` | (chemin composé) : Produire un document; getActions() | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBUG_CommandPaletteProduire` | `test_command_palette_z_index_above_settings` | (chemin composé) : Z_LAYER.COMMAND_PALETTE | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBUG_CommandPaletteProduire` | `test_cmd_n_works_in_input_context` | useKeyboardShortcuts.ts :  | retirée (garde textuelle sur l'interface) ; vitest : useKeyboardShortcuts.creneauxMorts.test.ts, useKeyboardShortcuts.test.ts |
| `TestBUG_PptxNbSlides` | `test_build_namespace_accepts_nb_slides` | code_executor.py : nb_slides: int = 10 | comportement : `tests/test_regression_socle.py` |
| `TestBUG_PptxNbSlides` | `test_namespace_contains_nb_slides` | code_executor.py : : nb_slides | comportement : `tests/test_regression_socle.py` |
| `TestBUG_PptxNbSlides` | `test_execute_sandboxed_passes_nb_slides` | code_executor.py : _build_namespace(output_path, title, format_type, nb_slides) | comportement : `tests/test_regression_socle.py` |
| `TestBUG_PptxNbSlides` | `test_skills_router_extracts_nb_slides_from_prompt` | skills.py : nb_slides_from_prompt; slides? | comportement : `tests/test_regression_socle.py` |
| `TestBUG_MistralTools` | `test_mistral_parses_tool_calls_in_stream` | mistral.py : tool_calls | comportement : `tests/test_regression_fournisseurs.py` |
| `TestBUG_MCPPollingStarting` | `test_tools_panel_imports_use_ref` | ToolsPanel.tsx : useRef | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBUG_MCPPollingStarting` | `test_tools_panel_has_polling_effect` | ToolsPanel.tsx : pollingIntervalRef; setInterval | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBUGOpenRouterStrftimeWindows` | `test_current_date_format_no_percent_minus_d` | llm.py :  | comportement : `tests/test_regression_fournisseurs.py` |
| `TestBUGTrafficLightsMacOnWindows` | `test_onboarding_wizard_has_ismac_guard` | OnboardingWizard.tsx : isMac; {isMac && ( | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBUGTrafficLightsMacOnWindows` | `test_chat_header_has_ismac_guard` | ChatHeader.tsx : isMac | retirée (garde textuelle sur l'interface) ; vitest : ChatHeader.test.tsx |
| `TestBUGTrafficLightsMacOnWindows` | `test_onboarding_wizard_no_unconditional_traffic_lights` | OnboardingWizard.tsx :  | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestOpenRouterEmptyResponse` | `test_provider_has_has_content_tracking` | openrouter.py : has_content | comportement : `tests/test_regression_fournisseurs.py` |
| `TestOpenRouterEmptyResponse` | `test_provider_handles_finish_reason_length` | openrouter.py :  | comportement : `tests/test_regression_fournisseurs.py` |
| `TestOpenRouterEmptyResponse` | `test_provider_handles_content_filter` | openrouter.py :  | comportement : `tests/test_regression_fournisseurs.py` |
| `TestOpenRouterEmptyResponse` | `test_provider_handles_sse_error` | openrouter.py : error | comportement : `tests/test_regression_fournisseurs.py` |
| `TestOpenRouterEmptyResponse` | `test_provider_handles_http_401` | openrouter.py : invalide; expiree | comportement : `tests/test_regression_fournisseurs.py` |
| `TestOpenRouterEmptyResponse` | `test_provider_handles_http_402` | openrouter.py : insuffisant; Rechargez | comportement : `tests/test_regression_fournisseurs.py` |
| `TestGroqWhisperLabel` | `test_services_tab_groq_label_mentions_cloud` | ServicesTab.tsx : cloud; Cloud | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestGroqWhisperLabel` | `test_services_tab_groq_label_mentions_model` | ServicesTab.tsx : whisper-large-v3-turbo | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestGroqWhisperLabel` | `test_services_tab_no_misleading_whisper_label` | ServicesTab.tsx : transcription audio (Whisper) | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBUG091_DecimalSeparator` | `test_quantity_input_has_lang_en` | INVOICE_FORM_TSX :  | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestBUG091_DecimalSeparator` | `test_unit_price_input_has_lang_en` | INVOICE_FORM_TSX :  | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestBUG091_DecimalSeparator` | `test_numeric_inputs_are_type_number` | INVOICE_FORM_TSX :  | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestBUG091_DecimalSeparator` | `test_step_precision_present` | INVOICE_FORM_TSX : isValidDecimalDraft; parseDecimalDraft | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestBUG091_DecimalSeparator` | `test_no_onkeydown_hack` | INVOICE_FORM_TSX : onKeyDown | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestBUG092_PDFErrorHandling` | `test_pdf_endpoint_has_try_except` | INVOICES_PY : try:; except | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestBUG092_PDFErrorHandling` | `test_pdf_except_logs_error` | INVOICES_PY : logger.error | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestBUG092_PDFErrorHandling` | `test_pdf_except_raises_http_500` | INVOICES_PY : status_code=500; HTTPException | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestBUG092_PDFErrorHandling` | `test_pdf_error_message_mentions_pdf` | INVOICES_PY :  | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestBUG092_PDFErrorHandling` | `test_pdf_error_message_mentions_erreur` | INVOICES_PY : Erreur; erreur | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestBUG092_PDFErrorHandling` | `test_invoice_pdf_generator_import_exists` | INVOICES_PY : InvoicePDFGenerator | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestBUG092_PDFErrorHandling` | `test_pdf_endpoint_function_name` | INVOICES_PY :  | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestBUG092_PDFErrorHandling` | `test_pdf_endpoint_is_get` | INVOICES_PY : @router.get | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestBUG094_PDFWorkingDirectory` | `test_no_hardcoded_default_in_init` | INVOICE_PDF_PY :  | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestBUG094_PDFWorkingDirectory` | `test_resolve_function_exists` | INVOICE_PDF_PY : def resolve_invoice_output_dir | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestBUG094_PDFWorkingDirectory` | `test_resolve_queries_working_directory` | INVOICE_PDF_PY : working_directory | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestBUG094_PDFWorkingDirectory` | `test_resolve_returns_factures_subfolder` | INVOICE_PDF_PY :  | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestBUG094_PDFWorkingDirectory` | `test_router_uses_get_invoice_output_dir` | INVOICES_PY :  | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestBUG094_PDFWorkingDirectory` | `test_no_bare_instantiation` | INVOICES_PY :  | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestBUG094_PDFWorkingDirectory` | `test_init_accepts_none_output_dir` | INVOICE_PDF_PY : None | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestCalendarGoogleSyncFix` | `test_provider_accepts_gmail` | CALENDAR_PY :  | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestCalendarGoogleSyncFix` | `test_provider_accepts_google` | CALENDAR_PY :  | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestCalendarGoogleSyncFix` | `test_provider_check_includes_both_gmail_and_google` | CALENDAR_PY :  | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestCalendarGoogleSyncFix` | `test_fallback_access_token_refresh_token` | CALENDAR_PY : access_token; refresh_token | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestCalendarGoogleSyncFix` | `test_logger_warning_for_fallthrough` | CALENDAR_PY : logger.warning; fallthrough | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestCalendarGoogleSyncFix` | `test_list_google_calendars_function_exists` | CALENDAR_PY :  | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestCalendarGoogleSyncFix` | `test_list_google_calendars_called_for_google_accounts` | CALENDAR_PY : _list_google_calendars | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestCalendarGoogleSyncFix` | `test_sync_status_endpoint_exists` | CALENDAR_PY : sync/status; sync_status | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestVersionConsistency` | `test_init_version_matches_config_version` | CONFIG_PY, INIT_PY :  | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestVersionConsistency` | `test_bump_script_includes_init_py` | __init__.py : __init__.py | comportement : `tests/test_regression_socle.py` |
| `TestVersionConsistency` | `test_bump_script_has_version_sed_pattern` | (chemin composé) : __version__ | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestVersionConsistency` | `test_version_format_is_semver` | INIT_PY :  | comportement : `tests/test_regression_socle.py` |
| `TestVersionConsistency` | `test_bump_script_validates_semver` | (chemin composé) : grep | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestInvoiceCRUDRobustness` | `test_create_endpoint_checks_contact` | INVOICES_PY : Contact; contact | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestInvoiceCRUDRobustness` | `test_update_endpoint_checks_invoice_exists` | INVOICES_PY :  | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestInvoiceCRUDRobustness` | `test_delete_endpoint_checks_invoice_exists` | INVOICES_PY :  | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestInvoiceCRUDRobustness` | `test_pdf_endpoint_returns_path_and_number` | INVOICES_PY : pdf_path; invoice_number | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestInvoiceCRUDRobustness` | `test_currency_support_eur_chf_usd_gbp` | INVOICE_FORM_TSX :  | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestInvoiceCRUDRobustness` | `test_invoice_number_format_prefix` | INVOICES_PY : FACT | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestInvoiceCRUDRobustness` | `test_invoice_number_uses_max_for_sequence` | INVOICES_PY : func.max | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestInvoiceCRUDRobustness` | `test_mark_paid_endpoint_exists` | INVOICES_PY :  | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestInvoiceCRUDRobustness` | `test_send_endpoint_returns_501` | INVOICES_PY :  | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestInvoiceCRUDRobustness` | `test_create_validates_document_type` | INVOICES_PY : document_type | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestCalendarRobustness` | `test_get_provider_checks_account_for_google` | CALENDAR_PY : account | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestCalendarRobustness` | `test_caldav_setup_validates_connection` | CALENDAR_PY : test_caldav_connection | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestCalendarRobustness` | `test_sync_status_returns_providers_list` | CALENDAR_PY : providers | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestCalendarRobustness` | `test_event_creation_validates_calendar_id` | CALENDAR_PY : calendar_id; request.calendar_id | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestCalendarRobustness` | `test_provider_detection_handles_unknown` | CALENDAR_PY : inconnu; unknown | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestCalendarRobustness` | `test_delete_event_endpoint_exists` | CALENDAR_PY :  | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestCalendarRobustness` | `test_calendar_has_local_provider_support` | CALENDAR_PY :  | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestCalendarRobustness` | `test_calendar_has_caldav_provider_support` | CALENDAR_PY :  | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestSecurityRegression` | `test_no_hardcoded_api_keys_in_routers` | (chemin composé) :  | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestSecurityRegression` | `test_no_dangerous_builtins_in_routers` | (chemin composé) :  | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestSecurityRegression` | `test_httpexception_used_for_errors` | CALENDAR_PY, INVOICES_PY : HTTPException; HTTPException | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestSecurityRegression` | `test_cors_settings_exist_in_main` | (chemin composé) : CORSMiddleware; allow_origins | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestSecurityRegression` | `test_rate_limiting_configured` | (chemin composé) : Limiter; rate_limit | sentinelle structurelle : `tests/test_sentinelles_structure.py` |
| `TestFrontendRegression` | `test_no_alert_in_main_components` | EventDetail.tsx, InvoiceForm.tsx, InvoicesPanel.tsx, MemoryP : alert( | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestFrontendRegression` | `test_api_calls_use_centralized_client` | .test.ts, core.ts, index.ts, types.ts : from; core | retirée (garde textuelle sur l'interface) ; vitest : core.portEtSingleton.test.ts, core.test.ts |
| `TestFrontendRegression` | `test_no_hardcoded_localhost_in_components` | .test.tsx, BoardPanel.tsx, EmailConnect.tsx, config.ts : http://localhost:; http://127.0.0.1: | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestFrontendRegression` | `test_invoice_form_has_currency_selector` | INVOICE_FORM_TSX : currency; CURRENCIES | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestFrontendRegression` | `test_invoice_form_has_tva_rates` | INVOICE_FORM_TSX : TVA_RATES | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestBUG69NestedExceptShadowing` | `test_openrouter_no_nested_except_as_e_in_http_error_handler` | openrouter.py : except Exception as e: | comportement : `tests/test_regression_fournisseurs.py` |
| `TestBUG69NestedExceptShadowing` | `test_anthropic_no_nested_except_as_e_in_http_error_handler` | anthropic.py : except Exception as e: | comportement : `tests/test_regression_fournisseurs.py` |
| `TestBUG69NestedExceptShadowing` | `test_ollama_no_nested_except_as_e_in_http_error_handler` | ollama.py : except Exception as e: | comportement : `tests/test_regression_fournisseurs.py` |
| `TestBUG73GoogleCalendarTZ` | `test_to_rfc3339_z_handles_tz_aware` | (chemin composé) : _to_rfc3339_z; astimezone(_UTC) | comportement : `tests/test_regression_socle.py` ou couverture existante (voir docstring) |
| `TestBUG090VCFExport` | `test_memory_api_uses_downloads_scope_for_tauri_export` | memory.ts : downloadDir; saveVCFFileInDownloads | retirée (garde textuelle sur l'interface) ; vitest : MemoryPanel.etatVide.test.tsx, MemoryPanel.test.tsx, memory.recherche.test.ts, memory.test.ts |
| `TestBUG090VCFExport` | `test_memory_panel_uses_download_helper_for_visible_export` | MemoryPanel.tsx : await api.downloadVCFFile(); Contacts exportés dans Téléchargements | retirée (garde textuelle sur l'interface) ; vitest : MemoryPanel.etatVide.test.tsx, MemoryPanel.test.tsx |
| `TestBUG090VCFExport` | `test_no_unicode_escape_in_jsx_text_nodes` | .test.ts, .test.tsx :  | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBUG090VCFExport` | `test_actions_store_inserts_result_in_chat_on_completion` | actionsStore.ts : useChatStore.getState().addMessage; BUG-097 | retirée (garde textuelle sur l'interface) ; vitest : actionsStore.insertResult.test.ts, actionsStore.resultatDansUneConversation.test.ts, actionsStore.sondage.test.ts, actionsStore.sondageUnique.test.ts |
| `TestQW_CADCurrency` | `test_backend_pdf_has_cad_symbol` | invoice_pdf.py :  | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestQW_CADCurrency` | `test_frontend_invoice_form_offers_cad` | InvoiceForm.tsx : CAD: | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestQW_EmailSignature` | `test_emailpanel_wires_signature_editor` | EmailPanel.tsx : SignatureEditorModal; setShowSignatureEditor | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestQW_EmailSignature` | `test_signature_editor_preview_is_sanitized` | SignatureEditorModal.tsx : sanitizeEmailHtml; pushEscapeHandler | retirée (garde textuelle sur l'interface) ; vitest : SignatureEditorModal.chargement.test.tsx |
| `TestQW_EmailSignature` | `test_shared_sanitizer_forbids_inline_style` | sanitizeEmailHtml.ts : FORBID_TAGS | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestP0IA3_ProviderBadge` | `test_main_auto_migration_adds_provider_column` | database.py : ALTER TABLE messages ADD COLUMN provider | comportement : `tests/test_regression_socle.py` |
| `TestP0IA3_ProviderBadge` | `test_message_bubble_shows_provider_badge` | MessageBubble.tsx : provider; ollama | retirée (garde textuelle sur l'interface) ; vitest : MessageBubble.markdownBrut.test.tsx, MessageBubble.test.tsx |
| `TestP0IA3_ProviderBadge` | `test_chat_input_has_model_selector` | ChatInput.tsx : setLLMConfig; setModel | retirée (garde textuelle sur l'interface) ; vitest : ChatInput.annulation.test.tsx, ChatInput.image.test.tsx, ChatInput.indexation.test.tsx, ChatInput.rattachement.test.tsx |
| `TestBUG130_SkillFilePersistence` | `test_main_auto_migration_adds_extra_data_column` | database.py : ALTER TABLE messages ADD COLUMN extra_data | comportement : `tests/test_regression_socle.py` |
| `TestBUG130_SkillFilePersistence` | `test_chat_persists_skill_file_on_message` | chat.py : assistant_message.extra_data | comportement : `tests/test_regression_socle.py` |
| `TestBUG130_SkillFilePersistence` | `test_message_response_exposes_extra_data` | chat.py : extra_data=msg.extra_data | comportement : `tests/test_regression_socle.py` |
| `TestBUG130_SkillFilePersistence` | `test_frontend_restores_skill_file_from_extra_data` | useConversationSync.ts : formatMessageFromResponse; skill_file | retirée (garde textuelle sur l'interface) ; vitest : useConversationSync.test.ts |
| `TestP0PROD2_BillingProfile` | `test_profile_tab_has_siret_field` | ProfileTab.tsx : siret; SIRET | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestP0PROD2_BillingProfile` | `test_invoice_form_has_emitter_guardrail` | InvoiceForm.tsx, billingProfileStore.ts : useBillingProfileStore; émetteur | comportement : `tests/test_regression_facturation_agenda.py` |
| `TestP0PROD3_ChatTools` | `test_calendar_tool_default_window_widened` | workspace_tools.py : , 30) | comportement : `tests/test_regression_socle.py` |
| `TestQW_PromptHardening` | `test_calendar_tool_directive_on_no_calendar` | workspace_tools.py : AUCUN CALENDRIER CONNECTE; invente AUCUN evenement | comportement : `tests/test_regression_socle.py` |
| `TestQW_GenerateDocumentTool` | `test_capabilities_advertise_generate_document_and_read_contact` | chat.py : generate_document; read_contact | comportement : `tests/test_regression_socle.py` |
| `TestGlobal_Fixes` | `test_mistral_provider_uses_valid_stream_event` | mistral.py : tool_use_id=; tool_call=ToolCall( | comportement : `tests/test_regression_fournisseurs.py` |
| `TestGlobal_Fixes` | `test_mcp_create_server_handles_duplicate_and_timeout` | mcp.py : status_code=409; asyncio.wait_for | comportement : `tests/test_regression_socle.py` |
| `TestV3GenerateTemplateLLMCall` | `test_generate_template_uses_generate_content` | (chemin composé) : llm.generate_content(; llm.generate( | comportement : `tests/test_regression_socle.py` ou couverture existante (voir docstring) |
| `TestBUGA_ToggleOuvrirChatDirectement` | `test_personalisation_store_has_skip_dashboard_preference` | (chemin composé) : skipDashboard: boolean; setSkipDashboard: | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBUGA_ToggleOuvrirChatDirectement` | `test_startup_behavior_uses_zustand_store` | (chemin composé) : usePersonalisationStore; useState | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBUGA_ToggleOuvrirChatDirectement` | `test_navigation_store_respects_skip_dashboard` | (chemin composé) : usePersonalisationStore; skipDashboard | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBUGA_ToggleOuvrirChatDirectement` | `test_migration_from_localstorage` | (chemin composé) : migrateFromLocalStorage; therese-skip-dashboard | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
| `TestBUGA_ToggleOuvrirChatDirectement` | `test_fallbacks_for_undefined_values` | (chemin composé) : ?? false; ?? false | retirée (garde textuelle sur l'interface, sans vitest nommant ce composant) |
