/**
 * THÉRÈSE v2 - Email List
 *
 * List of email messages (virtualized for performance).
 * Phase 1 Frontend - Email
 */

import { useEffect, useState, useRef } from 'react';
import { Star, Paperclip, Loader2, Search, Trash2 } from 'lucide-react';
import { useEmailStore } from '../../stores/emailStore';
import * as api from '../../services/api';
import { EmailPriorityBadge } from './EmailPriorityBadge';

interface EmailListProps {
  accountId: string;
}

export function EmailList({ accountId }: EmailListProps) {
  const {
    messages,
    setMessages,
    updateMessage,
    removeMessage,
    currentMessageId,
    setCurrentMessage,
    currentLabelId,
    searchQuery,
    setSearchQuery,
    setNeedsReauth,
    refreshCounter,
  } = useEmailStore();

  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load messages when label or account changes (avec retry automatique)
  const retryCountRef = useRef(0);
  const abortControllerRef = useRef<AbortController | null>(null);
  const isLoadingRef = useRef(false);

  useEffect(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    retryCountRef.current = 0;
    isLoadingRef.current = false;
    loadMessages();
  }, [accountId, currentLabelId, refreshCounter]);

  // Cleanup au démontage
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  async function loadMessages() {
    // Garde : empêcher les chargements concurrents
    if (isLoadingRef.current) {
      console.log('[Email] loadMessages bloqué (chargement déjà en cours)');
      return;
    }
    isLoadingRef.current = true;
    console.log('[Email] loadMessages démarré', { accountId, labelId: currentLabelId, retry: retryCountRef.current });

    // Annuler le chargement précédent et créer un nouvel AbortController
    const controller = new AbortController();
    abortControllerRef.current = controller;

    // Cache-first : lire directement depuis le store (pas de closure stale)
    const hasCachedMessages = useEmailStore.getState().messages.length > 0;

    if (!hasCachedMessages) {
      setLoading(true);
    } else {
      setRefreshing(true);
    }
    setError(null);

    try {
      const labelIds = currentLabelId ? [currentLabelId] : undefined;
      const result = await api.listEmailMessages(accountId, {
        maxResults: 50,
        labelIds,
        query: searchQuery || undefined,
      });

      if (controller.signal.aborted) return;

      // BUG-061: Utiliser les données enrichies du list endpoint directement
      // Plus besoin de re-fetch chaque message individuellement (économise 50+ appels API)
      const errorMessages = (result.messages as any[]).filter((msg) => msg.error);
      if (errorMessages.length > 0) {
        console.warn(`BUG-061b: ${errorMessages.length}/${result.messages.length} emails en erreur:`, errorMessages[0]?.error);
      }
      const mappedMessages: api.EmailMessage[] = result.messages
        .filter((msg: any) => !msg.error)
        .map((msg: any) => {
          // Parser "Nom <email>" depuis le champ from
          const fromStr = msg.from || '';
          const fromMatch = fromStr.match(/^(.*?)\s*<(.+?)>$/);
          const from_name = fromMatch ? fromMatch[1].trim().replace(/^"|"$/g, '') : '';
          const from_email = fromMatch ? fromMatch[2] : fromStr;

          const msgLabelIds: string[] = msg.labelIds || [];

          // Récupérer la classification existante du cache local
          const cached = useEmailStore.getState().messages.find((m) => m.id === msg.id);

          return {
            id: msg.id,
            thread_id: msg.threadId || msg.id,
            subject: msg.subject || '(Sans objet)',
            from_email,
            from_name: from_name || null,
            to_emails: cached?.to_emails || [],
            date: msg.date || new Date().toISOString(),
            labels: msgLabelIds,
            is_read: msg.is_read ?? !msgLabelIds.includes('UNREAD'),
            is_starred: msg.is_starred ?? msgLabelIds.includes('STARRED'),
            is_draft: msgLabelIds.includes('DRAFT'),
            has_attachments: cached?.has_attachments || false,
            snippet: msg.snippet || null,
            body_plain: cached?.body_plain || null,
            body_html: cached?.body_html || null,
            // Conserver la classification existante du cache
            priority: cached?.priority || null,
            priority_score: cached?.priority_score || null,
            priority_reason: cached?.priority_reason || null,
            category: cached?.category || null,
          } as api.EmailMessage;
        });

      if (controller.signal.aborted) return;

      // Afficher les messages immédiatement (pas de blocage)
      setMessages(mappedMessages);

      // Classifier en arrière-plan (ne bloque plus le refresh)
      classifyInBackground(mappedMessages, accountId, controller);
    } catch (err) {
      if (controller.signal.aborted) return;

      // BUG-066: Diagnostic complet de l'erreur (avant c'était opaque)
      const errMsg = err instanceof Error ? err.message : String(err);
      const isNetworkError = err instanceof TypeError || errMsg.includes('Load failed') || errMsg.includes('Failed to fetch');
      const isAuthError = errMsg.includes('expired') || errMsg.includes('revoked') || errMsg.includes('401') || errMsg.includes('Token');

      console.error('[Email] Échec chargement messages:', {
        message: errMsg,
        type: isNetworkError ? 'NETWORK' : isAuthError ? 'AUTH' : 'API',
        retry: `${retryCountRef.current}/3`,
        accountId,
        labelId: currentLabelId,
        error: err,
      });

      // Retry automatique (max 3 tentatives, délai croissant)
      if (retryCountRef.current < 3) {
        retryCountRef.current++;
        const delay = retryCountRef.current * 1500; // 1.5s, 3s, 4.5s
        console.log(`[Email] Retry ${retryCountRef.current}/3 dans ${delay}ms...`);
        isLoadingRef.current = false;
        setTimeout(() => loadMessages(), delay);
        return;
      }

      // Détecter expiration token OAuth (BUG-029)
      if (isAuthError) {
        setError('Connexion Gmail expirée - reconnecte-toi.');
        setNeedsReauth(true);
      } else if (isNetworkError) {
        // BUG-066: Erreur réseau identifiée clairement
        setError('Erreur réseau - le backend ne répond pas');
        const stillHasCache = useEmailStore.getState().messages.length > 0;
        if (stillHasCache) {
          setTimeout(() => setError(null), 4000);
        }
      } else {
        // BUG-066: Afficher l'erreur réelle au lieu du message générique
        const displayMsg = errMsg.length > 80 ? errMsg.slice(0, 80) + '...' : errMsg;
        setError(`Échec du rafraîchissement : ${displayMsg}`);
        const stillHasCache = useEmailStore.getState().messages.length > 0;
        if (stillHasCache) {
          setTimeout(() => setError(null), 6000);
        }
      }
    } finally {
      if (!controller.signal.aborted) {
        setLoading(false);
        setRefreshing(false);
      }
      isLoadingRef.current = false;
    }
  }

  // BUG-061: Classification en arrière-plan (ne bloque plus le refresh)
  async function classifyInBackground(
    msgs: api.EmailMessage[],
    acctId: string,
    controller: AbortController,
  ) {
    const unclassified = msgs.filter((m) => !m.priority);
    if (unclassified.length === 0) return;

    for (const msg of unclassified) {
      if (controller.signal.aborted) return;
      try {
        const classification = await api.classifyEmail(msg.id, acctId, false);
        if (controller.signal.aborted) return;
        // Mettre à jour le message individuellement dans le store
        updateMessage(msg.id, {
          priority: classification.priority,
          priority_score: classification.score,
          priority_reason: classification.reason,
          category: classification.category,
        });
      } catch {
        // Classification échouée = pas grave, on continue
      }
    }
  }

  async function handleTrash(e: React.MouseEvent, messageId: string) {
    e.stopPropagation();
    try {
      // BUG-030 : attendre la confirmation API AVANT de retirer de l'UI
      await api.deleteEmailMessage(accountId, messageId, false);
      removeMessage(messageId);
      if (currentMessageId === messageId) {
        setCurrentMessage(null);
      }
    } catch (err: any) {
      console.error('Failed to trash message:', err);
      const msg = err?.message || '';
      if (msg.includes('expired') || msg.includes('revoked') || msg.includes('Token')) {
        setError('Connexion Gmail expirée - reconnecte-toi.');
        setNeedsReauth(true);
        setTimeout(() => setError(null), 5000);
      } else {
        // Retirer le message de l'UI même en cas d'erreur non-auth :
        // Gmail a probablement déjà traité la suppression côté serveur
        removeMessage(messageId);
        if (currentMessageId === messageId) {
          setCurrentMessage(null);
        }
      }
    }
  }

  function formatDate(dateStr: string): string {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) {
      return date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
    } else if (diffDays === 1) {
      return 'Hier';
    } else if (diffDays < 7) {
      return date.toLocaleDateString('fr-FR', { weekday: 'short' });
    } else {
      return date.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' });
    }
  }

  return (
    <div className="w-96 shrink-0 min-w-0 border-r border-border/30 flex flex-col">
      {/* Search */}
      <div className="p-4 border-b border-border/30">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Rechercher..."
            className="w-full pl-10 pr-4 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:ring-2 focus:ring-accent-cyan/50"
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                loadMessages();
              }
            }}
          />
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto relative">
        {/* Indicateur de rafraîchissement */}
        {refreshing && (
          <div className="absolute top-0 left-0 right-0 z-10 flex items-center justify-center py-2 bg-accent-cyan/10 backdrop-blur-sm border-b border-accent-cyan/20">
            <Loader2 className="w-4 h-4 animate-spin text-accent-cyan mr-2" />
            <span className="text-sm font-medium text-accent-cyan">Mise à jour des messages...</span>
          </div>
        )}
        {/* BUG-061: Erreur non-bloquante quand on a du cache */}
        {error && messages.length > 0 && (
          <div className="absolute top-0 left-0 right-0 z-10 flex items-center justify-center py-2 bg-red-500/10 backdrop-blur-sm border-b border-red-500/20">
            <span className="text-sm font-medium text-red-400">{error}</span>
          </div>
        )}
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin text-accent-cyan" />
          </div>
        ) : error && messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 px-4 text-center">
            <p className="text-sm text-red-400">{error}</p>
          </div>
        ) : messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 px-4 text-center">
            <p className="text-sm text-text-muted">Aucun message</p>
          </div>
        ) : (
          <div className="divide-y divide-border/30">
            {messages.map((message) => {
              const isActive = currentMessageId === message.id;
              const isUnread = !message.is_read;

              return (
                <button
                  key={message.id}
                  onClick={() => setCurrentMessage(message.id)}
                  className={`group w-full text-left px-4 py-3 hover:bg-border/10 transition-colors ${
                    isActive ? 'bg-accent-cyan/5' : ''
                  } ${isUnread ? 'bg-background/40' : ''}`}
                >
                  <div className="flex items-start justify-between gap-2 mb-1">
                    <div className="flex items-center gap-2 flex-1 min-w-0">
                      {message.is_starred && <Star className="w-3 h-3 text-yellow-400 shrink-0" />}
                      <div className="w-8 shrink-0 flex items-center justify-center">
                        {message.priority && (
                          <EmailPriorityBadge
                            priority={message.priority}
                            score={message.priority_score || undefined}
                          />
                        )}
                      </div>
                      <span
                        className={`text-sm font-medium truncate ${
                          isUnread ? 'text-text' : 'text-text-muted'
                        }`}
                      >
                        {message.from_name || message.from_email}
                      </span>
                    </div>
                    {/* Bouton supprimer (visible au hover, remplace la date) */}
                    <span
                      className="text-xs text-text-muted shrink-0 group-hover:hidden"
                    >
                      {formatDate(message.date)}
                    </span>
                    <span
                      className="shrink-0 hidden group-hover:inline-flex"
                      onClick={(e) => handleTrash(e, message.id)}
                      role="button"
                      title="Supprimer"
                    >
                      <Trash2 className="w-3.5 h-3.5 text-text-muted hover:text-red-400 transition-colors" />
                    </span>
                  </div>

                  <div className="flex items-center gap-2 mb-1">
                    <p
                      className={`text-sm font-medium truncate flex-1 ${
                        isUnread ? 'text-text' : 'text-text-muted'
                      }`}
                    >
                      {message.subject || '(Sans objet)'}
                    </p>
                    {message.has_attachments && (
                      <Paperclip className="w-3 h-3 text-text-muted shrink-0" />
                    )}
                  </div>

                  <p className="text-xs text-text-muted line-clamp-2">{message.snippet}</p>
                </button>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
