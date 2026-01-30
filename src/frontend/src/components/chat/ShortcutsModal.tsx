import { motion, AnimatePresence } from 'framer-motion';
import { X, Keyboard } from 'lucide-react';
import { cn } from '../../lib/utils';

interface ShortcutsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

interface ShortcutGroup {
  title: string;
  shortcuts: { keys: string; description: string }[];
}

const SHORTCUT_GROUPS: ShortcutGroup[] = [
  {
    title: 'Chat',
    shortcuts: [
      { keys: '↵', description: 'Envoyer le message' },
      { keys: '⇧ + ↵', description: 'Nouvelle ligne' },
      { keys: '⌘ + N', description: 'Nouvelle conversation' },
      { keys: '⌘ + ⌫', description: 'Effacer la conversation' },
    ],
  },
  {
    title: 'Navigation',
    shortcuts: [
      { keys: '⌘ + K', description: 'Palette de commandes' },
      { keys: '⌘ + /', description: 'Raccourcis clavier' },
      { keys: '⌘ + B', description: 'Sidebar conversations' },
      { keys: '⌘ + M', description: 'Panneau mémoire' },
      { keys: 'Échap', description: 'Fermer le panneau actif' },
    ],
  },
  {
    title: 'Core Features',
    shortcuts: [
      { keys: '⌘ + D', description: 'Board de décision' },
      { keys: '⌘ + E', description: 'Email (Gmail)' },
      { keys: '⌘ + T', description: 'Tâches (Kanban)' },
      { keys: '⌘ + I', description: 'Factures' },
      { keys: '⌘ + P', description: 'CRM Pipeline' },
    ],
  },
  {
    title: 'Outils',
    shortcuts: [
      { keys: '⌘ + ⇧ + C', description: 'Calendrier (Google Calendar)' },
      { keys: '⌘ + ⇧ + P', description: 'Nouveau projet' },
      { keys: '⌘ + ⇧ + F', description: 'Rechercher en mémoire' },
    ],
  },
  {
    title: 'Fichiers',
    shortcuts: [
      { keys: '⌘ + O', description: 'Ouvrir un fichier' },
      { keys: '⌘ + ⇧ + O', description: 'Ouvrir un dossier' },
      { keys: '⌘ + S', description: 'Sauvegarder' },
    ],
  },
];

export function ShortcutsModal({ isOpen, onClose }: ShortcutsModalProps) {
  return (
    <AnimatePresence>
      {isOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center"
          onClick={onClose}
        >
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="absolute inset-0 bg-black/60 backdrop-blur-md"
          />

          {/* Modal */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.2, ease: [0.23, 1, 0.32, 1] }}
            className={cn(
              'relative w-full max-w-2xl mx-4',
              'bg-surface/95 backdrop-blur-xl border border-border/50 rounded-xl',
              'shadow-[0_25px_50px_-12px_rgba(0,0,0,0.5)]',
              'overflow-hidden'
            )}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-border/50">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-accent-cyan/20 flex items-center justify-center">
                  <Keyboard className="w-4 h-4 text-accent-cyan" />
                </div>
                <h2 className="text-lg font-semibold text-text">Raccourcis clavier</h2>
              </div>
              <button
                onClick={onClose}
                className="p-1.5 rounded-lg hover:bg-surface-elevated transition-colors"
              >
                <X className="w-5 h-5 text-text-muted" />
              </button>
            </div>

            {/* Content */}
            <div className="p-6 max-h-[70vh] overflow-y-auto">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {SHORTCUT_GROUPS.map((group, groupIndex) => (
                  <motion.div
                    key={group.title}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: groupIndex * 0.05 }}
                  >
                    <h3 className="text-sm font-medium text-accent-cyan mb-3 flex items-center gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-accent-cyan shadow-[0_0_6px_rgba(34,211,238,0.5)]" />
                      {group.title}
                    </h3>
                    <div className="space-y-2">
                      {group.shortcuts.map((shortcut, shortcutIndex) => (
                        <motion.div
                          key={shortcut.description}
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: groupIndex * 0.05 + shortcutIndex * 0.02 }}
                          className="flex items-center justify-between py-1.5 hover:bg-surface-elevated/30 px-2 -mx-2 rounded-lg transition-colors"
                        >
                          <span className="text-sm text-text-muted">
                            {shortcut.description}
                          </span>
                          <div className="flex items-center gap-1">
                            {shortcut.keys.split(' + ').map((key, i) => (
                              <span key={i} className="flex items-center gap-1">
                                {i > 0 && (
                                  <span className="text-text-muted text-xs">+</span>
                                )}
                                <kbd
                                  className={cn(
                                    'min-w-[24px] h-6 px-1.5 inline-flex items-center justify-center',
                                    'rounded bg-bg border border-border/50',
                                    'text-xs font-mono text-text',
                                    'shadow-[0_1px_2px_rgba(0,0,0,0.2)]'
                                  )}
                                >
                                  {key}
                                </kbd>
                              </span>
                            ))}
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>

            {/* Footer */}
            <div className="px-6 py-3 border-t border-border/50 bg-bg/30">
              <p className="text-xs text-text-muted text-center">
                Appuie sur <kbd className="px-1.5 py-0.5 rounded bg-surface-elevated border border-border/50">Échap</kbd> pour fermer
              </p>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
