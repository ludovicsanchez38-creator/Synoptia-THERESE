import { useState } from 'react';
import { MessageSquare, PanelRightClose } from 'lucide-react';
import { MessageList } from '../chat/MessageList';
import { ChatInput } from '../chat/ChatInput';
import { ConversationMemoryChip } from '../chat/ConversationMemoryChip';
import { ConnectionStatus } from '../ui/ConnectionStatus';
import { useChatStore } from '../../stores/chatStore';
import { usePanelStore } from '../../stores/panelStore';
import type { SlashCommand } from '../chat/SlashCommandsMenu';

interface PrototypeChatSurfaceProps {
  initialPrompt: string | null;
  userCommands: SlashCommand[];
  onInitialPromptConsumed: () => void;
  onOpenCommandPalette: () => void;
  onClose: () => void;
}

export function PrototypeChatSurface({
  initialPrompt,
  userCommands,
  onInitialPromptConsumed,
  onOpenCommandPalette,
  onClose,
}: PrototypeChatSurfaceProps) {
  const [guidedPrompt, setGuidedPrompt] = useState<string | undefined>();
  const [guidedSkillId, setGuidedSkillId] = useState<string | undefined>();
  const [guidedPanelActive, setGuidedPanelActive] = useState(false);
  const conversations = useChatStore((state) => state.conversations);
  const currentConversationId = useChatStore((state) => state.currentConversationId);
  const conversation = conversations.find((item) => item.id === currentConversationId) ?? null;
  const openSaveCommand = usePanelStore((state) => state.openSaveCommand);

  const consumed = () => {
    setGuidedPrompt(undefined);
    setGuidedSkillId(undefined);
    onInitialPromptConsumed();
  };

  return (
    <section className="relative flex min-w-0 flex-1 flex-col overflow-hidden bg-bg" data-testid="prototype-chat-surface">
      <header className="flex h-12 shrink-0 items-center gap-3 border-b border-border bg-surface px-4">
        <span className="grid h-7 w-7 place-items-center rounded-[8px] bg-accent-tint text-accent">
          <MessageSquare className="h-4 w-4" />
        </span>
        <div className="min-w-0 flex-1">
          <h2 className="truncate text-sm font-semibold text-text">{conversation?.title || 'Nouvelle conversation'}</h2>
          <p className="text-[10px] text-text-muted">Conversation réelle, historique et fichiers conservés</p>
        </div>
        <ConnectionStatus />
        <button type="button" onClick={onClose} aria-label="Fermer la conversation" className="grid h-8 w-8 place-items-center rounded-[9px] border border-border bg-surface text-text-muted hover:text-text">
          <PanelRightClose className="h-4 w-4" />
        </button>
      </header>

      <div className="min-h-0 flex-1 overflow-hidden">
        <MessageList
          onPromptSelect={(prompt, skillId) => {
            setGuidedPrompt(prompt);
            setGuidedSkillId(skillId);
          }}
          onSaveAsCommand={openSaveCommand}
          onGuidedPanelChange={setGuidedPanelActive}
        />
      </div>
      {!guidedPanelActive && (
        <>
          <ConversationMemoryChip />
          <div className="shrink-0 border-t border-border bg-surface">
            <ChatInput
              onOpenCommandPalette={onOpenCommandPalette}
              initialPrompt={guidedPrompt ?? initialPrompt ?? undefined}
              initialSkillId={guidedSkillId}
              onInitialPromptConsumed={consumed}
              userCommands={userCommands}
            />
          </div>
        </>
      )}
    </section>
  );
}
