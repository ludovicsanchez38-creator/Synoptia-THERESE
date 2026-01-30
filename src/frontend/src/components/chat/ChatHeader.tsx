import { Plus, Settings, Command, Mail, Calendar, CheckSquare, FileText, Users } from 'lucide-react';
import { ConnectionStatus } from '../ui/ConnectionStatus';
import { Button } from '../ui/Button';
import { useChatStore } from '../../stores/chatStore';
import { getCurrentWindow } from '@tauri-apps/api/window';

interface ChatHeaderProps {
  onOpenCommandPalette?: () => void;
  onOpenSettings?: () => void;
  onToggleEmailPanel?: () => void;
  onToggleCalendarPanel?: () => void;
  onToggleTasksPanel?: () => void;
  onToggleInvoicesPanel?: () => void;
  onToggleCRMPanel?: () => void;
}

export function ChatHeader({
  onOpenCommandPalette,
  onOpenSettings,
  onToggleEmailPanel,
  onToggleCalendarPanel,
  onToggleTasksPanel,
  onToggleInvoicesPanel,
  onToggleCRMPanel,
}: ChatHeaderProps) {
  const { createConversation, currentConversation, isCurrentConversationEmpty } = useChatStore();
  const conversation = currentConversation();
  const isEmpty = isCurrentConversationEmpty();

  // Drag window handler
  const handleMouseDown = async (e: React.MouseEvent) => {
    // Only drag on left click and not on interactive elements
    if (e.button !== 0) return;
    const target = e.target as HTMLElement;
    if (target.closest('button')) return;

    try {
      await getCurrentWindow().startDragging();
    } catch (err) {
      console.error('Failed to start dragging:', err);
    }
  };

  // Window controls
  const handleMinimize = () => getCurrentWindow().minimize();
  const handleMaximize = () => getCurrentWindow().toggleMaximize();
  const handleClose = () => getCurrentWindow().close();

  return (
    <header
      className="h-14 flex items-center justify-between pl-4 pr-4 border-b border-border/50 bg-surface/60 backdrop-blur-md shadow-[0_1px_3px_rgba(0,0,0,0.2)] relative cursor-default select-none"
      onMouseDown={handleMouseDown}
    >

      {/* Left: Window controls (macOS style) + Logo */}
      <div className="flex items-center gap-4">
        {/* Window controls */}
        <div className="flex items-center gap-2">
          <button
            onClick={handleClose}
            className="w-3 h-3 rounded-full bg-red-500 hover:bg-red-600 transition-colors"
            title="Fermer"
          />
          <button
            onClick={handleMinimize}
            className="w-3 h-3 rounded-full bg-yellow-500 hover:bg-yellow-600 transition-colors"
            title="Réduire"
          />
          <button
            onClick={handleMaximize}
            className="w-3 h-3 rounded-full bg-green-500 hover:bg-green-600 transition-colors"
            title="Agrandir"
          />
        </div>

        {/* Logo + Title */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-accent-cyan shadow-[0_0_8px_rgba(34,211,238,0.5)] animate-pulse" />
            <h1 className="text-lg font-bold gradient-text tracking-tight">THÉRÈSE</h1>
          </div>
          {conversation && (
            <>
              <span className="text-border/60">/</span>
              <span className="text-sm text-text-muted truncate max-w-[200px]">
                {conversation.title}
              </span>
            </>
          )}
        </div>
      </div>

      {/* Right: Actions + Status */}
      <div className="flex items-center gap-2">
        <ConnectionStatus />

        {/* Core Features */}
        <Button
          variant="ghost"
          size="icon"
          onClick={onToggleEmailPanel}
          title="Email (⌘E)"
        >
          <Mail className="w-5 h-5" />
        </Button>

        <Button
          variant="ghost"
          size="icon"
          onClick={onToggleCalendarPanel}
          title="Calendar (⌘⇧C)"
        >
          <Calendar className="w-5 h-5" />
        </Button>

        <Button
          variant="ghost"
          size="icon"
          onClick={onToggleTasksPanel}
          title="Tasks (⌘T)"
        >
          <CheckSquare className="w-5 h-5" />
        </Button>

        <Button
          variant="ghost"
          size="icon"
          onClick={onToggleInvoicesPanel}
          title="Invoices (⌘I)"
        >
          <FileText className="w-5 h-5" />
        </Button>

        <Button
          variant="ghost"
          size="icon"
          onClick={onToggleCRMPanel}
          title="CRM Pipeline (⌘P)"
        >
          <Users className="w-5 h-5" />
        </Button>

        {/* Separateur */}
        <div className="h-6 w-px bg-border/50" />

        {/* Global actions */}
        <Button
          variant="ghost"
          size="icon"
          onClick={onOpenCommandPalette}
          title="Commandes (⌘K)"
        >
          <Command className="w-5 h-5" />
        </Button>

        <Button
          variant="ghost"
          size="icon"
          onClick={() => createConversation()}
          disabled={isEmpty}
          title={isEmpty ? "Conversation vide" : "Nouvelle conversation (⌘N)"}
          className={isEmpty ? "opacity-40 cursor-not-allowed" : ""}
        >
          <Plus className="w-5 h-5" />
        </Button>

        <Button variant="ghost" size="icon" title="Paramètres" onClick={onOpenSettings}>
          <Settings className="w-5 h-5" />
        </Button>
      </div>
    </header>
  );
}
