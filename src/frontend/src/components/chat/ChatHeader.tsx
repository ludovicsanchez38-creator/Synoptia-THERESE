import { Settings, Mail, Calendar, CheckSquare, FileText, Users, Briefcase, Zap } from 'lucide-react';
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
  onToggleBoardPanel?: () => void;
  onToggleAtelierPanel?: () => void;
}

export function ChatHeader({
  onOpenSettings,
  onToggleEmailPanel,
  onToggleCalendarPanel,
  onToggleTasksPanel,
  onToggleInvoicesPanel,
  onToggleCRMPanel,
  onToggleMemoryPanel,
  onToggleBoardPanel,
  onToggleAtelierPanel,
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
      <div className="flex-1 min-w-0 flex items-center gap-4">
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

      {/* Centre: Navigation (6 boutons icônes) */}
      <div className="flex-shrink-0 flex items-center gap-0.5 px-2 py-1 rounded-lg bg-surface-elevated/50 border border-border/40">
        <Button
          variant="ghost"
          size="icon"
          onClick={onToggleEmailPanel}
          className="w-8 h-8 hover:bg-accent-cyan/10"
          title={isMac ? 'Mail (⌘E)' : 'Mail (Ctrl+E)'}
        >
          <Mail className="w-4 h-4" />
        </Button>

        <Button
          variant="ghost"
          size="icon"
          onClick={onToggleCalendarPanel}
          className="w-8 h-8 hover:bg-accent-cyan/10"
          title={isMac ? 'Calendrier (⌘⇧C)' : 'Calendrier (Ctrl+Shift+C)'}
        >
          <Calendar className="w-4 h-4" />
        </Button>

        <Button
          variant="ghost"
          size="icon"
          onClick={onToggleTasksPanel}
          className="w-8 h-8 hover:bg-accent-cyan/10"
          title={isMac ? 'Tâches (⌘T)' : 'Tâches (Ctrl+T)'}
        >
          <CheckSquare className="w-4 h-4" />
        </Button>

        {/* Board - icône custom 5 conseillers colorés */}
        <Button
          variant="ghost"
          size="icon"
          onClick={onToggleBoardPanel}
          className="w-8 h-8 hover:bg-accent-cyan/15"
          title={isMac ? 'Board (⌘D)' : 'Board (Ctrl+D)'}
        >
          <svg width="24" height="24" viewBox="0 0 40 40" fill="none" className="shrink-0">
            <circle cx="20" cy="20" r="5.5" fill="#E6EDF7" />
            <circle cx="20" cy="8" r="3" stroke="#22D3EE" strokeWidth="1.5" />
            <circle cx="31.4" cy="16.3" r="3" stroke="#A855F7" strokeWidth="1.5" />
            <circle cx="27.1" cy="29.7" r="3" stroke="#EF4444" strokeWidth="1.5" />
            <circle cx="12.9" cy="29.7" r="3" stroke="#F59E0B" strokeWidth="1.5" />
            <circle cx="8.6" cy="16.3" r="3" stroke="#E11D8D" strokeWidth="1.5" />
          </svg>
        </Button>

        <Button
          variant="ghost"
          size="icon"
          onClick={onToggleMemoryPanel}
          className="w-8 h-8 hover:bg-accent-cyan/10"
          title={isMac ? 'Projet (⌘M)' : 'Projet (Ctrl+M)'}
        >
          <Briefcase className="w-4 h-4" />
        </Button>

        <Button
          variant="ghost"
          size="icon"
          onClick={onToggleCRMPanel}
          className="w-8 h-8 hover:bg-accent-cyan/10"
          title={isMac ? 'CRM (⌘P)' : 'CRM (Ctrl+P)'}
        >
          <Users className="w-4 h-4" />
        </Button>

        <Button
          variant="ghost"
          size="icon"
          onClick={onToggleInvoicesPanel}
          className="w-8 h-8 hover:bg-accent-cyan/10"
          title={isMac ? 'Facture (⌘I)' : 'Facture (Ctrl+I)'}
        >
          <FileText className="w-4 h-4" />
        </Button>
      </div>

      {/* Droite: Atelier + Paramètres + Window controls */}
      <div className="flex-1 flex items-center justify-end gap-2">
        <Button
          variant="ghost"
          size="icon"
          onClick={onToggleAtelierPanel}
          className="w-8 h-8 hover:bg-purple-500/15"
          title={isMac ? 'Atelier (⌘⇧A)' : 'Atelier (Ctrl+Shift+A)'}
        >
          <Zap className="w-4 h-4 text-purple-400" />
        </Button>
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
