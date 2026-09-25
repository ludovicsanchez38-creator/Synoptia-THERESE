import { motion, AnimatePresence } from 'framer-motion';
import { X, Keyboard } from 'lucide-react';
import { cn } from '../../lib/utils';
import { DialogShell } from '../ui/DialogShell';
import { Button, Carte } from '../ui';
import { RACCOURCIS_PENDANT_LA_SAISIE, SHORTCUT_GROUPS } from '../../lib/raccourcisAnnonces';

interface ShortcutsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function ShortcutsModal({ isOpen, onClose }: ShortcutsModalProps) {
  // Adapter ⌘ → Ctrl sur Windows/Linux (BUG-042 icône Apple sur Windows)
  const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
  const adaptKey = (keys: string) => isMac ? keys : keys.replace(/⌘/g, 'Ctrl');

  return (
    <DialogShell open={isOpen} onClose={onClose} ariaLabel="Raccourcis clavier">
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.2, ease: [0.23, 1, 0.32, 1] }}
            className={cn(
              'w-full max-w-2xl mx-4',
              'bg-surface border border-border rounded-md shadow-lg',
              'overflow-hidden'
            )}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-border/50">
              <div className="flex items-center gap-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-accent-tint">
                  <Keyboard className="h-4 w-4 text-accent" />
                </div>
                <h2 className="text-lg font-semibold text-text">Raccourcis clavier</h2>
              </div>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                onClick={onClose}
                aria-label="Fermer les raccourcis clavier"
              >
                <X className="w-5 h-5 text-text-muted" />
              </Button>
            </div>

            {/* Content */}
            <div className="p-6 max-h-[70vh] overflow-y-auto">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {SHORTCUT_GROUPS.map((group, groupIndex) => (
                  <Carte
                    as="section"
                    key={group.title}
                    className="p-4"
                  >
                    <h3 className="mb-3 flex items-center gap-2 text-sm font-semibold text-accent">
                      <span className="h-1.5 w-1.5 rounded-full bg-accent" />
                      {group.title}
                    </h3>
                    <div className="space-y-2">
                      {group.shortcuts.map((shortcut, shortcutIndex) => (
                        <motion.div
                          key={shortcut.description}
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: groupIndex * 0.05 + shortcutIndex * 0.02 }}
                          className="flex items-center justify-between py-1.5 hover:bg-surface-elevated/30 px-2 -mx-2 rounded-md transition-colors"
                        >
                          <span className="text-sm text-text-muted">
                            {shortcut.description}
                          </span>
                          <div className="flex items-center gap-1">
                            {adaptKey(shortcut.keys).split(' + ').map((key, i) => (
                              <span key={i} className="flex items-center gap-1">
                                {i > 0 && (
                                  <span className="text-text-muted text-xs">+</span>
                                )}
                                <kbd
                                  className={cn(
                                    'min-w-[24px] h-6 px-1.5 inline-flex items-center justify-center',
                                    'rounded-sm bg-bg border border-border/50',
                                    'text-xs font-mono text-text',
                                    'shadow-sm'
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
                  </Carte>
                ))}
              </div>
              {/* B-1376 : la plupart des raccourcis sont ignorés dans un champ. */}
              <p className="mt-6 text-sm text-text-muted">
                En écrivant dans un champ, seuls ces raccourcis restent actifs :{' '}
                {RACCOURCIS_PENDANT_LA_SAISIE.map(adaptKey).join(' · ')}.
              </p>
            </div>

            {/* Footer */}
            <div className="px-6 py-3 border-t border-border/50 bg-bg/30">
              <p className="text-xs text-text-muted text-center">
                Appuie sur <kbd className="px-1.5 py-0.5 rounded-sm bg-surface-elevated border border-border/50">Échap</kbd> pour fermer
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </DialogShell>
  );
}
