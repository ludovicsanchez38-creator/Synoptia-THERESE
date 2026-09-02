/**
 * THÉRÈSE v2 - Email List
 *
 * List of email messages (virtualized for performance).
 * Phase 1 Frontend - Email
 */

import { useEffect, useState, useRef } from 'react';
import { Star, Paperclip, Search, Trash2 } from 'lucide-react';
import { useEmailStore } from '../../stores/emailStore';
import * as api from '../../services/api';
import { EmailPriorityBadge } from './EmailPriorityBadge';
import { mapEmailList } from '../prototype/emailReadModels';
import { useExternalActionConfirmation } from '../app/useExternalActionConfirmation';
import { Spinner } from '../ui/Spinner';

interface EmailListProps {
  accountId: string;
}

export function EmailList({ accountId }: EmailListProps) {
  const requestExternalAction = useExternalActionConfirmation();
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
    hasMore,
    setHasMore,
    pageToken,
    setPageToken,
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

      // BUG-122 : dossier spécial introuvable côté serveur -> le backend
      // assume une liste vide avec avertissement ; ne surtout pas laisser
      // l'ancienne liste (souvent l'INBOX) s'afficher sous cet onglet.
      if (result.warning) {
        setMessages([]);
        // F3b revue : sans purge de la sélection, le volet droit affichait
        // « Message introuvable » au lieu de l'état vide.
        setCurrentMessage(null);
        setError(result.warning);
        setHasMore(false);
        setPageToken(null);
        return;
      }

      // BUG-061: Utiliser les données enrichies du list endpoint directement
      // Plus besoin de re-fetch chaque message individuellement (économise 50+ appels API)
      const errorMessages = (result.messages as any[]).filter((msg) => msg.error);
      if (errorMessages.length > 0) {
        console.warn(`BUG-061b: ${errorMessages.length}/${result.messages.length} emails en erreur:`, errorMessages[0]?.error);
      }
      const mappedMessages = mapEmailList(
        result.messages,
        useEmailStore.getState().messages,
      );

      if (controller.signal.aborted) return;

      // Afficher les messages immédiatement (pas de blocage)
      setMessages(mappedMessages);
      // Lot F : le jeton existait dans le store, aucun bouton ne s'en servait.
      setPageToken(result.nextPageToken ?? null);
      setHasMore(Boolean(result.nextPageToken));

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

  async function loadMore() {
    const token = pageToken;
    if (!token || isLoadingRef.current) return;
    isLoadingRef.current = true;
    try {
      const labelIds = currentLabelId ? [currentLabelId] : undefined;
      const result = await api.listEmailMessages(accountId, {
        maxResults: 50,
        labelIds,
        query: searchQuery || undefined,
        pageToken: token,
      });
      const deja = new Set(useEmailStore.getState().messages.map((m) => m.id));
      const mapped = mapEmailList(
        result.messages,
        useEmailStore.getState().messages,
      ).filter((m) => !deja.has(m.id));
      setMessages([...useEmailStore.getState().messages, ...mapped]);
      setPageToken(result.nextPageToken ?? null);
      setHasMore(Boolean(result.nextPageToken));
    } catch (err) {
      console.error('[Email] Échec chargement page suivante:', err);
      setError('Impossible de charger la suite.');
    } finally {
      isLoadingRef.current = false;
    }
  }

  function handleTrash(e: React.MouseEvent, messageId: string) {
    e.stopPropagation();
    const message = messages.find((item) => item.id === messageId);
    if (!message) return;

    requestExternalAction({
      title: 'Confirmer la mise à la corbeille',
      description: 'Vérifie le message. Il ne sera déplacé qu’après ta confirmation.',
      confirmLabel: 'Mettre à la corbeille',
      details: [
        { label: 'Expéditeur', value: message.from_name || message.from_email },
        { label: 'Objet', value: message.subject || '(Sans objet)' },
      ],
    }, async () => {
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
    });
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
          <input aria-label="Rechercher dans les messages"
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Rechercher..."
            className="w-full pl-10 pr-4 py-2 bg-background/60 border border-border/50 rounded-md text-sm text-text placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-ring/50"
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
            <Spinner taille="bouton" className="text-accent-cyan-ink mr-2" />
            <span className="text-sm font-medium text-accent-cyan-ink">Mise à jour des messages...</span>
          </div>
        )}
        {/* BUG-061: Erreur non-bloquante quand on a du cache */}
        {error && messages.length > 0 && (
          <div role="alert" className="absolute top-0 left-0 right-0 z-10 flex items-center justify-center py-2 bg-error/10 backdrop-blur-sm border-b border-error/20">
            <span className="text-sm font-medium text-error">{error}</span>
          </div>
        )}
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Spinner taille="zone" className="text-accent-cyan-ink" />
          </div>
        ) : error && messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-8 px-4 text-center">
            <p className="text-sm text-error">{error}</p>
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
                // B-092 : la corbeille était un <span role="button"> sans
                // tabIndex, IMBRIQUÉ dans le bouton de la ligne — imbrication
                // interdite et hors de tout ordre de tabulation. Les deux
                // commandes sont désormais deux boutons frères.
                <div
                  key={message.id}
                  className={`group relative ${isActive ? 'bg-accent-cyan/5' : ''} ${
                    isUnread ? 'bg-background/40' : ''
                  }`}
                >
                <button
                  onClick={() => setCurrentMessage(message.id)}
                  className="w-full text-left px-4 py-3 hover:bg-border/10 transition-colors"
                >
                  <div className="flex items-start justify-between gap-2 mb-1">
                    <div className="flex items-center gap-2 flex-1 min-w-0">
                      {message.is_starred && <Star className="w-3 h-3 text-warning shrink-0" />}
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
                      className="text-xs text-text-muted shrink-0 group-hover:invisible group-focus-within:invisible"
                    >
                      {formatDate(message.date)}
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
                {/* Frère du bouton de ligne : atteignable au clavier (l'opacité
                    le montre au survol comme au focus ; `hidden` l'aurait
                    retiré de l'ordre de tabulation). */}
                <button
                  type="button"
                  onClick={(e) => handleTrash(e, message.id)}
                  className="absolute right-4 top-3 inline-flex shrink-0 rounded-sm p-0.5 opacity-0 pointer-events-none transition-opacity group-hover:opacity-100 group-hover:pointer-events-auto group-focus-within:opacity-100 group-focus-within:pointer-events-auto focus-visible:opacity-100 focus-visible:pointer-events-auto focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  title="Supprimer"
                  aria-label={`Supprimer le message « ${message.subject || '(Sans objet)'} »`}
                >
                  <Trash2 className="w-3.5 h-3.5 text-text-muted hover:text-error transition-colors" />
                </button>
                </div>
              );
            })}
            {hasMore && (
              <div className="p-3">
                <button
                  type="button"
                  onClick={() => void loadMore()}
                  className="w-full px-3 py-2 rounded-md text-sm bg-surface-elevated text-text hover:bg-surface-elevated/70"
                >
                  Charger la suite
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
