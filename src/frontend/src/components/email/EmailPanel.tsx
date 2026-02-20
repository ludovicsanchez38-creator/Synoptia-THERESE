/**
 * THÉRÈSE v2 - Email Panel
 *
 * Main email panel component (modal/sidebar).
 * Phase 1 Frontend - Email
 */

import { useEffect, useState, useRef } from 'react';
import { motion } from 'framer-motion';
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
  Loader2,
  UserPlus,
  ChevronDown,
  AlertTriangle,
  ExternalLink,
  LogOut,
} from 'lucide-react';
import { open } from '@tauri-apps/plugin-shell';
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
    needsReauth,
    setNeedsReauth,
  } = useEmailStore();

  // Cache-first : si le store a déjà des données (localStorage), pas de spinner
  const hasCachedAccounts = accounts.length > 0 && !!currentAccountId;
  const [loading, setLoading] = useState(!hasCachedAccounts);
  const [error, setError] = useState<string | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [showAddAccount, setShowAddAccount] = useState(false);
  const [showAccountMenu, setShowAccountMenu] = useState(false);
  const [reauthing, setReauthing] = useState(false);
  // Contrôle l'affichage du wizard indépendamment de isConnected.
  // Initialisé à true pour l'afficher automatiquement si aucun compte.
  // Mis à false quand l'utilisateur clique la croix du wizard.
  const [showSetupWizard, setShowSetupWizard] = useState(true);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Load accounts on mount (standalone ou modal)
  useEffect(() => {
    if (standalone || isEmailPanelOpen) {
      loadAccounts();
    }
  }, [standalone, isEmailPanelOpen]);

  async function loadAccounts() {
    // Si on a des données en cache, ne pas bloquer l'affichage
    if (!hasCachedAccounts) {
      setLoading(true);
    }
    setError(null);

    // Tenter de rafraîchir les comptes depuis l'API
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

      // Fallback : utiliser les comptes déjà dans le store (cache localStorage)
      if (accounts.length > 0 && currentAccountId) {
        console.log('Using cached accounts and labels');
        // Labels et messages sont aussi en cache via le store persist
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
      setNeedsReauth(false);
    } catch (err: any) {
      console.error('Failed to load labels:', err);
      // Détecter si c'est un problème de token expiré
      if (err?.message?.includes('401') || err?.message?.includes('token') || err?.message?.includes('expired')) {
        setNeedsReauth(true);
      }
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

  function handleAddAccountComplete() {
    setShowAddAccount(false);
    setShowSetupWizard(true);
    loadAccounts();
  }

  function switchAccount(accountId: string) {
    setCurrentAccount(accountId);
    setShowAccountMenu(false);
    loadLabels(accountId);
  }

  async function handleDisconnectAccount(accountId: string) {
    try {
      await api.disconnectEmailAccount(accountId);
      setShowAccountMenu(false);
      await loadAccounts();
    } catch (err) {
      console.error('Failed to disconnect account:', err);
    }
  }

  async function handleReauthorize() {
    if (!currentAccountId || reauthing) return;
    setReauthing(true);

    try {
      const flow = await api.reauthorizeEmail(currentAccountId);

      // Ouvrir le navigateur
      try {
        await open(flow.auth_url);
      } catch {
        window.open(flow.auth_url, '_blank');
      }

      // Poller le status pour détecter quand le token est renouvelé
      let attempts = 0;
      const maxAttempts = 100; // ~5 min à 3s d'intervalle
      pollRef.current = setInterval(async () => {
        attempts++;
        if (attempts > maxAttempts) {
          if (pollRef.current) clearInterval(pollRef.current);
          setReauthing(false);
          return;
        }
        try {
          // Tester si les labels se chargent (= token valide)
          await api.listEmailLabels(currentAccountId);
          if (pollRef.current) clearInterval(pollRef.current);
          setNeedsReauth(false);
          setReauthing(false);
          // Recharger les données
          loadAccounts();
        } catch {
          // Pas encore réautorisé
        }
      }, 3000);
    } catch (err) {
      console.error('Reauthorize failed:', err);
      setReauthing(false);
    }
  }

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

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
              {/* Sélecteur de compte */}
              {accounts.length > 1 ? (
                <div className="relative">
                  <button
                    onClick={() => setShowAccountMenu(!showAccountMenu)}
                    className="flex items-center gap-1 text-xs text-text-muted hover:text-accent-cyan transition-colors"
                  >
                    {currentAccount?.email || 'Sélectionner'}
                    <ChevronDown className="w-3 h-3" />
                  </button>
                  {showAccountMenu && (
                    <div className="absolute top-full left-0 mt-1 bg-surface border border-border/50 rounded-lg shadow-xl py-1 z-20 min-w-[250px]">
                      {accounts.map((acc) => (
                        <div key={acc.id} className="flex items-center">
                          <button
                            onClick={() => switchAccount(acc.id)}
                            className={`flex-1 text-left px-3 py-2 text-sm hover:bg-border/20 transition-colors ${
                              acc.id === currentAccountId ? 'text-accent-cyan bg-accent-cyan/5' : 'text-text-muted'
                            }`}
                          >
                            {acc.email}
                          </button>
                          <button
                            onClick={() => handleDisconnectAccount(acc.id)}
                            className="px-2 py-2 text-text-muted hover:text-red-400 hover:bg-red-500/10 transition-colors"
                            title="Déconnecter ce compte"
                          >
                            <LogOut className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      ))}
                      <div className="h-px bg-border/30 my-1" />
                      <button
                        onClick={() => { setShowAccountMenu(false); setShowAddAccount(true); }}
                        className="w-full text-left px-3 py-2 text-sm text-text-muted hover:bg-border/20 transition-colors flex items-center gap-2"
                      >
                        <UserPlus className="w-3.5 h-3.5" />
                        Ajouter un compte
                      </button>
                    </div>
                  )}
                </div>
              ) : currentAccount ? (
                <div className="flex items-center gap-2">
                  <p className="text-xs text-text-muted">{currentAccount.email}</p>
                  <button
                    onClick={() => handleDisconnectAccount(currentAccount.id)}
                    className="p-0.5 text-text-muted hover:text-red-400 transition-colors"
                    title="Déconnecter ce compte"
                  >
                    <LogOut className="w-3 h-3" />
                  </button>
                </div>
              ) : null}
            </div>
          </div>

          <div className="flex items-center gap-2">
            {isConnected && (
              <>
                <Button variant="ghost" size="sm" onClick={handleCompose}>
                  <Plus className="w-4 h-4 mr-2" />
                  Nouveau
                </Button>
                <Button variant="ghost" size="sm" onClick={() => setShowAddAccount(true)} title="Ajouter un compte">
                  <UserPlus className="w-4 h-4" />
                </Button>
                <Button variant="ghost" size="sm" onClick={handleSync} disabled={syncing}>
                  <RefreshCw className={`w-4 h-4 ${syncing ? 'animate-spin' : ''}`} />
                </Button>
              </>
            )}
          </div>
        </div>

        {/* Bannière réautorisation */}
        {needsReauth && (
          <div className="px-4 py-2 bg-yellow-500/10 border-b border-yellow-500/20 flex items-center gap-3">
            <AlertTriangle className="w-4 h-4 text-yellow-400 shrink-0" />
            <p className="text-sm text-yellow-200 flex-1">
              Connexion Gmail expirée. Reconnecte-toi pour continuer.
            </p>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleReauthorize}
              disabled={reauthing}
              className="text-yellow-300 hover:text-yellow-100 shrink-0"
            >
              {reauthing ? (
                <>
                  <Loader2 className="w-3 h-3 animate-spin mr-2" />
                  En attente...
                </>
              ) : (
                <>
                  <ExternalLink className="w-3 h-3 mr-2" />
                  Reconnecter
                </>
              )}
            </Button>
          </div>
        )}

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
          ) : (!isConnected && showSetupWizard) || showAddAccount ? (
            <div className="flex-1">
              <EmailSetupWizard
                onComplete={handleAddAccountComplete}
                onCancel={() => {
                  setShowAddAccount(false);
                  setShowSetupWizard(false);
                }}
              />
            </div>
          ) : !isConnected ? (
            <div className="flex-1 flex flex-col items-center justify-center gap-4">
              <Mail className="w-12 h-12 text-text-muted/40" />
              <p className="text-text-muted text-sm">Aucun compte email configuré.</p>
              <Button variant="primary" size="sm" onClick={() => setShowSetupWizard(true)}>
                Configurer un compte
              </Button>
            </div>
          ) : isComposing ? (
            <EmailCompose />
          ) : (
            <>
              {/* Sidebar - Labels */}
              <div className="w-64 shrink-0 border-r border-border/30 flex flex-col">
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
              {currentMessageId && currentAccountId && (
                <EmailDetail accountId={currentAccountId} messageId={currentMessageId} />
              )}
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
              {/* Sélecteur de compte */}
              {accounts.length > 1 ? (
                <div className="relative">
                  <button
                    onClick={() => setShowAccountMenu(!showAccountMenu)}
                    className="flex items-center gap-1 text-xs text-text-muted hover:text-accent-cyan transition-colors"
                  >
                    {currentAccount?.email || 'Sélectionner'}
                    <ChevronDown className="w-3 h-3" />
                  </button>
                  {showAccountMenu && (
                    <div className="absolute top-full left-0 mt-1 bg-surface border border-border/50 rounded-lg shadow-xl py-1 z-20 min-w-[250px]">
                      {accounts.map((acc) => (
                        <div key={acc.id} className="flex items-center">
                          <button
                            onClick={() => switchAccount(acc.id)}
                            className={`flex-1 text-left px-3 py-2 text-sm hover:bg-border/20 transition-colors ${
                              acc.id === currentAccountId ? 'text-accent-cyan bg-accent-cyan/5' : 'text-text-muted'
                            }`}
                          >
                            {acc.email}
                          </button>
                          <button
                            onClick={() => handleDisconnectAccount(acc.id)}
                            className="px-2 py-2 text-text-muted hover:text-red-400 hover:bg-red-500/10 transition-colors"
                            title="Déconnecter ce compte"
                          >
                            <LogOut className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      ))}
                      <div className="h-px bg-border/30 my-1" />
                      <button
                        onClick={() => { setShowAccountMenu(false); setShowAddAccount(true); }}
                        className="w-full text-left px-3 py-2 text-sm text-text-muted hover:bg-border/20 transition-colors flex items-center gap-2"
                      >
                        <UserPlus className="w-3.5 h-3.5" />
                        Ajouter un compte
                      </button>
                    </div>
                  )}
                </div>
              ) : currentAccount ? (
                <div className="flex items-center gap-2">
                  <p className="text-xs text-text-muted">{currentAccount.email}</p>
                  <button
                    onClick={() => handleDisconnectAccount(currentAccount.id)}
                    className="p-0.5 text-text-muted hover:text-red-400 transition-colors"
                    title="Déconnecter ce compte"
                  >
                    <LogOut className="w-3 h-3" />
                  </button>
                </div>
              ) : null}
            </div>
          </div>

          <div className="flex items-center gap-2">
            {isConnected && (
              <>
                <Button variant="ghost" size="sm" onClick={handleCompose}>
                  <Plus className="w-4 h-4 mr-2" />
                  Nouveau
                </Button>
                <Button variant="ghost" size="sm" onClick={() => setShowAddAccount(true)} title="Ajouter un compte">
                  <UserPlus className="w-4 h-4" />
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

        {/* Bannière réautorisation */}
        {needsReauth && (
          <div className="px-4 py-2 bg-yellow-500/10 border-b border-yellow-500/20 flex items-center gap-3">
            <AlertTriangle className="w-4 h-4 text-yellow-400 shrink-0" />
            <p className="text-sm text-yellow-200 flex-1">
              Connexion Gmail expirée. Reconnecte-toi pour continuer.
            </p>
            <Button
              variant="ghost"
              size="sm"
              onClick={handleReauthorize}
              disabled={reauthing}
              className="text-yellow-300 hover:text-yellow-100 shrink-0"
            >
              {reauthing ? (
                <>
                  <Loader2 className="w-3 h-3 animate-spin mr-2" />
                  En attente...
                </>
              ) : (
                <>
                  <ExternalLink className="w-3 h-3 mr-2" />
                  Reconnecter
                </>
              )}
            </Button>
          </div>
        )}

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
          ) : (!isConnected && showSetupWizard) || showAddAccount ? (
            <div className="flex-1">
              <EmailSetupWizard
                onComplete={handleAddAccountComplete}
                onCancel={() => {
                  setShowAddAccount(false);
                  setShowSetupWizard(false);
                  if (!showAddAccount) toggleEmailPanel();
                }}
              />
            </div>
          ) : isComposing ? (
            <EmailCompose />
          ) : (
            <>
              {/* Sidebar - Labels */}
              <div className="w-64 shrink-0 border-r border-border/30 flex flex-col">
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
              {currentMessageId && currentAccountId && (
                <EmailDetail accountId={currentAccountId} messageId={currentMessageId} />
              )}
            </>
          )}
        </div>
      </motion.div>
    </div>
  );
}
