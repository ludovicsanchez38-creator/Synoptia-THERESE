/**
 * THÉRÈSE v2 - Email Panel
 *
 * Main email panel component (modal/sidebar).
 * Phase 1 Frontend - Email
 */

import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Mail,
  X,
  Inbox,
  Send,
  Archive,
  Trash2,
  Star,
  RefreshCw,
  Plus,
  Settings,
  Loader2,
} from 'lucide-react';
import { useEmailStore } from '../../stores/emailStore';
import { Button } from '../ui/Button';
import { EmailList } from './EmailList';
import { EmailDetail } from './EmailDetail';
import { EmailCompose } from './EmailCompose';
import { EmailSetupWizard } from './wizard';
import * as api from '../../services/api';

interface EmailPanelProps {
  standalone?: boolean;
}

export function EmailPanel({ standalone = false }: EmailPanelProps) {
  const {
    isEmailPanelOpen,
    toggleEmailPanel,
    accounts,
    currentAccountId,
    setAccounts,
    setCurrentAccount,
    isComposing,
    setIsComposing,
    currentMessageId,
    labels,
    setLabels,
    currentLabelId,
    setCurrentLabel,
  } = useEmailStore();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [syncing, setSyncing] = useState(false);

  // Load accounts on mount (standalone ou modal)
  useEffect(() => {
    if (standalone || isEmailPanelOpen) {
      loadAccounts();
    }
  }, [standalone, isEmailPanelOpen]);

  async function loadAccounts() {
    setLoading(true);
    setError(null);

    // Tenter de rafraichir les comptes depuis l'API
    try {
      const status = await api.getEmailAuthStatus();
      setAccounts(status.accounts);
      if (status.accounts.length > 0 && !currentAccountId) {
        setCurrentAccount(status.accounts[0].id);
        await loadLabels(status.accounts[0].id);
      } else if (currentAccountId) {
        await loadLabels(currentAccountId);
      }
    } catch (err) {
      console.error('Failed to load accounts from API:', err);

      // Fallback : utiliser les comptes deja dans le store (cache localStorage)
      if (accounts.length > 0 && currentAccountId) {
        console.log('Using cached accounts, loading labels...');
        try {
          await loadLabels(currentAccountId);
        } catch {
          // Labels aussi en cache via le store persist
          console.warn('Failed to load labels, using cached data');
        }
      } else {
        setError('Impossible de charger les comptes email');
      }
    } finally {
      setLoading(false);
    }
  }

  async function loadLabels(accountId: string) {
    try {
      const labelsData = await api.listEmailLabels(accountId);
      setLabels(labelsData);
    } catch (err) {
      console.error('Failed to load labels:', err);
    }
  }

  async function handleSync() {
    if (!currentAccountId) return;
    setSyncing(true);
    try {
      // Reload messages (will be handled by EmailList)
      await loadLabels(currentAccountId);
    } catch (err) {
      console.error('Failed to sync:', err);
      setError('Échec de la synchronisation');
    } finally {
      setSyncing(false);
    }
  }

  function handleCompose() {
    setIsComposing(true);
  }

  // En mode standalone, le panel est toujours visible
  if (!standalone && !isEmailPanelOpen) return null;

  const currentAccount = accounts.find((a) => a.id === currentAccountId);
  const isConnected = accounts.length > 0;

  // System labels
  const systemLabels = [
    { id: 'INBOX', name: 'Boite de réception', icon: Inbox },
    { id: 'SENT', name: 'Envoyés', icon: Send },
    { id: 'STARRED', name: 'Suivis', icon: Star },
    { id: 'TRASH', name: 'Corbeille', icon: Trash2 },
  ];

  // Mode standalone : pleine page sans modal
  if (standalone) {
    return (
      <div className="h-full flex flex-col bg-bg">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border/30">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-accent-cyan/20 to-accent-magenta/20 flex items-center justify-center">
              <Mail className="w-5 h-5 text-accent-cyan" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-text">Email</h2>
              {currentAccount && (
                <p className="text-xs text-text-muted">{currentAccount.email}</p>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2">
            {isConnected && (
              <>
                <Button variant="ghost" size="sm" onClick={handleCompose}>
                  <Plus className="w-4 h-4 mr-2" />
                  Nouveau
                </Button>
                <Button variant="ghost" size="sm" onClick={handleSync} disabled={syncing}>
                  <RefreshCw className={`w-4 h-4 ${syncing ? 'animate-spin' : ''}`} />
                </Button>
              </>
            )}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 flex overflow-hidden">
          {loading ? (
            <div className="flex-1 flex items-center justify-center">
              <Loader2 className="w-8 h-8 animate-spin text-accent-cyan" />
            </div>
          ) : error ? (
            <div className="flex-1 flex flex-col items-center justify-center gap-3">
              <p className="text-red-400">{error}</p>
              <Button variant="ghost" size="sm" onClick={loadAccounts}>
                Réessayer
              </Button>
            </div>
          ) : !isConnected ? (
            <div className="flex-1">
              <EmailSetupWizard onComplete={loadAccounts} onCancel={() => {}} />
            </div>
          ) : isComposing ? (
            <EmailCompose />
          ) : (
            <>
              {/* Sidebar - Labels */}
              <div className="w-64 border-r border-border/30 flex flex-col">
                <div className="flex-1 overflow-y-auto p-4 space-y-1">
                  {systemLabels.map((label) => {
                    const LabelIcon = label.icon;
                    const isActive = currentLabelId === label.id;
                    return (
                      <button
                        key={label.id}
                        onClick={() => setCurrentLabel(label.id)}
                        className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                          isActive
                            ? 'bg-accent-cyan/10 text-accent-cyan'
                            : 'hover:bg-border/20 text-text-muted'
                        }`}
                      >
                        <LabelIcon className="w-4 h-4 shrink-0" />
                        <span className="text-sm flex-1 text-left">{label.name}</span>
                      </button>
                    );
                  })}

                  {labels.filter((l) => l.type === 'user').length > 0 && (
                    <>
                      <div className="h-px bg-border/30 my-3" />
                      {labels
                        .filter((l) => l.type === 'user')
                        .map((label) => {
                          const isActive = currentLabelId === label.id;
                          return (
                            <button
                              key={label.id}
                              onClick={() => setCurrentLabel(label.id)}
                              className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                                isActive
                                  ? 'bg-accent-cyan/10 text-accent-cyan'
                                  : 'hover:bg-border/20 text-text-muted'
                              }`}
                            >
                              <Archive className="w-4 h-4 shrink-0" />
                              <span className="text-sm flex-1 text-left">{label.name}</span>
                            </button>
                          );
                        })}
                    </>
                  )}
                </div>
              </div>

              {/* Messages List */}
              {currentAccountId && <EmailList accountId={currentAccountId} />}

              {/* Message Detail */}
              <AnimatePresence>
                {currentMessageId && currentAccountId && (
                  <EmailDetail accountId={currentAccountId} messageId={currentMessageId} />
                )}
              </AnimatePresence>
            </>
          )}
        </div>
      </div>
    );
  }

  // Mode modal (comportement original)
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={toggleEmailPanel}
      />

      {/* Panel */}
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="relative bg-surface border border-border rounded-xl shadow-2xl w-full max-w-7xl h-[90vh] flex flex-col overflow-hidden"
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-border/30">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-accent-cyan/20 to-accent-magenta/20 flex items-center justify-center">
              <Mail className="w-5 h-5 text-accent-cyan" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-text">Email</h2>
              {currentAccount && (
                <p className="text-xs text-text-muted">{currentAccount.email}</p>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2">
            {isConnected && (
              <>
                <Button variant="ghost" size="sm" onClick={handleCompose}>
                  <Plus className="w-4 h-4 mr-2" />
                  Nouveau
                </Button>
                <Button variant="ghost" size="sm" onClick={handleSync} disabled={syncing}>
                  <RefreshCw className={`w-4 h-4 ${syncing ? 'animate-spin' : ''}`} />
                </Button>
              </>
            )}
            <button
              onClick={toggleEmailPanel}
              className="p-2 hover:bg-border/30 rounded-lg transition-colors"
            >
              <X className="w-5 h-5 text-text-muted" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 flex overflow-hidden">
          {loading ? (
            <div className="flex-1 flex items-center justify-center">
              <Loader2 className="w-8 h-8 animate-spin text-accent-cyan" />
            </div>
          ) : error ? (
            <div className="flex-1 flex flex-col items-center justify-center gap-3">
              <p className="text-red-400">{error}</p>
              <Button variant="ghost" size="sm" onClick={loadAccounts}>
                Réessayer
              </Button>
            </div>
          ) : !isConnected ? (
            <div className="flex-1">
              <EmailSetupWizard onComplete={loadAccounts} onCancel={toggleEmailPanel} />
            </div>
          ) : isComposing ? (
            <EmailCompose />
          ) : (
            <>
              {/* Sidebar - Labels */}
              <div className="w-64 border-r border-border/30 flex flex-col">
                <div className="flex-1 overflow-y-auto p-4 space-y-1">
                  {/* System labels */}
                  {systemLabels.map((label) => {
                    const LabelIcon = label.icon;
                    const isActive = currentLabelId === label.id;
                    return (
                      <button
                        key={label.id}
                        onClick={() => setCurrentLabel(label.id)}
                        className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                          isActive
                            ? 'bg-accent-cyan/10 text-accent-cyan'
                            : 'hover:bg-border/20 text-text-muted'
                        }`}
                      >
                        <LabelIcon className="w-4 h-4 shrink-0" />
                        <span className="text-sm flex-1 text-left">{label.name}</span>
                      </button>
                    );
                  })}

                  {/* Custom labels */}
                  {labels.filter((l) => l.type === 'user').length > 0 && (
                    <>
                      <div className="h-px bg-border/30 my-3" />
                      {labels
                        .filter((l) => l.type === 'user')
                        .map((label) => {
                          const isActive = currentLabelId === label.id;
                          return (
                            <button
                              key={label.id}
                              onClick={() => setCurrentLabel(label.id)}
                              className={`w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-colors ${
                                isActive
                                  ? 'bg-accent-cyan/10 text-accent-cyan'
                                  : 'hover:bg-border/20 text-text-muted'
                              }`}
                            >
                              <Archive className="w-4 h-4 shrink-0" />
                              <span className="text-sm flex-1 text-left">{label.name}</span>
                            </button>
                          );
                        })}
                    </>
                  )}
                </div>
              </div>

              {/* Messages List */}
              {currentAccountId && <EmailList accountId={currentAccountId} />}

              {/* Message Detail */}
              <AnimatePresence>
                {currentMessageId && currentAccountId && (
                  <EmailDetail accountId={currentAccountId} messageId={currentMessageId} />
                )}
              </AnimatePresence>
            </>
          )}
        </div>
      </motion.div>
    </div>
  );
}
