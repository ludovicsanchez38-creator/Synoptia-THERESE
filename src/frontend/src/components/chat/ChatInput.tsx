import {
  useState,
  useRef,
  useCallback,
  useEffect,
  type KeyboardEvent,
  type ChangeEvent,
} from 'react';
import { Send, Square, Paperclip, Mic, MicOff, Loader2, X, Cpu, Search } from 'lucide-react';
import { AnimatePresence, motion } from 'framer-motion';
import { open } from '@tauri-apps/plugin-dialog';
import { Button } from '../ui/Button';
import { SlashCommandsMenu, detectSlashCommand, type SlashCommand } from './SlashCommandsMenu';
import { InlineDropZone, FileChip } from '../files/DropZone';
import { useChatStore } from '../../stores/chatStore';
import { useStatusStore } from '../../stores/statusStore';
import { useFileDrop, type DroppedFile } from '../../hooks/useFileDrop';
import { useVoiceRecorder } from '../../hooks/useVoiceRecorder';
import { streamMessage, streamDeepResearch, indexFile, ApiError, getLLMConfig, setLLMConfig, type LLMProvider } from '../../services/api';
import { useGhostText } from '../../hooks/useGhostText';
import { useAutosave } from '../../hooks/useAutosave';
import { cn } from '../../lib/utils';

const MIN_ROWS = 2;
const MAX_ROWS = 12;

interface ChatInputProps {
  onOpenCommandPalette?: () => void;
  initialPrompt?: string;
  initialSkillId?: string;
  onInitialPromptConsumed?: () => void;
  userCommands?: import('./SlashCommandsMenu').SlashCommand[];
}


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
    <p className="text-xs text-text-muted/50">
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
  const [attachedFiles, setAttachedFiles] = useState<DroppedFile[]>([]);
  const [isIndexing, setIsIndexing] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<AbortController | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const {
    addMessage,
    updateMessage,
    setMessageEntities,
    setMessageMetadata,
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

  // US-007 : Autosave brouillon
  const { saveDraft, restoreDraft, clearDraft, lastSavedAt } = useAutosave(currentConversationId);

  const isOffline = connectionState !== 'connected';
  const hasQueuedPrompt = queuedPrompt !== null;
  const isDisabled = isOffline || hasQueuedPrompt;

  // F-12 : modèle LLM actif + sélecteur rapide
  const [currentModel, setCurrentModel] = useState<string | null>(null);
  const [currentProvider, setCurrentProvider] = useState<LLMProvider | null>(null);
  const [availableModels, setAvailableModels] = useState<string[]>([]);

  const loadLLMConfig = useCallback(() => {
    getLLMConfig()
      .then((cfg) => {
        setCurrentModel(cfg.model);
        setCurrentProvider(cfg.provider);
        setAvailableModels(cfg.available_models || []);
      })
      .catch(() => {});
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
    try {
      const cfg = await setLLMConfig(currentProvider, newModel);
      setCurrentModel(cfg.model);
      setAvailableModels(cfg.available_models || []);
      window.dispatchEvent(new Event('therese:llm-config-changed'));
    } catch {
      // Silently fail - model stays unchanged
    }
  }, [currentProvider, currentModel]);

  // Ghost text prédictif
  const { suggestion, accept: acceptGhost, dismiss: dismissGhost } = useGhostText(
    input,
    currentConversationId,
    isStreaming,
  );

  // File drop handling (with deduplication)
  const handleFilesDropped = useCallback(async (files: DroppedFile[]) => {
    setAttachedFiles((prev) => {
      // Deduplicate by path
      const existingPaths = new Set(prev.map((f) => f.path));
      const newFiles = files.filter((f) => !existingPaths.has(f.path));
      return [...prev, ...newFiles];
    });

    // Auto-index dropped files
    setIsIndexing(true);
    try {
      for (const file of files) {
        await indexFile(file.path);
      }
    } catch (err) {
      console.error('Failed to index files:', err);
    } finally {
      setIsIndexing(false);
    }
  }, []);

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
  }, []);

  const [voiceError, setVoiceError] = useState<string | null>(null);
  // Voice is always supported now (Tauri plugin or Web API fallback)
  const voiceSupported = true;

  const handleVoiceError = useCallback((error: string) => {
    console.error('Voice recording error:', error);
    setVoiceError(error);
    // Auto-clear error after 5 seconds
    setTimeout(() => setVoiceError(null), 5000);
  }, []);

  const {
    isRecording,
    isProcessing,
    pluginReady,
    toggleRecording,
  } = useVoiceRecorder({
    onTranscript: handleTranscript,
    onError: handleVoiceError,
  });

  // Remove attached file
  const removeFile = useCallback((index: number) => {
    setAttachedFiles((prev) => prev.filter((_, i) => i !== index));
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

  const sendMessage = useCallback(async () => {
    const trimmed = input.trim();
    if (!trimmed || isOffline) return;

    // Si streaming en cours, mettre en file d'attente (1 seul)
    if (isStreaming) {
      setQueuedPrompt(trimmed);
      setInput('');
      if (textareaRef.current) textareaRef.current.style.height = 'auto';
      return;
    }

    // Close slash menu if open
    setShowSlashMenu(false);

    // Build message content with file attachments
    // BUG-044 : capturer les paths AVANT le clear pour les envoyer au backend
    const filePaths = attachedFiles.length > 0
      ? attachedFiles.map((f) => f.path)
      : undefined;
    let messageContent = trimmed;
    if (attachedFiles.length > 0) {
      const filesList = attachedFiles.map((f) => f.name).join(', ');
      messageContent = `${trimmed}\n\n[Fichiers joints: ${filesList}]`;
    }

    // Add user message
    addMessage({ role: 'user', content: messageContent });
    setInput('');
    clearDraft(); // US-007 : Supprimer le brouillon après envoi
    setAttachedFiles([]); // Clear attached files after sending

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
        updateMessage(assistantMessageId, displayedContent);
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
        } else if (chunk.type === 'done') {
          // Store usage and uncertainty metadata (US-ESC-02, US-ESC-01)
          if (chunk.usage || chunk.uncertainty) {
            setMessageMetadata(assistantMessageId, chunk.usage, chunk.uncertainty);
          }
        } else if (chunk.type === 'error') {
          throw new Error(chunk.content || "Erreur lors de la génération");
        }
      }

      // Stop batching and do final update
      stopBatching();
      // Finalize the message (remove streaming flag)
      updateMessage(assistantMessageId, accumulatedContent);
    } catch (error) {
      // Stop batching on error
      stopBatching();
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
  }, [input, isOffline, isStreaming, addMessage, updateMessage, setMessageEntities, setMessageMetadata, setStreaming, setActivity, currentConversationId, currentConversation, updateConversationId, deleteConversation, setQueuedPrompt]);

  // Recherche approfondie
  const handleDeepResearch = useCallback(async () => {
    const trimmed = input.trim();
    if (!trimmed || isOffline || isStreaming) return;

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
  }, [input, isOffline, isStreaming, addMessage, updateMessage, setStreaming, setActivity, currentConversationId, currentConversation, updateConversationId]);

  // Ref stable pour sendMessage (évite dépendances circulaires dans useEffect)
  const sendMessageRef = useRef(sendMessage);
  sendMessageRef.current = sendMessage;

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

      {/* Attached files */}
      {attachedFiles.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-2">
          {attachedFiles.map((file, index) => (
            <FileChip
              key={`${file.path}-${index}`}
              name={file.name}
              mimeType={file.mimeType}
              size={file.size}
              onRemove={() => removeFile(index)}
            />
          ))}
          {isIndexing && (
            <span className="text-xs text-text-muted self-center ml-2">
              Indexation...
            </span>
          )}
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
              onClick={() => setQueuedPrompt(null)}
              className="flex-shrink-0 text-text-muted/60 hover:text-text transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* F-12/F-14/F-15 : sélecteur de modèle actif (pill interactif) */}
      {currentModel && (
        <div className="flex items-center px-2 mb-2">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-accent-cyan/10 border border-accent-cyan/20 hover:border-accent-cyan/40 transition-all">
            <Cpu className="w-3.5 h-3.5 text-accent-cyan" />
            {availableModels.length > 1 ? (
              <select
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
          className="flex-shrink-0 h-9 w-9"
          disabled={isDisabled}
          onClick={handleAttachClick}
          title={`Joindre un fichier (${/Mac|iPhone|iPad/.test(navigator.platform) ? '⌘' : 'Ctrl+'}O)`}
        >
          <Paperclip className="w-5 h-5" />
        </Button>

        {/* Textarea + ghost text overlay */}
        <div className="flex-1 relative">
          <label htmlFor="chat-input" className="sr-only">Message à THÉRÈSE</label>
          <textarea
            id="chat-input"
            ref={textareaRef}
            value={input}
            onChange={handleInput}
            onKeyDown={handleKeyDown}
            placeholder={
              hasQueuedPrompt
                ? 'Un message en file d\'attente'
                : isStreaming
                  ? 'Ajouter un message à la file...'
                  : isOffline
                    ? 'En attente de connexion...'
                    : 'Comment puis-je t'aider ?'
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
        <Button
          variant={isRecording ? 'primary' : 'ghost'}
          size="icon"
          className={cn(
            'flex-shrink-0 h-9 w-9 transition-all',
            isRecording && 'bg-error hover:bg-error/90 animate-pulse',
            !voiceSupported && 'opacity-50 cursor-not-allowed'
          )}
          disabled={isDisabled || isProcessing || !voiceSupported || !pluginReady}
          onClick={voiceSupported && pluginReady ? toggleRecording : undefined}
          title={
            !voiceSupported
              ? 'Dictée vocale non disponible (prochainement)'
              : !pluginReady
                ? 'Chargement du micro...'
              : isProcessing
                ? 'Transcription en cours...'
                : isRecording
                  ? 'Arrêter l\'enregistrement'
                  : 'Message vocal'
          }
        >
          {isProcessing ? (
            <Loader2 className="w-5 h-5 animate-spin" />
          ) : isRecording ? (
            <MicOff className="w-5 h-5" />
          ) : (
            <Mic className={cn('w-5 h-5', !voiceSupported && 'text-text-muted')} />
          )}
        </Button>

        {/* Send / Stop buttons */}
        {isStreaming && (
          <Button
            variant="primary"
            size="icon"
            className="flex-shrink-0 h-9 w-9 bg-error hover:bg-error/80"
            onClick={stopStreaming}
            title="Arrêter la réponse"
          >
            <Square className="w-4 h-4" />
          </Button>
        )}
        {!isStreaming && input.trim() && (
          <Button
            variant="ghost"
            size="icon"
            className="flex-shrink-0 h-9 w-9 text-accent-cyan hover:bg-accent-cyan/10"
            onClick={handleDeepResearch}
            disabled={isDisabled}
            title="Recherche approfondie (multi-sources)"
          >
            <Search className="w-4 h-4" />
          </Button>
        )}
        <Button
          variant="primary"
          size="icon"
          className="flex-shrink-0 h-9 w-9"
          onClick={sendMessage}
          disabled={isDisabled || !input.trim()}
          title={isStreaming ? 'Envoyer en file d\'attente' : 'Envoyer (↵)'}
        >
          <Send className="w-4 h-4" />
        </Button>
      </div>

      {/* Voice error message */}
      {voiceError && (
        <div className="mt-2 p-2 rounded-lg bg-error/10 border border-error/20">
          <p className="text-xs text-error">{voiceError}</p>
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
        <p className="text-xs text-text-muted">
          <kbd className="px-1 rounded bg-surface-elevated">⇧</kbd>+
          <kbd className="px-1 rounded bg-surface-elevated">↵</kbd> nouvelle ligne
        </p>
        <p className="text-xs text-text-muted">
          <kbd className="px-1 rounded bg-surface-elevated">{/Mac|iPhone|iPad/.test(navigator.platform) ? '⌘' : 'Ctrl'}</kbd>+
          <kbd className="px-1 rounded bg-surface-elevated">K</kbd> commandes
        </p>
        {suggestion && (
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
