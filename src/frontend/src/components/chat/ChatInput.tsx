import {
  useState,
  useRef,
  useCallback,
  useEffect,
  type KeyboardEvent,
  type ChangeEvent,
} from 'react';
import { Send, Paperclip, Mic, MicOff, Loader2 } from 'lucide-react';
import { open } from '@tauri-apps/plugin-dialog';
import { Button } from '../ui/Button';
import { SlashCommandsMenu, detectSlashCommand, type SlashCommand } from './SlashCommandsMenu';
import { InlineDropZone, FileChip } from '../files/DropZone';
import { useChatStore } from '../../stores/chatStore';
import { useStatusStore } from '../../stores/statusStore';
import { useFileDrop, type DroppedFile } from '../../hooks/useFileDrop';
import { useVoiceRecorder } from '../../hooks/useVoiceRecorder';
import { streamMessage, indexFile, ApiError } from '../../services/api';
import { cn } from '../../lib/utils';

const MAX_ROWS = 8;

interface ChatInputProps {
  onOpenCommandPalette?: () => void;
  initialPrompt?: string;
  onInitialPromptConsumed?: () => void;
  userCommands?: import('./SlashCommandsMenu').SlashCommand[];
}

export function ChatInput({ onOpenCommandPalette, initialPrompt, onInitialPromptConsumed, userCommands }: ChatInputProps) {
  const [input, setInput] = useState('');
  const [showSlashMenu, setShowSlashMenu] = useState(false);
  const [slashMenuIndex, setSlashMenuIndex] = useState(0);
  const [inputRect, setInputRect] = useState<DOMRect | null>(null);
  const [attachedFiles, setAttachedFiles] = useState<DroppedFile[]>([]);
  const [isIndexing, setIsIndexing] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

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
  } = useChatStore();
  const { connectionState, setActivity } = useStatusStore();

  const isDisabled = connectionState !== 'connected' || isStreaming;

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
  const [voiceSupported, setVoiceSupported] = useState(true);

  // Check voice support on mount
  useEffect(() => {
    const checkVoiceSupport = () => {
      // Check if we're in Tauri and if MediaRecorder is available
      const isTauri = '__TAURI__' in window || '__TAURI_INTERNALS__' in window;
      const hasMediaDevices = !!(navigator.mediaDevices?.getUserMedia);
      const hasMediaRecorder = typeof MediaRecorder !== 'undefined';

      if (isTauri && (!hasMediaDevices || !hasMediaRecorder)) {
        setVoiceSupported(false);
      }
    };
    checkVoiceSupport();
  }, []);

  const handleVoiceError = useCallback((error: string) => {
    console.error('Voice recording error:', error);
    setVoiceError(error);
    // Auto-clear error after 5 seconds
    setTimeout(() => setVoiceError(null), 5000);
  }, []);

  const {
    isRecording,
    isProcessing,
    toggleRecording,
  } = useVoiceRecorder({
    onTranscript: handleTranscript,
    onError: handleVoiceError,
  });

  // Remove attached file
  const removeFile = useCallback((index: number) => {
    setAttachedFiles((prev) => prev.filter((_, i) => i !== index));
  }, []);

  // Open file picker
  const handleAttachClick = useCallback(async () => {
    if (isDisabled) return;

    try {
      const selected = await open({
        multiple: true,
        filters: [
          {
            name: 'Documents',
            extensions: ['txt', 'md', 'pdf', 'doc', 'docx', 'json', 'csv'],
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
    } catch (err) {
      console.error('File picker error:', err);
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

    // Reset height to calculate new height
    textarea.style.height = 'auto';
    const lineHeight = 24;
    const maxHeight = lineHeight * MAX_ROWS;
    const newHeight = Math.min(textarea.scrollHeight, maxHeight);
    textarea.style.height = `${newHeight}px`;
  }, []);

  const sendMessage = useCallback(async () => {
    const trimmed = input.trim();
    if (!trimmed || isDisabled) return;

    // Close slash menu if open
    setShowSlashMenu(false);

    // Build message content with file attachments
    let messageContent = trimmed;
    if (attachedFiles.length > 0) {
      const filesList = attachedFiles.map((f) => f.name).join(', ');
      messageContent = `${trimmed}\n\n[Fichiers joints: ${filesList}]`;
    }

    // Add user message
    addMessage({ role: 'user', content: messageContent });
    setInput('');
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

    // Sprint 2 - PERF-2.7: Batching SSE updates with requestAnimationFrame
    // This reduces re-renders from ~50/sec to max 60fps (frame-aligned)
    let pendingUpdate = false;
    let rafId: number | null = null;

    const batchedUpdateMessage = (content: string) => {
      accumulatedContent = content;
      if (!pendingUpdate) {
        pendingUpdate = true;
        rafId = requestAnimationFrame(() => {
          updateMessage(assistantMessageId, accumulatedContent);
          pendingUpdate = false;
        });
      }
    };

    try {
      // Only send conversation_id if it's synced with backend
      const conversation = currentConversation();
      const syncedConversationId = conversation?.synced ? currentConversationId : undefined;

      // Stream response from backend
      const stream = streamMessage({
        message: trimmed,
        conversation_id: syncedConversationId || undefined,
        include_memory: true,
        stream: true,
      });

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
          // Accumulate content and batch update (Sprint 2 - PERF-2.7)
          accumulatedContent += chunk.content;
          setActivity('streaming', "En train d'écrire...");
          batchedUpdateMessage(accumulatedContent);
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

      // Cancel any pending RAF and do final update (Sprint 2 - PERF-2.7)
      if (rafId !== null) {
        cancelAnimationFrame(rafId);
      }
      // Finalize the message (remove streaming flag)
      updateMessage(assistantMessageId, accumulatedContent);
    } catch (error) {
      // Cancel any pending RAF on error (Sprint 2 - PERF-2.7)
      if (rafId !== null) {
        cancelAnimationFrame(rafId);
      }
      console.error('Error sending message:', error);
      const errorMessage = error instanceof ApiError
        ? `Erreur serveur (${error.status}): ${error.message}`
        : error instanceof Error
          ? error.message
          : "Désolée, une erreur s'est produite. Veuillez réessayer.";

      // Update the placeholder message with error
      updateMessage(assistantMessageId, errorMessage);
    } finally {
      setStreaming(false);
      setActivity('idle');
    }
  }, [input, isDisabled, addMessage, updateMessage, setMessageEntities, setMessageMetadata, setStreaming, setActivity, currentConversationId, currentConversation, updateConversationId]);

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
    [sendMessage, showSlashMenu, onOpenCommandPalette]
  );

  // Focus textarea on mount
  useEffect(() => {
    textareaRef.current?.focus();
  }, []);

  // Consume initial prompt from guided prompts
  useEffect(() => {
    if (initialPrompt) {
      setInput(initialPrompt);
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

      <div
        ref={containerRef}
        className={cn(
          'flex items-end gap-2 p-3 rounded-2xl',
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
          title="Joindre un fichier (⌘+O)"
        >
          <Paperclip className="w-5 h-5" />
        </Button>

        {/* Textarea */}
        <textarea
          ref={textareaRef}
          value={input}
          onChange={handleInput}
          onKeyDown={handleKeyDown}
          placeholder={
            isStreaming
              ? 'THÉRÈSE réfléchit...'
              : connectionState !== 'connected'
                ? 'En attente de connexion...'
                : 'Comment puis-je vous aider ?'
          }
          disabled={isDisabled}
          rows={1}
          className={cn(
            'flex-1 resize-none bg-transparent text-text placeholder:text-text-muted',
            'focus:outline-none disabled:opacity-50 disabled:cursor-not-allowed',
            'text-sm leading-6 py-1.5'
          )}
          style={{ maxHeight: `${24 * MAX_ROWS}px` }}
        />

        {/* Voice button */}
        <Button
          variant={isRecording ? 'primary' : 'ghost'}
          size="icon"
          className={cn(
            'flex-shrink-0 h-9 w-9 transition-all',
            isRecording && 'bg-error hover:bg-error/90 animate-pulse',
            !voiceSupported && 'opacity-50 cursor-not-allowed'
          )}
          disabled={isDisabled || isProcessing || !voiceSupported}
          onClick={voiceSupported ? toggleRecording : undefined}
          title={
            !voiceSupported
              ? 'Dictée vocale non disponible (prochainement)'
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

        {/* Send button */}
        <Button
          variant="primary"
          size="icon"
          className="flex-shrink-0 h-9 w-9"
          onClick={sendMessage}
          disabled={isDisabled || !input.trim()}
          title="Envoyer (↵)"
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

      {/* Hints */}
      <div className="flex items-center justify-center gap-4 mt-2">
        <p className="text-xs text-text-muted">
          <kbd className="px-1 rounded bg-surface-elevated">⇧</kbd>+
          <kbd className="px-1 rounded bg-surface-elevated">↵</kbd> nouvelle ligne
        </p>
        <p className="text-xs text-text-muted">
          <kbd className="px-1 rounded bg-surface-elevated">⌘</kbd>+
          <kbd className="px-1 rounded bg-surface-elevated">K</kbd> commandes
        </p>
      </div>
    </div>
  );
}
