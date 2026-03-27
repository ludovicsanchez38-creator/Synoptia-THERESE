/**
 * THÉRÈSE v2 - PanelContainer (US-016)
 *
 * Gère l'affichage conditionnel de tous les panneaux lazy-loaded.
 * Extrait de ChatLayout.tsx pour réduire sa complexité.
 */

import { lazy, Suspense, useCallback } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { X } from 'lucide-react';
import { usePanelStore } from '../../stores/panelStore';
import { CreateCommandForm } from '../guided/CreateCommandForm';
import { listUserCommands, createUserCommand, type UserCommand } from '../../services/api/commands';
import type { SlashCommand } from './SlashCommandsMenu';

// Lazy-loaded panels (UltraJury perf: réduire le bundle initial)
const MemoryPanel = lazy(() =>
  import('../memory/MemoryPanel').then((m) => ({ default: m.MemoryPanel }))
);
const ContactModal = lazy(() =>
  import('../memory/ContactModal').then((m) => ({ default: m.ContactModal }))
);
const ProjectModal = lazy(() =>
  import('../memory/ProjectModal').then((m) => ({ default: m.ProjectModal }))
);
const SettingsModal = lazy(() =>
  import('../settings/SettingsModal').then((m) => ({ default: m.SettingsModal }))
);
const BoardPanel = lazy(() =>
  import('../board/BoardPanel').then((m) => ({ default: m.BoardPanel }))
);
const AtelierPanel = lazy(() =>
  import('../atelier/AtelierPanel').then((m) => ({ default: m.AtelierPanel }))
);

interface PanelContainerProps {
  onUserCommandsRefresh: (commands: SlashCommand[]) => void;
}

export function PanelContainer({ onUserCommandsRefresh }: PanelContainerProps) {
  const {
    showMemoryPanel,
    showSettings,
    showContactModal,
    showProjectModal,
    showBoardPanel,
    showSaveCommand,
    editingContact,
    editingProject,
    saveCommandData,
    closeMemoryPanel,
    closeSettings,
    closeContactModal,
    closeProjectModal,
    closeBoardPanel,
    closeSaveCommand,
    openNewContact,
    openEditContact,
  } = usePanelStore();

  const handleMemorySaved = useCallback(() => {
    // Le panel se recharge au re-render
  }, []);

  const handleSaveCommandSubmit = useCallback(
    async (data: {
      name: string;
      description: string;
      category: string;
      icon: string;
      show_on_home: boolean;
      content: string;
    }) => {
      await createUserCommand(data);
      closeSaveCommand();
      // Rafraîchir les commandes slash
      const commands = await listUserCommands();
      const slashCmds: SlashCommand[] = commands.map((cmd: UserCommand) => ({
        id: `user-${cmd.name}`,
        name: cmd.name,
        description: cmd.description || cmd.name,
        icon: null,
        prefix: cmd.content,
      }));
      onUserCommandsRefresh(slashCmds);
    },
    [closeSaveCommand, onUserCommandsRefresh]
  );

  return (
    <>
      {/* Lazy-loaded panels (chargés à la demande) */}
      <Suspense
        fallback={
          <div className="flex items-center justify-center h-full">
            <div className="text-text-muted">Chargement...</div>
          </div>
        }
      >
        {/* Memory Panel (sidebar) */}
        <MemoryPanel
          isOpen={showMemoryPanel}
          onClose={closeMemoryPanel}
          onNewContact={openNewContact}
          onEditContact={openEditContact}
        />

        {/* Settings Modal */}
        <SettingsModal isOpen={showSettings} onClose={closeSettings} />

        {/* Contact Modal */}
        <ContactModal
          isOpen={showContactModal}
          onClose={closeContactModal}
          onSaved={handleMemorySaved}
          contact={editingContact}
        />

        {/* Project Modal */}
        <ProjectModal
          isOpen={showProjectModal}
          onClose={closeProjectModal}
          onSaved={handleMemorySaved}
          project={editingProject}
        />

        {/* Board de Décision */}
        <BoardPanel isOpen={showBoardPanel} onClose={closeBoardPanel} />

        {/* Atelier - Agents IA Embarqués */}
        <AtelierPanel />
      </Suspense>

      {/* Modal Sauvegarder comme raccourci */}
      <AnimatePresence>
        {showSaveCommand && saveCommandData && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
            onClick={closeSaveCommand}
          >
            <motion.div
              role="dialog"
              aria-modal="true"
              aria-label="Sauvegarder comme raccourci"
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              transition={{ duration: 0.2 }}
              className="relative bg-surface-elevated border border-border rounded-2xl p-6 shadow-2xl max-w-lg w-full mx-4 max-h-[80vh] overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Bouton fermer */}
              <button
                onClick={closeSaveCommand}
                className="absolute top-3 right-3 p-1.5 rounded-lg hover:bg-surface text-text-muted hover:text-text transition-colors"
              >
                <X className="w-4 h-4" />
              </button>

              <CreateCommandForm
                onSubmit={handleSaveCommandSubmit}
                onBack={closeSaveCommand}
                initialContent={saveCommandData.userPrompt}
                initialDescription={saveCommandData.assistantContent.slice(0, 100)}
                capturedPreview={saveCommandData.assistantContent.slice(0, 300)}
              />
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
