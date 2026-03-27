/**
 * THÉRÈSE v2 - ChatLayout (US-016 refactorisé + US-005 Dashboard)
 *
 * Composant principal du chat. Réduit de ~480 lignes à ~170 lignes.
 * - Panneaux gérés par panelStore (Zustand) - US-016
 * - Dashboard "Ma journée" au lancement - US-005
 * - Composants lazy-loaded dans PanelContainer
 */

import { useState, useCallback, useEffect, lazy, Suspense } from 'react';
import { Sparkles, WifiOff } from 'lucide-react';
import { ChatHeader } from './ChatHeader';
import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';
import { CommandPalette } from './CommandPalette';
import { ShortcutsModal } from './ShortcutsModal';
import { ConversationSidebar } from '../sidebar/ConversationSidebar';
import { DropZone } from '../files/DropZone';
import { PanelContainer } from './PanelContainer';
import { SideToggle } from '../ui/SideToggle';
import { ConnectionStatus } from '../ui/ConnectionStatus';
import { useKeyboardShortcuts, useConversationSync, useFileDrop, useOnlineStatus } from '../../hooks';
import { useChatStore } from '../../stores/chatStore';
import { useDemoStore } from '../../stores/demoStore';
import { useAtelierStore } from '../../stores/atelierStore';
import { useOpenClawStore } from '../../stores/openclawStore';
import { usePanelStore } from '../../stores/panelStore';
import { openPanelWindow } from '../../services/windowManager';
import { listUserCommands, type UserCommand } from '../../services/api/commands';
import type { SlashCommand } from './SlashCommandsMenu';

// Lazy-loaded : Dashboard "Ma journée" (US-005)
const DashboardToday = lazy(() =>
  import('../home/DashboardToday').then((m) => ({ default: m.DashboardToday }))
);

// Préférence utilisateur : skip dashboard au lancement
const PREF_SKIP_DASHBOARD = 'therese-skip-dashboard';

export function ChatLayout() {
  const [guidedPrompt, setGuidedPrompt] = useState<string | undefined>(undefined);
  const [guidedSkillId, setGuidedSkillId] = useState<string | undefined>(undefined);
  const [userSlashCommands, setUserSlashCommands] = useState<SlashCommand[]>([]);
  const [guidedPanelActive, setGuidedPanelActive] = useState(false);
  const [showDashboard, setShowDashboard] = useState(() => {
    return localStorage.getItem(PREF_SKIP_DASHBOARD) !== 'true';
  });

  const { createConversation, currentConversationId, conversations } = useChatStore();
  const toggleDemo = useDemoStore((s) => s.toggle);
  const toggleAtelier = useAtelierStore((s) => s.togglePanel);
  const openAtelierPanel = useAtelierStore((s) => s.openPanel);
  const setAtelierView = useAtelierStore((s) => s.setActiveView);
  const openNewTask = useOpenClawStore((s) => s.openNewTask);
  const ps = usePanelStore();

  useEffect(() => { setGuidedPanelActive(false); }, [currentConversationId]);

  // Si l'utilisateur a déjà des messages dans la conversation courante, pas de dashboard
  useEffect(() => {
    if (currentConversationId) {
      const conv = conversations.find((c) => c.id === currentConversationId);
      if (conv && conv.messages && conv.messages.length > 0) {
        setShowDashboard(false);
      }
    }
  }, [currentConversationId, conversations]);

  useEffect(() => {
    listUserCommands()
      .then((commands: UserCommand[]) => {
        setUserSlashCommands(commands.map((cmd) => ({
          id: `user-${cmd.name}`, name: cmd.name,
          description: cmd.description || cmd.name,
          icon: <Sparkles className="w-4 h-4" />, prefix: cmd.content,
        })));
      })
      .catch(() => {});
  }, []);

  useConversationSync();
  const isOnline = useOnlineStatus();
  const { isDragging } = useFileDrop();

  const handleNewConversation = useCallback(() => createConversation(), [createConversation]);
  const handleToggleEmail = useCallback(() => openPanelWindow('email'), []);
  const handleToggleCalendar = useCallback(() => openPanelWindow('calendar'), []);
  const handleToggleTasks = useCallback(() => openPanelWindow('tasks'), []);
  const handleToggleInvoices = useCallback(() => openPanelWindow('invoices'), []);
  const handleToggleCRM = useCallback(() => openPanelWindow('crm'), []);
  const handleDismissDashboard = useCallback(() => setShowDashboard(false), []);

  const handleOpenKatiaNewTask = useCallback(() => {
    openAtelierPanel(); setAtelierView('openclaw'); openNewTask();
  }, [openAtelierPanel, setAtelierView, openNewTask]);

  const handleGuidedPromptSelect = useCallback((prompt: string, skillId?: string) => {
    setGuidedPrompt(prompt); setGuidedSkillId(skillId);
  }, []);
  const handleGuidedPromptConsumed = useCallback(() => {
    setGuidedPrompt(undefined); setGuidedSkillId(undefined);
  }, []);

  useKeyboardShortcuts({
    onCommandPalette: ps.openCommandPalette,
    onNewConversation: handleNewConversation,
    onShowShortcuts: ps.openShortcuts,
    onEscape: ps.handleEscape,
    onToggleMemoryPanel: ps.toggleMemoryPanel,
    onNewContact: ps.openNewContact,
    onNewProject: ps.openNewProject,
    onOpenSettings: ps.openSettings,
    onToggleConversationSidebar: ps.toggleConversationSidebar,
    onToggleBoardPanel: ps.toggleBoardPanel,
    onToggleEmailPanel: handleToggleEmail,
    onToggleCalendarPanel: handleToggleCalendar,
    onToggleTasksPanel: handleToggleTasks,
    onToggleInvoicesPanel: handleToggleInvoices,
    onToggleCRMPanel: handleToggleCRM,
    onToggleAtelierPanel: toggleAtelier,
    onToggleDemoMode: toggleDemo,
    onOpenKatiaNewTask: handleOpenKatiaNewTask,
    onSearch: () => usePanelStore.getState().togglePanel('memory'),
    onOpenFile: () => console.log('Open file'),
  });

  const isMac = /Mac|iPhone|iPad/.test(navigator.platform);

  return (
    <div className="h-full flex flex-col relative">
      <DropZone isDragging={isDragging} />
      <SideToggle side="left" isOpen={ps.showConversationSidebar} onClick={ps.toggleConversationSidebar} label="Conversations" shortcut={isMac ? '⌘B' : 'Ctrl+B'} />
      <SideToggle side="right" isOpen={ps.showMemoryPanel} onClick={ps.toggleMemoryPanel} label="Mémoire" shortcut={isMac ? '⌘M' : 'Ctrl+M'} />

      <header role="banner" aria-label="Barre d'outils Therese">
        <ChatHeader onOpenSettings={ps.openSettings} onToggleEmailPanel={handleToggleEmail} onToggleCalendarPanel={handleToggleCalendar} onToggleTasksPanel={handleToggleTasks} onToggleInvoicesPanel={handleToggleInvoices} onToggleCRMPanel={handleToggleCRM} onToggleMemoryPanel={() => openPanelWindow('memory')} onToggleBoardPanel={ps.toggleBoardPanel} onToggleAtelierPanel={toggleAtelier} />
      </header>

      <main id="main-content" role="main" aria-label="Conversation" className="flex-1 overflow-hidden flex flex-col">
        {!isOnline && (
          <div className="flex items-center justify-center gap-2 px-4 py-2 bg-yellow-500/10 border-b border-yellow-500/20 text-yellow-400 text-sm" role="alert">
            <WifiOff className="w-4 h-4 flex-shrink-0" />
            <span>Mode hors ligne - tes données sont sauvegardées localement</span>
          </div>
        )}

        {/* US-005 : Dashboard "Ma journée" ou chat */}
        {showDashboard ? (
          <Suspense fallback={<div className="flex-1 flex items-center justify-center"><div className="text-text-muted text-sm">Chargement...</div></div>}>
            <DashboardToday onDismiss={handleDismissDashboard} />
          </Suspense>
        ) : (
          <>
            <div className="flex-1 overflow-hidden">
              <MessageList onPromptSelect={handleGuidedPromptSelect} onSaveAsCommand={(u, a) => ps.openSaveCommand(u, a)} onGuidedPanelChange={setGuidedPanelActive} />
            </div>
            {!guidedPanelActive && (
              <div className="border-t border-border">
                <ChatInput onOpenCommandPalette={ps.openCommandPalette} initialPrompt={guidedPrompt} initialSkillId={guidedSkillId} onInitialPromptConsumed={handleGuidedPromptConsumed} userCommands={userSlashCommands} />
              </div>
            )}
          </>
        )}
      </main>

      <CommandPalette isOpen={ps.showCommandPalette} onClose={ps.closeCommandPalette} onShowShortcuts={ps.openShortcuts} onNewContact={ps.openNewContact} onNewProject={ps.openNewProject} onOpenSettings={ps.openSettings} onToggleConversations={ps.toggleConversationSidebar} onToggleMemory={ps.toggleMemoryPanel} onToggleBoard={ps.toggleBoardPanel} onToggleEmail={handleToggleEmail} onToggleCalendar={handleToggleCalendar} onToggleTasks={handleToggleTasks} onToggleInvoices={handleToggleInvoices} onToggleCRM={handleToggleCRM} onSearch={() => usePanelStore.getState().togglePanel('memory')} onOpenFile={() => console.log('Open file')} onOpenGuided={() => setGuidedPanelActive(false)} />
      <ShortcutsModal isOpen={ps.showShortcuts} onClose={ps.closeShortcuts} />
      <aside role="complementary" aria-label="Conversations">
        <ConversationSidebar isOpen={ps.showConversationSidebar} onClose={ps.closeConversationSidebar} />
      </aside>
      <PanelContainer onUserCommandsRefresh={setUserSlashCommands} />
      <div className="fixed bottom-1 right-4 z-10"><ConnectionStatus /></div>
    </div>
  );
}
