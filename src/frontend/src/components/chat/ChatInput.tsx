import {
  useState,
  useRef,
  useCallback,
  useEffect,
  type KeyboardEvent,
  type ChangeEvent,
} from 'react';
import { AlertCircle, Send, Square, Paperclip, X, Cpu, Search, Settings } from 'lucide-react';
import { useActionsStore } from '../../stores/actionsStore';
import { AnimatePresence, motion } from 'framer-motion';
import { open } from '@tauri-apps/plugin-dialog';
import { Button } from '../ui/Button';
import { SlashCommandsMenu, detectSlashCommand, type SlashCommand } from './SlashCommandsMenu';
import { handleClientActionChunk } from '../../lib/clientActions';
import { ActionChips } from './ActionChips';
import { InlineDropZone, FileChip } from '../files/DropZone';
import { useChatStore } from '../../stores/chatStore';
import { usePanelStore } from '../../stores/panelStore';
import { useStatusStore } from '../../stores/statusStore';
import {
  hasVariableTokens,
  previewVariables,
  type VariablesPreview,
} from '../../services/api/variables';
import { useToolConfirmationStore } from '../../stores/toolConfirmationStore';
import { useFileDrop, type DroppedFile } from '../../hooks/useFileDrop';
import { streamMessage, streamDeepResearch, indexFile, ApiError, getLLMConfig, setLLMConfig, type LLMProvider } from '../../services/api';
import type { StreamChunk } from '../../services/api/chat';
import { useGhostText } from '../../hooks/useGhostText';
import { useAutosave } from '../../hooks/useAutosave';
import { cn } from '../../lib/utils';
import { grantCloudConsent, hasCloudConsent } from '../../lib/consent';
import { VoiceDictationButton } from './VoiceDictationButton';
import { useAccessibilityStore } from '../../stores/accessibilityStore';

const MIN_ROWS = 2;
const MAX_ROWS = 12;

interface ChatInputProps {
  onOpenCommandPalette?: () => void;
  initialPrompt?: string;
  initialSkillId?: string;
  onInitialPromptConsumed?: () => void;
  userCommands?: import('./SlashCommandsMenu').SlashCommand[];
}

interface PendingCloudConsent {
  action: 'message' | 'deep-research';
  provider: LLMProvider;
  providerLabel: string;
  dataCategories: string[];
}

interface AttachedFile extends DroppedFile {
  indexStatus: 'indexing' | 'ready' | 'error';
  indexError?: string;
}

const cloudProviderLabels: Partial<Record<LLMProvider, string>> = {
  anthropic: 'Anthropic', openai: 'OpenAI', gemini: 'Google Gemini', mistral: 'Mistral',
  grok: 'xAI', openrouter: 'OpenRouter', perplexity: 'Perplexity', deepseek: 'DeepSeek',
  infomaniak: 'Infomaniak',
};


// US-007 : Indicateur de dernière sauvegarde
function SavedIndicator({ savedAt }: { savedAt: Date }) {
  const [label, setLabel] = useState('');

  useEffect(() => {
    const update = () => {
      const seconds = Math.floor((Date.now() - savedAt.getTime()) / 1000);
      if (seconds < 5) setLabel('Sauvegardé');
      else if (seconds < 60) setLabel(`Sauvegardé il y a ${seconds}s`);
      else setLabel(`Sauvegardé il y a ${Math.floor(seconds / 60)}min`);
    };
    update();
    const interval = setInterval(update, 5000);
    return () => clearInterval(interval);
  }, [savedAt]);

  return (
    <p className="text-xs text-text-muted">
      {label}
    </p>
  );
}

export function ChatInput({ onOpenCommandPalette, initialPrompt, initialSkillId, onInitialPromptConsumed, userCommands }: ChatInputProps) {
  const [input, setInput] = useState('');
  const [pendingSkillId, setPendingSkillId] = useState<string | undefined>(undefined);
  const [showSlashMenu, setShowSlashMenu] = useState(false);
  const [slashMenuIndex, setSlashMenuIndex] = useState(0);
  const [inputRect, setInputRect] = useState<DOMRect | null>(null);
  const [attachedFiles, setAttachedFiles] = useState<AttachedFile[]>([]);
  const attachedPathsRef = useRef(new Set<string>());
  // Chantier 4 Variables V1 : aperçu de résolution {nom} (debounced) et
  // confirmation par double-envoi quand des variables sont inconnues.
  const [variablesPreview, setVariablesPreview] = useState<VariablesPreview | null>(null);
  const unknownConfirmedRef = useRef(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const showKeyboardHints = useAccessibilityStore((state) => state.showKeyboardHints);

  const {
    addMessage,
    updateMessage,
    setMessageEntities,
    setMessageMetadata,
    setMessageSkillFile,
    setStreaming,
    isStreaming,
    currentConversationId,
    currentConversation,
    updateConversationId,
    deleteConversation,
    queuedPrompt,
    setQueuedPrompt,
  } = useChatStore();
  const { connectionState, setActivity } = useStatusStore();
  const openSettings = usePanelStore((state) => state.openSettings);

  // US-007 : Autosave brouillon
  const { saveDraft, restoreDraft, clearDraft, retrySave, lastSavedAt, draftError } = useAutosave(currentConversationId);

  const isOffline = connectionState !== 'connected';
  const hasQueuedPrompt = queuedPrompt !== null;

  // F-12 : modèle LLM actif + sélecteur rapide
  const [currentModel, setCurrentModel] = useState<string | null>(null);
  const [currentProvider, setCurrentProvider] = useState<LLMProvider | null>(null);
  const [pendingCloudConsent, setPendingCloudConsent] = useState<PendingCloudConsent | null>(null);
  // Mémorise le FOURNISSEUR accordé dans la session : changer de fournisseur
  // redemande un accord (consentement par fournisseur, revue 0.40).
  const cloudConsentGrantedRef = useRef<string | null>(null);
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const [modelAvailable, setModelAvailable] = useState<boolean | null>(null);
  const [modelChangeError, setModelChangeError] = useState<string | null>(null);
  const [failedModel, setFailedModel] = useState<string | null>(null);
  const modelChecking = modelAvailable === null;
  const modelUnavailable = modelAvailable === false;
  const isDisabled = isOffline || hasQueuedPrompt || modelChecking || modelUnavailable;

  const loadLLMConfig = useCallback(() => {
    getLLMConfig()
      .then((cfg) => {
        setCurrentModel(cfg.model);
        setCurrentProvider(cfg.provider);
        setAvailableModels(cfg.available_models || []);
        setModelAvailable(cfg.available !== false);
      })
      .catch(() => setModelAvailable(false));
  }, []);

  useEffect(() => {
    loadLLMConfig();
  }, [loadLLMConfig]);

  // Écouter les changements de config LLM depuis Settings
  useEffect(() => {
    window.addEventListener('therese:llm-config-changed', loadLLMConfig);
    return () => window.removeEventListener('therese:llm-config-changed', loadLLMConfig);
  }, [loadLLMConfig]);

  const handleModelChange = useCallback(async (newModel: string) => {
    if (!currentProvider || newModel === currentModel) return;
    setModelChangeError(null);
    try {
      const cfg = await setLLMConfig(currentProvider, newModel);
      setCurrentModel(cfg.model);
      setAvailableModels(cfg.available_models || []);
      setModelAvailable(cfg.available !== false);
      setFailedModel(null);
      window.dispatchEvent(new Event('therese:llm-config-changed'));
    } catch (reason) {
      setFailedModel(newModel);
      setModelChangeError(reason instanceof Error ? reason.message : 'Le modèle n’a pas pu être changé.');
    }
  }, [currentProvider, currentModel]);

  // Ghost text prédictif
  const { suggestion, accept: acceptGhost, dismiss: dismissGhost } = useGhostText(
    input,
    currentConversationId,
    isStreaming,
  );

  // File drop handling (with deduplication)
  const indexAttachment = useCallback(async (path: string) => {
    setAttachedFiles((current) => current.map((file) => (
      file.path === path ? { ...file, indexStatus: 'indexing', indexError: undefined } : file
    )));
    try {
      await indexFile(path);
      setAttachedFiles((current) => current.map((file) => (
        file.path === path ? { ...file, indexStatus: 'ready', indexError: undefined } : file
      )));
    } catch (reason) {
      setAttachedFiles((current) => current.map((file) => (
        file.path === path
          ? {
              ...file,
              indexStatus: 'error',
              indexError: reason instanceof Error ? reason.message : 'Indexation impossible.',
            }
          : file
      )));
    }
  }, []);

  const handleFilesDropped = useCallback(async (files: DroppedFile[]) => {
    const newFiles = files.filter((file) => {
      if (attachedPathsRef.current.has(file.path)) return false;
      attachedPathsRef.current.add(file.path);
      return true;
    });
    if (newFiles.length === 0) return;
    setAttachedFiles((current) => [
      ...current,
      ...newFiles.map((file): AttachedFile => ({ ...file, indexStatus: 'indexing' })),
    ]);
    await Promise.all(newFiles.map((file) => indexAttachment(file.path)));
  }, [indexAttachment]);

  const { isDragging } = useFileDrop({
    onDrop: handleFilesDropped,
    disabled: isDisabled,
  });

  // Voice recording
  const handleTranscript = useCallback((text: string) => {
    // Append transcript to current input
    setInput((prev) => {
      const trimmed = prev.trim();
      return trimmed ? `${trimmed} ${text}` : text;
    });
    // Focus textarea
    textareaRef.current?.focus();
    setVoiceError(null);
  }, []);

  const [voiceError, setVoiceError] = useState<string | null>(null);
  const handleVoiceError = useCallback((error: string) => {
    setVoiceError(error);
  }, []);

  // Remove attached file
  const removeFile = useCallback((index: number) => {
    setAttachedFiles((current) => {
      const removed = current[index];
      if (removed) attachedPathsRef.current.delete(removed.path);
      return current.filter((_, currentIndex) => currentIndex !== index);
    });
  }, []);

  // Handle browser file input change (fallback when Tauri dialog unavailable)
  const handleBrowserFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const fileList = e.target.files;
    if (!fileList || fileList.length === 0) return;
    const files: DroppedFile[] = Array.from(fileList).map((f) => ({
      path: f.name,
      name: f.name,
      size: f.size,
      mimeType: f.type,
    }));
    handleFilesDropped(files);
    // Reset input so the same file can be re-selected
    e.target.value = '';
  }, [handleFilesDropped]);

  // Open file picker (Tauri dialog or browser fallback)
  const handleAttachClick = useCallback(async () => {
    if (isDisabled) return;

    try {
      const selected = await open({
        multiple: true,
        filters: [
          {
            name: 'Documents',
            extensions: ['txt', 'md', 'pdf', 'docx', 'xlsx', 'json', 'csv'],
          },
          {
            name: 'Code',
            extensions: ['py', 'js', 'ts', 'tsx', 'jsx', 'html', 'css'],
          },
          {
            name: 'Images',
            extensions: ['png', 'jpg', 'jpeg', 'gif', 'webp'],
          },
          {
            name: 'Tous les fichiers',
            extensions: ['*'],
          },
        ],
      });

      if (selected) {
        const paths = Array.isArray(selected) ? selected : [selected];
        const files: DroppedFile[] = paths.map((path) => ({
          path,
          name: path.split(/[/\\]/).pop() || path,
        }));
        handleFilesDropped(files);
      }
    } catch {
      // Tauri dialog not available (browser mode) - fallback to input[type=file]
      fileInputRef.current?.click();
    }
  }, [isDisabled, handleFilesDropped]);

  // Update input rect for menu positioning
  useEffect(() => {
    if (containerRef.current && showSlashMenu) {
      setInputRect(containerRef.current.getBoundingClientRect());
    }
  }, [showSlashMenu]);

  // Detect slash commands
  useEffect(() => {
    const shouldShow = detectSlashCommand(input);
    setShowSlashMenu(shouldShow);
    if (shouldShow) {
      setSlashMenuIndex(0);
    }
  }, [input]);

  // Auto-resize textarea
  const handleInput = useCallback((e: ChangeEvent<HTMLTextAreaElement>) => {
    const textarea = e.target;
    setInput(textarea.value);

    // US-007 : Autosave brouillon (debounced)
    saveDraft(textarea.value);

    // Reset height to calculate new height
    textarea.style.height = 'auto';
    const lineHeight = 24;
    const maxHeight = lineHeight * MAX_ROWS;
    const newHeight = Math.min(textarea.scrollHeight, maxHeight);
    textarea.style.height = `${newHeight}px`;
  }, [saveDraft]);

  useEffect(() => {
    unknownConfirmedRef.current = false;
    if (!hasVariableTokens(input)) {
      setVariablesPreview(null);
      return;
    }
    const handle = window.setTimeout(async () => {
      try {
        setVariablesPreview(await previewVariables(input));
      } catch {
        setVariablesPreview(null);
      }
    }, 350);
    return () => window.clearTimeout(handle);
  }, [input]);

  const sendMessage = useCallback(async () => {
    const trimmed = input.trim();
    if (!trimmed || isOffline || modelAvailable !== true) return;
    if (attachedFiles.some((file) => file.indexStatus !== 'ready')) return;

    // Detection {{action: agent_id}} -> rediriger vers le panneau Actions
    const actionMatch = trimmed.match(/\{\{action\s*:\s*([a-zA-Z0-9_-]+)\s*\}\}/i);
    if (actionMatch) {
      const agentId = actionMatch[1];
      const actionsStore = useActionsStore.getState();
      // Charger les agents si pas encore fait
      if (actionsStore.agents.length === 0) {
        await actionsStore.loadAgents();
      }
      const agent = useActionsStore.getState().agents.find((a) => a.id === agentId);
      if (agent) {
        setInput('');
        actionsStore.openPanel();
        if (agent.params.length > 0) {
          actionsStore.selectAgent(agent);
        } else {
          actionsStore.launchAction(agentId);
        }
        return;
      }
    }

    // Variables inconnues : premier envoi = avertissement local, second =
    // envoi tel quel (les tokens inconnus restent littéraux côté backend).
    if (
      variablesPreview &&
      variablesPreview.unknown.length > 0 &&
      !unknownConfirmedRef.current
    ) {
      unknownConfirmedRef.current = true;
      useStatusStore.getState().addNotification({
        type: 'warning',
        title: 'Variables inconnues',
        message: `${variablesPreview.unknown.map((n) => `{${n}}`).join(', ')} : `
          + 'inconnue(s), le texte partira tel quel. Renvoie pour confirmer.',
      });
      return;
    }
    unknownConfirmedRef.current = false;

    // Si streaming en cours, mettre en file d'attente (1 seul)
    if (isStreaming) {
      setQueuedPrompt(trimmed);
      setInput('');
      if (textareaRef.current) textareaRef.current.style.height = 'auto';
      return;
    }

    if (
      currentProvider && currentProvider !== 'ollama'
      && cloudConsentGrantedRef.current !== currentProvider
      && !hasCloudConsent('llm', currentProvider)
    ) {
      setPendingCloudConsent({
        action: 'message',
        provider: currentProvider,
        providerLabel: cloudProviderLabels[currentProvider] || currentProvider,
        dataCategories: [
          'message saisi',
          'contexte de conversation',
          'mémoire locale utile',
          ...(attachedFiles.length > 0 ? ['fichiers joints sélectionnés'] : []),
        ],
      });
      return;
    }

    // Close slash menu if open
    setShowSlashMenu(false);

    // Build message content with file attachments
    // BUG-044 : capturer les paths AVANT le clear pour les envoyer au backend
    const sentFiles = attachedFiles;
    const filePaths = sentFiles.length > 0
      ? sentFiles.map((f) => f.path)
      : undefined;
    let messageContent = trimmed;
    if (sentFiles.length > 0) {
      const filesList = sentFiles.map((f) => f.name).join(', ');
      messageContent = `${trimmed}\n\n[Fichiers joints: ${filesList}]`;
    }

    // Add user message
    addMessage({ role: 'user', content: messageContent });
    setInput('');
    setAttachedFiles([]); // Clear attached files after sending
    attachedPathsRef.current.clear();

    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }

    // Start streaming
    setStreaming(true);
    setActivity('thinking', 'Réflexion en cours...');

    // Create placeholder assistant message for streaming
    const assistantMessageId = addMessage({
      role: 'assistant',
      content: '',
      isStreaming: true,
    });

    let accumulatedContent = '';
    let backendConversationId: string | null = null;

    // Streaming phrase-par-phrase : flush sur frontière naturelle (. ! ? \n\n)
    // ou timeout 800ms - plus fluide que le setInterval 300ms
    let displayedContent = '';
    let pendingChunk = '';
    const SENTENCE_ENDINGS = /[.!?]\s|[\n]{2}/;
    let bufferTimer: ReturnType<typeof setTimeout> | null = null;

    const flushToDisplay = () => {
      if (accumulatedContent !== displayedContent) {
        displayedContent = accumulatedContent;
        // US-010 : maintenir isStreaming pendant les flushs intermédiaires.
        // updateMessage force isStreaming:false par défaut -> dès la première
        // phrase, la bulle re-parsait tout le markdown à chaque chunk et le
        // curseur de streaming disparaissait.
        updateMessage(assistantMessageId, displayedContent, { isStreaming: true });
      }
      if (bufferTimer) { clearTimeout(bufferTimer); bufferTimer = null; }
    };

    const stopBatching = () => {
      if (bufferTimer) { clearTimeout(bufferTimer); bufferTimer = null; }
    };

    try {
      // Only send conversation_id if it's synced with backend
      const conversation = currentConversation();
      const syncedConversationId = conversation?.synced ? currentConversationId : undefined;

      // Stream response from backend (inclure skill_id si provient des guided prompts)
      const controller = new AbortController();
      abortRef.current = controller;
      const stream = streamMessage({
        message: trimmed,
        conversation_id: syncedConversationId || undefined,
        include_memory: true,
        stream: true,
        ...(pendingSkillId && { skill_id: pendingSkillId }),
        ...(filePaths && { file_paths: filePaths }),
      }, controller.signal);
      // Consommer le skillId après envoi
      setPendingSkillId(undefined);

      // BUG-139 : navigation déterministe différée à la fin du flux

      let pendingClientAction: StreamChunk | null = null;

      for await (const chunk of stream) {
        // Capture the backend conversation ID from the first chunk
        if (chunk.conversation_id && !backendConversationId) {
          backendConversationId = chunk.conversation_id;
          // Update local conversation ID if it was auto-created by the store
          if (currentConversationId && currentConversationId !== backendConversationId) {
            updateConversationId(currentConversationId, backendConversationId);
          }
        }

        if (chunk.type === 'text') {
          // Accumulate content et flush sur frontière de phrase
          accumulatedContent += chunk.content;
          pendingChunk += chunk.content;
          setActivity('streaming', "En train d'écrire...");

          // Flush si fin de phrase détectée dans le nouveau contenu
          if (SENTENCE_ENDINGS.test(pendingChunk)) {
            pendingChunk = '';
            flushToDisplay();
          } else if (!bufferTimer) {
            // Timeout de sécurité : flush après 800ms max sans ponctuation
            bufferTimer = setTimeout(() => {
              pendingChunk = '';
              flushToDisplay();
            }, 800);
          }
        } else if (chunk.type === 'status') {
          // Status updates (file processing, tool execution start, etc.)
          setActivity('thinking', chunk.content || 'Traitement...');
        } else if (chunk.type === 'tool_result') {
          // Tool execution result - show in activity indicator
          setActivity('thinking', `🔧 ${chunk.content || 'Outil exécuté'}`);
        } else if (chunk.type === 'entities_detected' && chunk.entities) {
          // Entities detected - attach to the assistant message
          setMessageEntities(assistantMessageId, chunk.entities);
        } else if (chunk.type === 'skill_file' && chunk.skill_file) {
          // BUG-093 : Fichier généré automatiquement par un skill détecté.
          // BUG-131 : on attache le fichier au message (bouton de téléchargement
          // réel via downloadSkillFile) au lieu d'un lien markdown avec une URL
          // relative `/api/skills/download/...`, morte dans l'app desktop Tauri.
          const sf = chunk.skill_file as {
            skill_id: string;
            file_id: string;
            file_name: string;
            file_size: number;
            download_url: string;
            format: string;
            local_dir?: string;
          };
          setMessageSkillFile(assistantMessageId, {
            skill_id: sf.skill_id,
            file_id: sf.file_id,
            file_name: sf.file_name,
            file_size: sf.file_size,
            format: sf.format,
            local_dir: sf.local_dir,
          });
        } else if (chunk.type === 'client_action') {
          // Actions déterministes (tranche 1a) : le backend a résolu un
          // message-action pur ({action: ouvrir email}) - exécution locale
          // via le registre d'actions, aucun LLM impliqué.
          // BUG-139 : STASH, exécution après la fin du flux - le chunk arrive
          // avant `done`, or la coque refuse de changer de vue pendant un
          // stream (« Arrête la réponse avant de changer de vue »).
          pendingClientAction = chunk;
        } else if (chunk.type === 'skill_file_error') {
          // Fichiers générés visibles (10/07) : un échec de génération ne
          // reste plus silencieux (avant : logs backend seulement, réponse
          // texte sans fichier ni explication).
          useStatusStore.getState().addNotification({
            type: 'error',
            title: 'Fichier non généré',
            message: chunk.content || 'La génération du fichier a échoué.',
          });
        } else if (chunk.type === 'confirmation_required' && chunk.confirmation) {
          // US-002 : action sensible (envoi d'email) en attente de validation.
          // On affiche une carte de confirmation ; rien n'est exécuté sans clic.
          useToolConfirmationStore.getState().add(chunk.confirmation);
        } else if (chunk.type === 'done') {
          // Store usage and uncertainty metadata (US-ESC-02, US-ESC-01)
          if (chunk.usage || chunk.uncertainty) {
            setMessageMetadata(assistantMessageId, chunk.usage, chunk.uncertainty);
          }
        } else if (chunk.type === 'error') {
          throw new Error(chunk.content || "Erreur lors de la génération");
        }
      }

      // BUG-139 : le flux est terminé, la navigation demandée peut s'exécuter
      // (la coque revendique l'événement et ouvre la vue embarquée).
      if (pendingClientAction) {
        setStreaming(false);
        handleClientActionChunk(pendingClientAction);
        pendingClientAction = null;
      }

      // Stop batching and do final update
      stopBatching();
      // Finalize the message (remove streaming flag)
      updateMessage(assistantMessageId, accumulatedContent);
      clearDraft();
    } catch (error) {
      // Stop batching on error
      stopBatching();
      // Le message et ses pièces jointes restent modifiables/réessayables tant
      // que le backend n'a pas confirmé la fin du stream.
      setInput((current) => current.trim() ? current : trimmed);
      setAttachedFiles((current) => {
        if (current.length > 0) return current;
        for (const file of sentFiles) attachedPathsRef.current.add(file.path);
        return sentFiles;
      });
      saveDraft(trimmed);
      // Interruption volontaire : afficher le texte déjà reçu
      if (error instanceof DOMException && error.name === 'AbortError') {
        updateMessage(assistantMessageId, accumulatedContent || '*(interrompu)*');
      } else {
        console.error('Error sending message:', error);

        // BUG-070 : conversation fantôme → 404 persistant
        // Si le backend répond 404 "Conversation not found", la conversation locale
        // référence un ID supprimé. On la retire du store (sans appel API) pour
        // que le prochain message crée une nouvelle conversation propre.
        const isConversationGhost =
          error instanceof ApiError &&
          error.status === 404 &&
          typeof error.message === 'string' &&
          error.message.includes('Conversation not found');

        if (isConversationGhost && currentConversationId) {
          deleteConversation(currentConversationId);
        }

        const errorMessage = isConversationGhost
          ? "La conversation n'existait plus sur le serveur. Un nouveau chat a été créé automatiquement. Tu peux renvoyer ton message."
          : error instanceof ApiError
            ? `Erreur serveur (${error.status}): ${error.message}`
            : error instanceof Error
              ? error.message
              : "Désolée, une erreur s'est produite. Réessaie.";

        // Update the placeholder message with error
        updateMessage(assistantMessageId, errorMessage);
      }
    } finally {
      abortRef.current = null;
      setStreaming(false);
      setActivity('idle');
    }
  }, [input, isOffline, modelAvailable, isStreaming, currentProvider, attachedFiles, addMessage, updateMessage, setMessageEntities, setMessageMetadata, setMessageSkillFile, setStreaming, setActivity, currentConversationId, currentConversation, updateConversationId, deleteConversation, setQueuedPrompt, clearDraft, saveDraft, pendingSkillId, variablesPreview]);

  // Recherche approfondie
  const handleDeepResearch = useCallback(async () => {
    const trimmed = input.trim();
    if (!trimmed || isOffline || isStreaming) return;

    if (
      currentProvider && currentProvider !== 'ollama'
      && cloudConsentGrantedRef.current !== currentProvider
      && !hasCloudConsent('llm', currentProvider)
    ) {
      setPendingCloudConsent({
        action: 'deep-research',
        provider: currentProvider,
        providerLabel: cloudProviderLabels[currentProvider] || currentProvider,
        dataCategories: ['requête saisie', 'contexte de conversation', 'résultats de recherche web'],
      });
      return;
    }

    setShowSlashMenu(false);
    addMessage({ role: 'user', content: `[Recherche approfondie] ${trimmed}` });
    setInput('');
    if (textareaRef.current) textareaRef.current.style.height = 'auto';

    setStreaming(true);
    setActivity('thinking', 'Lancement de la recherche approfondie...');

    const assistantMessageId = addMessage({
      role: 'assistant',
      content: '',
      isStreaming: true,
    });

    let accumulatedContent = '';
    let backendConversationId: string | null = null;

    try {
      const conversation = currentConversation();
      const syncedConversationId = conversation?.synced ? currentConversationId : undefined;

      const controller = new AbortController();
      abortRef.current = controller;

      const stream = streamDeepResearch({
        question: trimmed,
        conversation_id: syncedConversationId || undefined,
      }, controller.signal);

      for await (const chunk of stream) {
        if (chunk.conversation_id && !backendConversationId) {
          backendConversationId = chunk.conversation_id;
          if (currentConversationId && currentConversationId !== backendConversationId) {
            updateConversationId(currentConversationId, backendConversationId);
          }
        }

        if (chunk.type === 'text') {
          accumulatedContent += chunk.content;
          updateMessage(assistantMessageId, accumulatedContent);
          setActivity('streaming', 'Rédaction du rapport...');
        } else if (chunk.type === 'decomposition' || chunk.type === 'searching' || chunk.type === 'search_done') {
          setActivity('thinking', chunk.content || 'Recherche en cours...');
        } else if (chunk.type === 'synthesizing' && !chunk.content) {
          setActivity('thinking', 'Synthèse des sources...');
        } else if (chunk.type === 'error') {
          throw new Error(chunk.content || 'Erreur lors de la recherche');
        }
      }

      updateMessage(assistantMessageId, accumulatedContent);
    } catch (error) {
      if (error instanceof DOMException && error.name === 'AbortError') {
        updateMessage(assistantMessageId, accumulatedContent || '*(recherche interrompue)*');
      } else {
        const errorMessage = error instanceof Error ? error.message : 'Erreur de recherche';
        updateMessage(assistantMessageId, errorMessage);
      }
    } finally {
      abortRef.current = null;
      setStreaming(false);
      setActivity('idle');
    }
  }, [input, isOffline, isStreaming, currentProvider, addMessage, updateMessage, setStreaming, setActivity, currentConversationId, currentConversation, updateConversationId]);

  // Ref stable pour sendMessage (évite dépendances circulaires dans useEffect)
  const sendMessageRef = useRef(sendMessage);
  sendMessageRef.current = sendMessage;
  const deepResearchRef = useRef(handleDeepResearch);
  deepResearchRef.current = handleDeepResearch;

  const confirmCloudConsent = useCallback(() => {
    if (!pendingCloudConsent || currentProvider !== pendingCloudConsent.provider) {
      setPendingCloudConsent(null);
      return;
    }
    grantCloudConsent('llm', pendingCloudConsent.provider, pendingCloudConsent.dataCategories);
    cloudConsentGrantedRef.current = pendingCloudConsent.provider;
    const action = pendingCloudConsent.action;
    setPendingCloudConsent(null);
    window.setTimeout(() => {
      if (action === 'message') void sendMessageRef.current();
      else void deepResearchRef.current();
    }, 0);
  }, [currentProvider, pendingCloudConsent]);

  // Auto-send du prompt en file d'attente quand le streaming finit
  useEffect(() => {
    if (!isStreaming && queuedPrompt) {
      setInput(queuedPrompt);
      setQueuedPrompt(null);
      setTimeout(() => {
        sendMessageRef.current?.();
      }, 50);
    }
  }, [isStreaming, queuedPrompt, setQueuedPrompt]);

  // Interrompre le streaming en cours
  const stopStreaming = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  // Handle slash command selection
  const handleSlashCommandSelect = useCallback((command: SlashCommand) => {
    setInput(command.prefix);
    setShowSlashMenu(false);
    textareaRef.current?.focus();
  }, []);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      // If slash menu is open, let it handle navigation
      if (showSlashMenu) {
        if (['ArrowUp', 'ArrowDown', 'Tab'].includes(e.key)) {
          // These are handled by SlashCommandsMenu
          return;
        }
        if (e.key === 'Enter' && !e.shiftKey) {
          // Enter selects the command - handled by menu
          return;
        }
        if (e.key === 'Escape') {
          e.preventDefault();
          setShowSlashMenu(false);
          return;
        }
      }

      // Ghost text : Tab accepte, Escape dismiss
      if (e.key === 'Tab' && suggestion) {
        e.preventDefault();
        setInput(input + suggestion);
        acceptGhost();
        return;
      }
      if (e.key === 'Escape' && suggestion) {
        e.preventDefault();
        dismissGhost();
        return;
      }

      // Cmd+K opens command palette
      const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
      const modKey = isMac ? e.metaKey : e.ctrlKey;

      if (modKey && e.key === 'k') {
        e.preventDefault();
        onOpenCommandPalette?.();
        return;
      }

      // Send on Enter (without Shift)
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    },
    [sendMessage, showSlashMenu, onOpenCommandPalette, suggestion, input, acceptGhost, dismissGhost]
  );

  // Focus textarea on mount
  useEffect(() => {
    textareaRef.current?.focus();
  }, []);

  // US-007 : Restaurer le brouillon au chargement d'une conversation
  useEffect(() => {
    const draft = restoreDraft();
    if (draft && !input) {
      setInput(draft);
      // Resize textarea pour le brouillon restauré
      setTimeout(() => {
        if (textareaRef.current) {
          textareaRef.current.style.height = 'auto';
          const lineHeight = 24;
          const maxHeight = lineHeight * MAX_ROWS;
          const newHeight = Math.min(textareaRef.current.scrollHeight, maxHeight);
          textareaRef.current.style.height = `${newHeight}px`;
        }
      }, 0);
    }
  }, [currentConversationId]); // eslint-disable-line react-hooks/exhaustive-deps

  // Consume initial prompt from guided prompts
  useEffect(() => {
    if (initialPrompt) {
      setInput(initialPrompt);
      setPendingSkillId(initialSkillId);
      onInitialPromptConsumed?.();
      // Focus and position cursor at end
      setTimeout(() => {
        if (textareaRef.current) {
          textareaRef.current.focus();
          textareaRef.current.selectionStart = textareaRef.current.value.length;
          textareaRef.current.selectionEnd = textareaRef.current.value.length;
          // Trigger resize
          textareaRef.current.style.height = 'auto';
          const lineHeight = 24;
          const maxHeight = lineHeight * MAX_ROWS;
          const newHeight = Math.min(textareaRef.current.scrollHeight, maxHeight);
          textareaRef.current.style.height = `${newHeight}px`;
        }
      }, 0);
    }
  }, [initialPrompt, onInitialPromptConsumed]);

  return (
    <div className="p-4 relative">
      {/* Slash commands menu */}
      <SlashCommandsMenu
        isOpen={showSlashMenu}
        query={input}
        selectedIndex={slashMenuIndex}
        onSelect={handleSlashCommandSelect}
        onClose={() => setShowSlashMenu(false)}
        onIndexChange={setSlashMenuIndex}
        inputRect={inputRect}
        userCommands={userCommands}
      />

      {/* Inline drop zone */}
      <InlineDropZone isDragging={isDragging} />

      {modelUnavailable && (
        <div
          className="mb-3 flex items-start gap-3 rounded-xl border border-warning/35 bg-[var(--color-warning-tint)] px-4 py-3"
          data-testid="chat-model-unavailable"
          role="alert"
        >
          <AlertCircle className="mt-0.5 h-5 w-5 shrink-0 text-warning" />
          <div className="min-w-0 flex-1">
            <p className="text-sm font-semibold text-text">Choisis d’abord un modèle</p>
            <p className="mt-1 text-xs leading-5 text-text-muted">Aucun modèle actif ne peut répondre. Configure une clé cloud ou démarre Ollama avec un modèle local.</p>
          </div>
          <button
            type="button"
            onClick={() => openSettings('ai')}
            className="inline-flex shrink-0 items-center gap-1.5 rounded-lg border border-text bg-surface px-3 py-2 text-xs font-semibold text-text"
          >
            <Settings className="h-3.5 w-3.5" />
            Ouvrir les réglages IA
          </button>
        </div>
      )}

      {/* Tranche 1c : puces d'actions déterministes sur conversation vide -
          un clic insère la syntaxe {action: ...}, l'utilisateur complète et
          envoie (exécution locale, allowlist backend). */}
      {!modelUnavailable && !input && !isStreaming && (currentConversation()?.messages?.length ?? 0) === 0 && (
        <ActionChips onInsert={(text) => setInput(text)} />
      )}

      {/* Chantier 4 : aperçu de résolution des variables {nom} */}
      {variablesPreview && (
        <div
          data-testid="variables-preview-chip"
          className="flex items-center gap-2 mb-2 px-3 py-1.5 rounded-lg text-xs
                     bg-surface-elevated/60 border border-border/40"
        >
          <span className="text-text-muted">
            {(() => {
              const total = (input.match(/(?<!\{)\{[a-z0-9_]{1,32}\}/g) ?? []).length;
              const resolues = total - variablesPreview.unknown.length;
              return `${resolues} variable${resolues > 1 ? 's' : ''} résolue${resolues > 1 ? 's' : ''}`;
            })()}
          </span>
          {variablesPreview.unknown.length > 0 && (
            <span className="text-warning">
              inconnue{variablesPreview.unknown.length > 1 ? 's' : ''} :{' '}
              {variablesPreview.unknown.map((n) => `{${n}}`).join(', ')}
            </span>
          )}
          {variablesPreview.errors.length > 0 && (
            <span className="text-error">{variablesPreview.errors[0]}</span>
          )}
        </div>
      )}

      {/* Attached files */}
      {attachedFiles.length > 0 && (
        <div className="mb-2 flex flex-wrap gap-2" aria-label="Pièces jointes">
          {attachedFiles.map((file, index) => (
            <div key={`${file.path}-${index}`} className="flex flex-wrap items-center gap-1 rounded-lg border border-border bg-surface-elevated p-1">
              <FileChip
                name={file.name}
                mimeType={file.mimeType}
                size={file.size}
                onRemove={() => removeFile(index)}
                className="border-0 bg-transparent"
              />
              <span
                role={file.indexStatus === 'error' ? 'alert' : 'status'}
                aria-live="polite"
                className={`rounded-[6px] px-2 py-1 text-xs font-semibold ${
                  file.indexStatus === 'ready'
                    ? 'bg-[var(--color-success-tint)] text-success'
                    : file.indexStatus === 'error'
                      ? 'bg-[var(--color-error-tint)] text-error'
                      : 'bg-[var(--color-info-tint)] text-info'
                }`}
              >
                {file.indexStatus === 'ready' ? 'Prêt' : file.indexStatus === 'error' ? 'Échec' : 'Indexation'}
              </span>
              {file.indexStatus === 'error' && (
                <button
                  type="button"
                  onClick={() => void indexAttachment(file.path)}
                  className="min-h-11 rounded-[7px] px-2 text-xs font-semibold text-error hover:bg-[var(--color-error-tint)]"
                  aria-label={`Réessayer l’indexation de ${file.name}`}
                >
                  Réessayer
                </button>
              )}
              {file.indexError && <span className="sr-only">{file.indexError}</span>}
            </div>
          ))}
        </div>
      )}

      {/* Bulle prompt en file d'attente */}
      <AnimatePresence>
        {queuedPrompt && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 8 }}
            className="flex items-center gap-2 mb-2 px-4 py-2.5 rounded-xl
                       bg-surface-elevated/60 border border-accent-cyan/20"
          >
            <span className="flex-1 text-sm italic text-text-muted truncate">
              {queuedPrompt}
            </span>
            <button
              type="button"
              onClick={() => setQueuedPrompt(null)}
              aria-label="Annuler le message en file d’attente"
              className="flex-shrink-0 text-text-muted hover:text-text transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* F-12/F-14/F-15 : sélecteur de modèle actif (pill interactif) */}
      {currentModel && !modelUnavailable && (
        <div className="flex items-center px-2 mb-2">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-[6px] bg-accent-cyan/10 border border-accent-cyan/20 hover:border-accent-cyan/40 transition-all">
            <Cpu className="w-3.5 h-3.5 text-accent-cyan" />
            {availableModels.length > 1 ? (
              <select
                aria-label="Modèle de conversation"
                value={currentModel}
                onChange={(e) => handleModelChange(e.target.value)}
                className="text-xs font-medium text-text bg-transparent border-none outline-none cursor-pointer hover:text-accent-cyan transition-colors appearance-none pr-4 [&>option]:bg-[var(--color-surface)] [&>option]:text-[var(--color-text)]"
                style={{ backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='8' height='8' viewBox='0 0 24 24' fill='none' stroke='%2322D3EE' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E")`, backgroundRepeat: 'no-repeat', backgroundPosition: 'right center' }}
              >
                {availableModels.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </select>
            ) : (
              <span className="text-xs font-medium text-text">{currentModel}</span>
            )}
            {currentProvider && (
              <span
                className={`text-xs px-1.5 py-0.5 rounded-[6px] ${
                  currentProvider === 'ollama'
                    ? 'bg-[var(--color-success-tint)] text-success'
                    : 'bg-[var(--color-warning-tint)] text-warning'
                }`}
                title={
                  currentProvider === 'ollama'
                    ? 'Modèle local (Ollama) : le traitement reste sur ta machine'
                    : 'Modèle cloud : le traitement sort vers le fournisseur'
                }
              >
                {currentProvider === 'ollama' ? 'local' : 'cloud'}
              </span>
            )}
          </div>
        </div>
      )}

      {modelChangeError && (
        <div role="alert" className="mb-2 flex items-center gap-2 rounded-[9px] border border-error/40 bg-[var(--color-error-tint)] px-3 py-2 text-xs text-error">
          <AlertCircle className="h-4 w-4 shrink-0" />
          <span className="min-w-0 flex-1">Changement de modèle non enregistré. {modelChangeError}</span>
          {failedModel && (
            <button type="button" onClick={() => void handleModelChange(failedModel)} className="min-h-11 rounded-[7px] border border-error px-2 font-semibold">
              Réessayer
            </button>
          )}
        </div>
      )}

      {pendingCloudConsent && (
        <div role="alertdialog" aria-labelledby="cloud-consent-title" className="mb-3 rounded-xl border border-warning/40 bg-[var(--color-warning-tint)] p-4 text-sm text-warning" data-testid="chat-cloud-consent">
          <p id="cloud-consent-title" className="font-semibold">Autoriser ce premier envoi à {pendingCloudConsent.providerLabel} ?</p>
          <p className="mt-1">Données transmises : {pendingCloudConsent.dataCategories.join(', ')}.</p>
          <div className="mt-3 flex justify-end gap-2">
            <button type="button" onClick={() => setPendingCloudConsent(null)} className="rounded-[8px] border border-border bg-surface px-3 py-2 text-xs font-semibold text-text">Annuler</button>
            <button type="button" onClick={confirmCloudConsent} className="rounded-[8px] bg-text px-3 py-2 text-xs font-semibold text-white">Autoriser et envoyer</button>
          </div>
        </div>
      )}

      <div
        ref={containerRef}
        className={cn(
          'flex items-center gap-2 p-3 rounded-2xl',
          'bg-surface-elevated/80 backdrop-blur-sm border border-border',
          'focus-within:border-accent-cyan/50 focus-within:shadow-[0_0_20px_rgba(34,211,238,0.1)]',
          'hover:border-border/80 transition-all duration-200',
          isDragging && 'border-accent-cyan/50'
        )}
      >
        {/* Attachment button */}
        <Button
          variant="ghost"
          size="icon"
          data-testid="chat-attach-btn"
          className="h-11 w-11 flex-shrink-0"
          disabled={isDisabled}
          onClick={handleAttachClick}
          title={`Joindre un fichier (${/Mac|iPhone|iPad/.test(navigator.platform) ? '⌘' : 'Ctrl+'}O)`}
          aria-label="Joindre un fichier"
        >
          <Paperclip className="w-5 h-5" />
        </Button>

        {/* Textarea + ghost text overlay */}
        <div className="flex-1 relative">
          <label htmlFor="chat-input" className="sr-only">Message à THÉRÈSE</label>
          <textarea
            id="chat-input"
            ref={textareaRef}
            data-testid="chat-message-input"
            value={input}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            placeholder={
              hasQueuedPrompt
                ? 'Un message en file d\'attente'
                : isStreaming
                  ? 'Ajouter un message à la file...'
                  : modelChecking
                    ? 'Vérification du modèle disponible...'
                    : modelUnavailable
                      ? 'Choisis d’abord un modèle dans les réglages IA'
                      : isOffline
                        ? 'En attente de connexion...'
                        : "Comment puis-je t'aider ?"
            }
            disabled={isDisabled}
            rows={MIN_ROWS}
            className={cn(
              'w-full resize-none bg-transparent text-text placeholder:text-text-muted',
              'focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed',
              'text-sm leading-6 py-1.5'
            )}
            style={{ maxHeight: `${24 * MAX_ROWS}px` }}
          />
          {/* Ghost text suggestion overlay */}
          {suggestion && (
            <div
              className="absolute inset-0 pointer-events-none text-sm leading-6 py-1.5 whitespace-pre-wrap break-words"
              aria-hidden="true"
            >
              <span className="invisible">{input}</span>
              <span className="text-text-muted/40">{suggestion}</span>
            </div>
          )}
        </div>

        {/* Voice button */}
        <VoiceDictationButton
          onTranscript={handleTranscript}
          onError={handleVoiceError}
          disabled={isDisabled}
        />

        {/* Send / Stop buttons */}
        {isStreaming && (
          <Button
            variant="primary"
            size="icon"
            className="h-11 w-11 flex-shrink-0 bg-error-fill text-error-ink hover:bg-error-fill/80"
            onClick={stopStreaming}
            title="Arrêter la réponse"
            aria-label="Arrêter la réponse"
          >
            <Square className="w-4 h-4" />
          </Button>
        )}
        {!isStreaming && input.trim() && (
          <Button
            variant="ghost"
            size="icon"
            className="h-11 w-11 flex-shrink-0 text-accent hover:bg-accent-tint"
            onClick={handleDeepResearch}
            disabled={isDisabled || attachedFiles.some((file) => file.indexStatus !== 'ready')}
            title="Recherche approfondie (multi-sources)"
            aria-label="Lancer une recherche approfondie"
          >
            <Search className="w-4 h-4" />
          </Button>
        )}
        <Button
          variant="primary"
          size="icon"
          data-testid="chat-send-btn"
          className="h-11 w-11 flex-shrink-0"
          onClick={sendMessage}
          disabled={isDisabled || !input.trim() || attachedFiles.some((file) => file.indexStatus !== 'ready')}
          title={isStreaming ? 'Envoyer en file d\'attente' : 'Envoyer (↵)'}
          aria-label={isStreaming ? 'Mettre le message en file d’attente' : 'Envoyer le message'}
        >
          <Send className="w-4 h-4" />
        </Button>
      </div>

      {/* Voice error message */}
      {voiceError && (
        <div role="alert" className="mt-2 flex items-start gap-2 rounded-lg border border-error/20 bg-error/10 p-2">
          <p className="flex-1 text-xs text-error">{voiceError}</p>
          <button type="button" onClick={() => setVoiceError(null)} aria-label="Fermer l’erreur de dictée" className="text-error"><X className="h-3.5 w-3.5" /></button>
        </div>
      )}

      {draftError && (
        <div role="alert" className="mt-2 flex items-center gap-2 rounded-lg border border-error/40 bg-[var(--color-error-tint)] p-2 text-xs text-error">
          <p className="min-w-0 flex-1">{draftError}</p>
          <button type="button" onClick={retrySave} className="min-h-11 rounded-[7px] border border-error px-2 font-semibold">Réessayer</button>
        </div>
      )}

      {/* Hidden file input (browser fallback) */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        className="hidden"
        accept=".txt,.md,.pdf,.docx,.xlsx,.json,.csv,.py,.js,.ts,.tsx,.jsx,.html,.css,.png,.jpg,.jpeg,.gif,.webp"
        onChange={handleBrowserFileChange}
      />

      {/* Hints + indicateur sauvegarde */}
      <div className="flex items-center justify-center gap-4 mt-2">
        {showKeyboardHints && <p className="text-xs text-text-muted">
          <kbd className="px-1 rounded bg-surface-elevated">⇧</kbd>+
          <kbd className="px-1 rounded bg-surface-elevated">↵</kbd> nouvelle ligne
        </p>}
        {showKeyboardHints && <p className="text-xs text-text-muted">
          <kbd className="px-1 rounded bg-surface-elevated">{/Mac|iPhone|iPad/.test(navigator.platform) ? '⌘' : 'Ctrl'}</kbd>+
          <kbd className="px-1 rounded bg-surface-elevated">K</kbd> commandes
        </p>}
        {showKeyboardHints && suggestion && (
          <p className="text-xs text-accent-cyan/60">
            <kbd className="px-1 rounded bg-surface-elevated">Tab</kbd> accepter
          </p>
        )}
        {lastSavedAt && (
          <SavedIndicator savedAt={lastSavedAt} />
        )}
      </div>
    </div>
  );
}
