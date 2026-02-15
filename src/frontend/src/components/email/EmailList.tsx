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
    removeMessage,
    currentMessageId,
    setCurrentMessage,
    currentLabelId,
    searchQuery,
    setSearchQuery,
    setNeedsReauth,
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
  }, [accountId, currentLabelId]);

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
    if (isLoadingRef.current) return;
    isLoadingRef.current = true;

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

      // Fetch full details for each message
      const messagesWithDetails = await Promise.all(
        result.messages.map(async (msg) => {
          try {
            return await api.getEmailMessage(accountId, msg.id);
          } catch (err) {
            console.error(`Failed to load message ${msg.id}:`, err);
            return null;
          }
        })
      );

      if (controller.signal.aborted) return;

      const validMessages = messagesWithDetails.filter((m): m is api.EmailMessage => m !== null);

      // Classifier uniquement les messages qui n'ont pas encore de classification
      const classifiedMessages = await Promise.all(
        validMessages.map(async (msg) => {
          // Si déjà classifié, garder la classification existante
          if (msg.priority) {
            return msg;
          }
          try {
            const classification = await api.classifyEmail(msg.id, accountId, false);
            return {
              ...msg,
              priority: classification.priority,
              priority_score: classification.score,
              priority_reason: classification.reason,
              category: classification.category
            };
          } catch (err) {
            console.error(`Failed to classify message ${msg.id}:`, err);
            return msg;
          }
        })
      );

      if (controller.signal.aborted) return;

      setMessages(classifiedMessages);
    } catch (err) {
      if (controller.signal.aborted) return;
      console.error('Failed to load messages:', err);
      // Retry automatique (max 3 tentatives, délai croissant)
      if (retryCountRef.current < 3) {
        retryCountRef.current++;
        const delay = retryCountRef.current * 1500; // 1.5s, 3s, 4.5s
        console.log(`Retry ${retryCountRef.current}/3 dans ${delay}ms...`);
        isLoadingRef.current = false;
        setTimeout(() => loadMessages(), delay);
        return;
      }
      // Si on a du cache, ne pas afficher d'erreur bloquante
      const stillHasCache = useEmailStore.getState().messages.length > 0;
      if (!stillHasCache) {
        setError('Impossible de charger les messages');
      }
    } finally {
      if (!controller.signal.aborted) {
        setLoading(false);
        setRefreshing(false);
      }
      isLoadingRef.current = false;
    }
  }

  async function handleTrash(e: React.MouseEvent, messageId: string) {
    e.stopPropagation();
    try {
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
      } else {
        setError('Impossible de supprimer ce message.');
      }
      // Effacer le message d'erreur après 5 secondes
      setTimeout(() => setError(null), 5000);
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
        {/* Indicateur de rafraîchissement discret (overlay, ne pousse pas le contenu) */}
        {refreshing && (
          <div className="absolute top-0 left-0 right-0 z-10 flex items-center justify-center py-1 bg-accent-cyan/5 backdrop-blur-sm border-b border-border/20">
            <Loader2 className="w-3 h-3 animate-spin text-accent-cyan mr-2" />
            <span className="text-xs text-text-muted">Mise à jour...</span>
          </div>
        )}
        {loading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin text-accent-cyan" />
          </div>
        ) : error ? (
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
