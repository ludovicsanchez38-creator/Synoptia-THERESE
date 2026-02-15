import { useState, useCallback, useEffect } from 'react';
import { Sparkles } from 'lucide-react';
import { ChatHeader } from './ChatHeader';
import { MessageList } from './MessageList';
import { ChatInput } from './ChatInput';
import { CommandPalette } from './CommandPalette';
import { ShortcutsModal } from './ShortcutsModal';
import { MemoryPanel } from '../memory/MemoryPanel';
import { ContactModal } from '../memory/ContactModal';
import { ProjectModal } from '../memory/ProjectModal';
import { SettingsModal } from '../settings/SettingsModal';
import { ConversationSidebar } from '../sidebar/ConversationSidebar';
import { BoardPanel } from '../board';
import { DropZone } from '../files/DropZone';
import { SideToggle } from '../ui/SideToggle';
import { ConnectionStatus } from '../ui/ConnectionStatus';
import { useKeyboardShortcuts, useConversationSync, useFileDrop } from '../../hooks';
import { useChatStore } from '../../stores/chatStore';
import { useDemoStore } from '../../stores/demoStore';
import { openPanelWindow } from '../../services/windowManager';
import * as api from '../../services/api';
import { listUserCommands, type UserCommand } from '../../services/api/commands';
import type { SlashCommand } from './SlashCommandsMenu';

export function ChatLayout() {
  const [showCommandPalette, setShowCommandPalette] = useState(false);
  const [showShortcuts, setShowShortcuts] = useState(false);
  const [showMemoryPanel, setShowMemoryPanel] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [showConversationSidebar, setShowConversationSidebar] = useState(true);
  const [showContactModal, setShowContactModal] = useState(false);
  const [showProjectModal, setShowProjectModal] = useState(false);
  const [showBoardPanel, setShowBoardPanel] = useState(false);
  const [editingContact, setEditingContact] = useState<api.Contact | null>(null);
  const [editingProject, setEditingProject] = useState<api.Project | null>(null);
  const [guidedPrompt, setGuidedPrompt] = useState<string | undefined>(undefined);
  const [userSlashCommands, setUserSlashCommands] = useState<SlashCommand[]>([]);

  const { createConversation } = useChatStore();
  const toggleDemo = useDemoStore((s) => s.toggle);

  // Fetch user commands for slash menu integration
  useEffect(() => {
    listUserCommands()
      .then((commands: UserCommand[]) => {
        const slashCmds: SlashCommand[] = commands.map((cmd) => ({
          id: `user-${cmd.name}`,
          name: cmd.name,
          description: cmd.description || cmd.name,
          icon: <Sparkles className="w-4 h-4" />,
          prefix: cmd.content,
        }));
        setUserSlashCommands(slashCmds);
      })
      .catch(() => {
        // Silently ignore - user commands are optional
      });
  }, []);

  // Sync conversations with backend on mount
  useConversationSync();

  // Global file drop handling for full-screen overlay
  const { isDragging } = useFileDrop();

  // Memoize handlers to avoid unnecessary re-renders
  const handleOpenCommandPalette = useCallback(() => {
    setShowCommandPalette(true);
  }, []);

  const handleCloseCommandPalette = useCallback(() => {
    setShowCommandPalette(false);
  }, []);

  const handleShowShortcuts = useCallback(() => {
    setShowShortcuts(true);
  }, []);

  const handleCloseShortcuts = useCallback(() => {
    setShowShortcuts(false);
  }, []);

  const handleNewConversation = useCallback(() => {
    createConversation();
  }, [createConversation]);

  const handleEscape = useCallback(() => {
    // Close any open modal (in order of z-index)
    if (showBoardPanel) {
      setShowBoardPanel(false);
    } else if (showContactModal) {
      setShowContactModal(false);
      setEditingContact(null);
    } else if (showProjectModal) {
      setShowProjectModal(false);
      setEditingProject(null);
    } else if (showCommandPalette) {
      setShowCommandPalette(false);
    } else if (showShortcuts) {
      setShowShortcuts(false);
    } else if (showSettings) {
      setShowSettings(false);
    } else if (showMemoryPanel) {
      setShowMemoryPanel(false);
    } else if (showConversationSidebar) {
      setShowConversationSidebar(false);
    }
  }, [showBoardPanel, showCommandPalette, showShortcuts, showMemoryPanel, showSettings, showConversationSidebar, showContactModal, showProjectModal]);

  const handleOpenSettings = useCallback(() => {
    setShowSettings(true);
  }, []);

  const handleCloseSettings = useCallback(() => {
    setShowSettings(false);
  }, []);

  const handleToggleMemoryPanel = useCallback(() => {
    setShowMemoryPanel((prev) => !prev);
  }, []);

  const handleCloseMemoryPanel = useCallback(() => {
    setShowMemoryPanel(false);
  }, []);

  const handleNewContact = useCallback(() => {
    setEditingContact(null);
    setShowContactModal(true);
  }, []);

  const handleEditContact = useCallback((contact: api.Contact) => {
    setEditingContact(contact);
    setShowContactModal(true);
  }, []);

  const handleNewProject = useCallback(() => {
    setEditingProject(null);
    setShowProjectModal(true);
  }, []);


  const handleToggleConversationSidebar = useCallback(() => {
    setShowConversationSidebar((prev) => !prev);
  }, []);

  const handleCloseConversationSidebar = useCallback(() => {
    setShowConversationSidebar(false);
  }, []);

  const handleCloseContactModal = useCallback(() => {
    setShowContactModal(false);
    setEditingContact(null);
  }, []);

  const handleCloseProjectModal = useCallback(() => {
    setShowProjectModal(false);
    setEditingProject(null);
  }, []);

  const handleMemorySaved = useCallback(() => {
    // Refresh memory panel data if open
    // The panel will reload when it re-renders
  }, []);

  const handleGuidedPromptSelect = useCallback((prompt: string) => {
    setGuidedPrompt(prompt);
  }, []);

  const handleGuidedPromptConsumed = useCallback(() => {
    setGuidedPrompt(undefined);
  }, []);

  const handleToggleBoardPanel = useCallback(() => {
    setShowBoardPanel((prev) => !prev);
  }, []);

  const handleCloseBoardPanel = useCallback(() => {
    setShowBoardPanel(false);
  }, []);

  const handleToggleDemoMode = useCallback(() => {
    toggleDemo();
  }, [toggleDemo]);

  // Panels ouverts dans des fenetres separees
  const handleToggleEmailPanel = useCallback(() => {
    openPanelWindow('email');
  }, []);

  const handleToggleCalendarPanel = useCallback(() => {
    openPanelWindow('calendar');
  }, []);

  const handleToggleTasksPanel = useCallback(() => {
    openPanelWindow('tasks');
  }, []);

  const handleToggleInvoicesPanel = useCallback(() => {
    openPanelWindow('invoices');
  }, []);

  const handleToggleCRMPanel = useCallback(() => {
    openPanelWindow('crm');
  }, []);

  // Global keyboard shortcuts
  useKeyboardShortcuts({
    onCommandPalette: handleOpenCommandPalette,
    onNewConversation: handleNewConversation,
    onShowShortcuts: handleShowShortcuts,
    onEscape: handleEscape,
    onToggleMemoryPanel: handleToggleMemoryPanel,
    onNewContact: handleNewContact,
    onNewProject: handleNewProject,
    onOpenSettings: handleOpenSettings,
    onToggleConversationSidebar: handleToggleConversationSidebar,
    onToggleBoardPanel: handleToggleBoardPanel,
    onToggleEmailPanel: handleToggleEmailPanel,
    onToggleCalendarPanel: handleToggleCalendarPanel,
    onToggleTasksPanel: handleToggleTasksPanel,
    onToggleInvoicesPanel: handleToggleInvoicesPanel,
    onToggleCRMPanel: handleToggleCRMPanel,
    onToggleDemoMode: handleToggleDemoMode,
    onSearch: () => {
      setShowMemoryPanel(true);
    },
    onOpenFile: () => {
      console.log('Open file');
    },
  });

  return (
    <div className="h-full flex flex-col relative">
      {/* Full-screen drop zone overlay */}
      <DropZone isDragging={isDragging} />

      {/* Side Toggles - Rails latéraux */}
      <SideToggle
        side="left"
        isOpen={showConversationSidebar}
        onClick={handleToggleConversationSidebar}
        label="Conversations"
        shortcut="⌘B"
      />
      <SideToggle
        side="right"
        isOpen={showMemoryPanel}
        onClick={handleToggleMemoryPanel}
        label="Mémoire"
        shortcut="⌘M"
      />

      {/* Header with drag region for Tauri */}
      <ChatHeader
        onOpenSettings={handleOpenSettings}
        onToggleEmailPanel={handleToggleEmailPanel}
        onToggleCalendarPanel={handleToggleCalendarPanel}
        onToggleTasksPanel={handleToggleTasksPanel}
        onToggleInvoicesPanel={handleToggleInvoicesPanel}
        onToggleCRMPanel={handleToggleCRMPanel}
        onToggleMemoryPanel={() => openPanelWindow('memory')}
      />

      {/* Messages area */}
      <div className="flex-1 overflow-hidden">
        <MessageList onPromptSelect={handleGuidedPromptSelect} />
      </div>

      {/* Input area */}
      <div className="border-t border-border">
        <ChatInput
          onOpenCommandPalette={handleOpenCommandPalette}
          initialPrompt={guidedPrompt}
          onInitialPromptConsumed={handleGuidedPromptConsumed}
          userCommands={userSlashCommands}
        />
      </div>

      {/* Command Palette (modal) */}
      <CommandPalette
        isOpen={showCommandPalette}
        onClose={handleCloseCommandPalette}
        onShowShortcuts={handleShowShortcuts}
        onNewContact={handleNewContact}
        onNewProject={handleNewProject}
        onOpenSettings={handleOpenSettings}
        onToggleConversations={handleToggleConversationSidebar}
        onToggleMemory={handleToggleMemoryPanel}
        onToggleBoard={handleToggleBoardPanel}
        onToggleEmail={handleToggleEmailPanel}
        onToggleCalendar={handleToggleCalendarPanel}
        onToggleTasks={handleToggleTasksPanel}
        onToggleInvoices={handleToggleInvoicesPanel}
        onToggleCRM={handleToggleCRMPanel}
        onSearch={() => setShowMemoryPanel(true)}
        onOpenFile={() => console.log('Open file')}
      />

      {/* Shortcuts Modal */}
      <ShortcutsModal
        isOpen={showShortcuts}
        onClose={handleCloseShortcuts}
      />

      {/* Memory Panel (sidebar) */}
      <MemoryPanel
        isOpen={showMemoryPanel}
        onClose={handleCloseMemoryPanel}
        onNewContact={handleNewContact}
        onEditContact={handleEditContact}
      />

      {/* Settings Modal */}
      <SettingsModal
        isOpen={showSettings}
        onClose={handleCloseSettings}
      />

      {/* Conversation Sidebar */}
      <ConversationSidebar
        isOpen={showConversationSidebar}
        onClose={handleCloseConversationSidebar}
      />

      {/* Contact Modal */}
      <ContactModal
        isOpen={showContactModal}
        onClose={handleCloseContactModal}
        onSaved={handleMemorySaved}
        contact={editingContact}
      />

      {/* Project Modal */}
      <ProjectModal
        isOpen={showProjectModal}
        onClose={handleCloseProjectModal}
        onSaved={handleMemorySaved}
        project={editingProject}
      />

      {/* Board de Decision */}
      <BoardPanel
        isOpen={showBoardPanel}
        onClose={handleCloseBoardPanel}
      />

      {/* Status connexion - coin bas droite */}
      <div className="fixed bottom-1 right-4 z-10">
        <ConnectionStatus />
      </div>
    </div>
  );
}
