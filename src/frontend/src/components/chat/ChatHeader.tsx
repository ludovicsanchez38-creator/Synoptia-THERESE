import { Settings, Mail, Calendar, CheckSquare, FileText, Users, Briefcase } from 'lucide-react';
import { Button } from '../ui/Button';
import { useChatStore } from '../../stores/chatStore';
import { useDemoStore } from '../../stores/demoStore';
import { getCurrentWindow } from '@tauri-apps/api/window';

interface ChatHeaderProps {
  onOpenSettings?: () => void;
  onToggleEmailPanel?: () => void;
  onToggleCalendarPanel?: () => void;
  onToggleTasksPanel?: () => void;
  onToggleInvoicesPanel?: () => void;
  onToggleCRMPanel?: () => void;
  onToggleMemoryPanel?: () => void;
}

export function ChatHeader({
  onOpenSettings,
  onToggleEmailPanel,
  onToggleCalendarPanel,
  onToggleTasksPanel,
  onToggleInvoicesPanel,
  onToggleCRMPanel,
  onToggleMemoryPanel,
}: ChatHeaderProps) {
  const { createConversation, currentConversation } = useChatStore();
  const demoEnabled = useDemoStore((s) => s.enabled);
  const conversation = currentConversation();
  const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;

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
      className="h-14 flex items-center pl-4 pr-4 border-b border-border/50 bg-surface/60 backdrop-blur-md shadow-[0_1px_3px_rgba(0,0,0,0.2)] relative cursor-default select-none"
      onMouseDown={handleMouseDown}
    >

      {/* Gauche: Window controls (macOS) + Logo */}
      <div className="flex-1 flex items-center gap-4">
        {/* macOS traffic lights */}
        {isMac && (
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
        )}

        {/* Logo + Title (cliquable = nouvelle conversation) */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => createConversation()}
            className="flex items-center gap-2 hover:opacity-80 transition-opacity"
            title={isMac ? 'Nouvelle conversation (⌘N)' : 'Nouvelle conversation (Ctrl+N)'}
          >
            <div className="w-2 h-2 rounded-full bg-accent-cyan shadow-[0_0_8px_rgba(34,211,238,0.5)] animate-pulse" />
            <h1 className="text-lg font-bold gradient-text tracking-tight">THÉRÈSE</h1>
          </button>
          {demoEnabled && (
            <span className="px-2 py-0.5 text-xs font-semibold bg-accent-cyan/20 text-accent-cyan border border-accent-cyan/40 rounded-full animate-pulse">
              Mode Démo
            </span>
          )}
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

      {/* Centre: Navigation (6 boutons) */}
      <div className="flex-shrink-0 flex items-center gap-1">
        <Button
          variant="ghost"
          size="sm"
          onClick={onToggleEmailPanel}
          className="flex items-center gap-1 px-2 py-1 hover:bg-accent-cyan/10"
          title={isMac ? 'Mail (⌘E)' : 'Mail (Ctrl+E)'}
        >
          <Mail className="w-4 h-4" />
          <span className="text-xs">Mail</span>
        </Button>

        <Button
          variant="ghost"
          size="sm"
          onClick={onToggleCalendarPanel}
          className="flex items-center gap-1 px-2 py-1 hover:bg-accent-cyan/10"
          title={isMac ? 'Calendrier (⌘⇧C)' : 'Calendrier (Ctrl+Shift+C)'}
        >
          <Calendar className="w-4 h-4" />
          <span className="text-xs">Calendrier</span>
        </Button>

        <Button
          variant="ghost"
          size="sm"
          onClick={onToggleTasksPanel}
          className="flex items-center gap-1 px-2 py-1 hover:bg-accent-cyan/10"
          title={isMac ? 'Tâches (⌘T)' : 'Tâches (Ctrl+T)'}
        >
          <CheckSquare className="w-4 h-4" />
          <span className="text-xs">Tâches</span>
        </Button>

        <Button
          variant="ghost"
          size="sm"
          onClick={onToggleMemoryPanel}
          className="flex items-center gap-1 px-2 py-1 hover:bg-accent-cyan/10"
          title={isMac ? 'Projet (⌘M)' : 'Projet (Ctrl+M)'}
        >
          <Briefcase className="w-4 h-4" />
          <span className="text-xs">Projet</span>
        </Button>

        <Button
          variant="ghost"
          size="sm"
          onClick={onToggleCRMPanel}
          className="flex items-center gap-1 px-2 py-1 hover:bg-accent-cyan/10"
          title={isMac ? 'CRM (⌘P)' : 'CRM (Ctrl+P)'}
        >
          <Users className="w-4 h-4" />
          <span className="text-xs">CRM</span>
        </Button>

        <Button
          variant="ghost"
          size="sm"
          onClick={onToggleInvoicesPanel}
          className="flex items-center gap-1 px-2 py-1 hover:bg-accent-cyan/10"
          title={isMac ? 'Facture (⌘I)' : 'Facture (Ctrl+I)'}
        >
          <FileText className="w-4 h-4" />
          <span className="text-xs">Facture</span>
        </Button>
      </div>

      {/* Droite: Paramètres + Window controls */}
      <div className="flex-1 flex items-center justify-end gap-2">
        <Button variant="ghost" size="icon" title="Paramètres" onClick={onOpenSettings}>
          <Settings className="w-5 h-5" />
        </Button>

        {/* Windows/Linux window controls */}
        {!isMac && (
          <>
            <div className="h-6 w-px bg-border/50" />
            <button
              onClick={handleMinimize}
              className="w-8 h-8 flex items-center justify-center text-text-muted hover:text-text hover:bg-surface-elevated/80 rounded transition-colors"
              title="Réduire"
            >
              <span className="text-xs leading-none">─</span>
            </button>
            <button
              onClick={handleMaximize}
              className="w-8 h-8 flex items-center justify-center text-text-muted hover:text-text hover:bg-surface-elevated/80 rounded transition-colors"
              title="Agrandir"
            >
              <span className="text-xs leading-none">□</span>
            </button>
            <button
              onClick={handleClose}
              className="w-8 h-8 flex items-center justify-center text-text-muted hover:text-white hover:bg-red-500 rounded transition-colors"
              title="Fermer"
            >
              <span className="text-xs leading-none">✕</span>
            </button>
          </>
        )}
      </div>
    </header>
  );
}
