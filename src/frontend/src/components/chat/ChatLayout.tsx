/**
 * THÉRÈSE v2 - ChatLayout (US-016 refactorisé + US-005 Dashboard)
 *
 * Composant principal du chat. Réduit de ~480 lignes à ~170 lignes.
 * - Panneaux gérés par panelStore (Zustand) - US-016
 * - Dashboard "Ma journée" au lancement - US-005
 * - Composants lazy-loaded dans PanelContainer
 */

import { useState, useCallback, useEffect, lazy, Suspense } from 'react';
import { Sparkles, WifiOff, ArrowLeft } from 'lucide-react';
import { ChatHeader } from './ChatHeader';
import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';
import { CommandPalette } from './CommandPalette';
import { ConversationMemoryChip } from './ConversationMemoryChip';
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
// OpenClaw store : conservé mais plus utilisé dans ChatLayout
import { usePanelStore } from '../../stores/panelStore';
import { useNavigationStore } from '../../stores/navigationStore';
import { useActionsStore } from '../../stores/actionsStore';
import { useContactsStore } from '../../stores/contactsStore';
import { resolveEscape } from '../../lib/resolveEscape';
import { runAction, getActions } from '../../lib/actionRegistry';
import { listUserCommands, type UserCommand } from '../../services/api/commands';
import type { SlashCommand } from './SlashCommandsMenu';

// Lazy-loaded : vue Accueil
const HomeView = lazy(() =>
  import('../home/HomeView').then((m) => ({ default: m.HomeView }))
);

// Phase 1 (content-swap) : vues rendues dans la zone principale au lieu de fenêtres.
const CRMPanel = lazy(() =>
  import('../crm').then((m) => ({ default: m.CRMPanel }))
);
const EmailPanel = lazy(() =>
  import('../email').then((m) => ({ default: m.EmailPanel }))
);
const CalendarPanel = lazy(() =>
  import('../calendar').then((m) => ({ default: m.CalendarPanel }))
);
const TasksPanel = lazy(() =>
  import('../tasks').then((m) => ({ default: m.TasksPanel }))
);
const InvoicesPanel = lazy(() =>
  import('../invoices').then((m) => ({ default: m.InvoicesPanel }))
);
// L6 : la Mémoire devient une vue de la zone principale (plus un tiroir overlay).
const MemoryPanel = lazy(() =>
  import('../memory/MemoryPanel').then((m) => ({ default: m.MemoryPanel }))
);
// Arbitrage A/B : l'indexation de fichiers sort de la Mémoire en vue dédiée.
const FileBrowser = lazy(() =>
  import('../files/FileBrowser').then((m) => ({ default: m.FileBrowser }))
);
// BUG-104 : vue Projets dédiée (la refonte 0.20 avait fait perdre cette surface).
const ProjectsPanel = lazy(() =>
  import('../memory/ProjectsPanel').then((m) => ({ default: m.ProjectsPanel }))
);

export function ChatLayout() {
  const [guidedPrompt, setGuidedPrompt] = useState<string | undefined>(undefined);
  const [guidedSkillId, setGuidedSkillId] = useState<string | undefined>(undefined);
  const [userSlashCommands, setUserSlashCommands] = useState<SlashCommand[]>([]);
  const [guidedPanelActive, setGuidedPanelActive] = useState(false);

  const { createConversation, currentConversationId } = useChatStore();
  const toggleDemo = useDemoStore((s) => s.toggle);
  const toggleAtelier = useAtelierStore((s) => s.togglePanel);
  const openAtelierPanel = useAtelierStore((s) => s.openPanel);
  const ps = usePanelStore();
  const activeView = useNavigationStore((s) => s.activeView);
  const goBack = useNavigationStore((s) => s.goBack);

  useEffect(() => { setGuidedPanelActive(false); }, [currentConversationId]);

  // Insertion d'un prompt dans le chat depuis ailleurs (⌘K « Produire un document »,
  // bibliothèque de prompts) — correctif KO Syn 2.1/2.2 : ramène au chat et pré-remplit.
  // Expose aussi runAction pour l'appel bas niveau (debug / test / pont Thérèse, Dr_logic).
  useEffect(() => {
    const onInsertPrompt = (e: Event) => {
      const text = (e as CustomEvent<string>).detail;
      if (typeof text !== 'string') return;
      useNavigationStore.getState().setView('chat');
      setGuidedSkillId(undefined);
      setGuidedPrompt(text);
      setGuidedPanelActive(false);
    };
    window.addEventListener('therese:insert-prompt', onInsertPrompt as EventListener);
    (window as unknown as { __therese?: unknown }).__therese = {
      runAction,
      getActions,
      // Inspection bas niveau (debug / test / pont Thérèse) : lecture d'état des stores.
      stores: {
        navigation: useNavigationStore,
        panel: usePanelStore,
        actions: useActionsStore,
        atelier: useAtelierStore,
        chat: useChatStore,
        contacts: useContactsStore,
      },
    };
    return () => window.removeEventListener('therese:insert-prompt', onInsertPrompt as EventListener);
  }, []);

  // Au lancement : atterrir sur l'Accueil (sauf préférence contraire).
  useEffect(() => {
    if (localStorage.getItem('therese-skip-dashboard') !== 'true') {
      useNavigationStore.getState().setView('home');
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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
  // Phase 1 : Email/Agenda/Tâches/Factures/CRM deviennent des VUES de la zone principale.
  const handleToggleEmail = useCallback(() => useNavigationStore.getState().setView('email'), []);
  const handleToggleCalendar = useCallback(() => useNavigationStore.getState().setView('calendar'), []);
  const handleToggleTasks = useCallback(() => useNavigationStore.getState().setView('tasks'), []);
  const handleToggleInvoices = useCallback(() => useNavigationStore.getState().setView('invoices'), []);
  const handleToggleCRM = useCallback(() => useNavigationStore.getState().setView('crm'), []);
  // BUG-104 : le bouton « Projet » du header ouvre la vue Projets (et non la Mémoire).
  const handleToggleProjects = useCallback(() => useNavigationStore.getState().setView('projects'), []);
  // L6 : la Mémoire est une vue. ⌘M garde une sémantique « toggle » :
  // déjà sur la vue Mémoire -> retour, sinon -> bascule vers la vue Mémoire.
  const handleToggleMemory = useCallback(() => {
    const nav = useNavigationStore.getState();
    if (nav.activeView === 'memory') nav.goBack();
    else nav.setView('memory');
  }, []);
  // Cmd+Shift+K : ouvrir l'Atelier en mode chat local
  const handleOpenAtelierChat = useCallback(() => {
    openAtelierPanel();
  }, [openAtelierPanel]);

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
    onEscape: resolveEscape,
    onToggleMemoryPanel: handleToggleMemory,
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
    onOpenKatiaNewTask: handleOpenAtelierChat,
    // L6 : ⌘K « Rechercher » bascule vers la vue Mémoire (fini le faux ami
    // qui ouvrait le tiroir). La vraie recherche globale relève de L8 (⌘K).
    onSearch: handleToggleMemory,
    onOpenFile: () => console.log('Open file'),
  });

  const isMac = /Mac|iPhone|iPad/.test(navigator.platform);

  return (
    <div className="h-full flex flex-col relative">
      <DropZone isDragging={isDragging} />
      <SideToggle side="left" isOpen={ps.showConversationSidebar} onClick={ps.toggleConversationSidebar} label="Conversations" shortcut={isMac ? '⌘B' : 'Ctrl+B'} />
      <SideToggle side="right" isOpen={activeView === 'memory'} onClick={handleToggleMemory} label="Mémoire" shortcut={isMac ? '⌘M' : 'Ctrl+M'} />

      <header role="banner" aria-label="Barre d'outils Therese">
        <ChatHeader onOpenSettings={ps.openSettings} onToggleEmailPanel={handleToggleEmail} onToggleCalendarPanel={handleToggleCalendar} onToggleTasksPanel={handleToggleTasks} onToggleInvoicesPanel={handleToggleInvoices} onToggleCRMPanel={handleToggleCRM} onToggleProjectsPanel={handleToggleProjects} onToggleBoardPanel={ps.toggleBoardPanel} onToggleAtelierPanel={toggleAtelier} onHome={() => useNavigationStore.getState().setView('home')} />
      </header>

      <main id="main-content" role="main" aria-label="Conversation" className="flex-1 overflow-hidden flex flex-col">
        {!isOnline && (
          <div className="flex items-center justify-center gap-2 px-4 py-2 bg-yellow-500/10 border-b border-yellow-500/20 text-yellow-400 text-sm" role="alert">
            <WifiOff className="w-4 h-4 flex-shrink-0" />
            <span>Mode hors ligne - tes données sont sauvegardées localement</span>
          </div>
        )}

        {/* Phase 1 (content-swap) : routeur de vues dans la zone principale */}
        {activeView === 'home' ? (
          <Suspense fallback={<div className="flex-1 flex items-center justify-center"><div className="text-text-muted text-sm">Chargement...</div></div>}>
            <HomeView />
          </Suspense>
        ) : activeView !== 'chat' ? (
          <div className="flex-1 overflow-hidden flex flex-col">
            <div className="flex items-center px-4 py-2 border-b border-border/50">
              <button
                onClick={goBack}
                className="flex items-center gap-1.5 text-sm text-text-muted hover:text-text transition-colors"
                aria-label="Retour au chat"
              >
                <ArrowLeft className="w-4 h-4" /> Chat
              </button>
            </div>
            <Suspense fallback={<div className="flex-1 flex items-center justify-center"><div className="text-text-muted text-sm">Chargement...</div></div>}>
              {activeView === 'crm' && <CRMPanel standalone />}
              {activeView === 'email' && <EmailPanel standalone />}
              {activeView === 'calendar' && <CalendarPanel standalone />}
              {activeView === 'tasks' && <TasksPanel standalone />}
              {activeView === 'invoices' && <InvoicesPanel standalone />}
              {activeView === 'memory' && (
                <MemoryPanel standalone onNewContact={ps.openNewContact} onEditContact={ps.openEditContact} />
              )}
              {activeView === 'files' && (
                <div className="flex-1 overflow-auto p-4">
                  <FileBrowser />
                </div>
              )}
              {activeView === 'projects' && <ProjectsPanel />}
            </Suspense>
          </div>
        ) : (
          <>
            <div className="flex-1 overflow-hidden">
              <MessageList onPromptSelect={handleGuidedPromptSelect} onSaveAsCommand={(u, a) => ps.openSaveCommand(u, a)} onGuidedPanelChange={setGuidedPanelActive} />
            </div>
            {!guidedPanelActive && (
              <>
                {/* L6 : pastille de glance « N contacts liés à cette conversation » */}
                <ConversationMemoryChip />
                <div className="border-t border-border">
                  <ChatInput onOpenCommandPalette={ps.openCommandPalette} initialPrompt={guidedPrompt} initialSkillId={guidedSkillId} onInitialPromptConsumed={handleGuidedPromptConsumed} userCommands={userSlashCommands} />
                </div>
              </>
            )}
          </>
        )}
      </main>

      <CommandPalette isOpen={ps.showCommandPalette} onClose={ps.closeCommandPalette} />
      <ShortcutsModal isOpen={ps.showShortcuts} onClose={ps.closeShortcuts} />
      <aside role="complementary" aria-label="Conversations">
        <ConversationSidebar isOpen={ps.showConversationSidebar} onClose={ps.closeConversationSidebar} />
      </aside>
      <PanelContainer onUserCommandsRefresh={setUserSlashCommands} />
      <div className="fixed bottom-1 right-4 z-10"><ConnectionStatus /></div>
    </div>
  );
}
