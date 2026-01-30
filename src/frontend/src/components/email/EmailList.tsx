/**
 * THÉRÈSE v2 - Email List
 *
 * List of email messages (virtualized for performance).
 * Phase 1 Frontend - Email
 */

import { useEffect, useState } from 'react';
import { Star, Paperclip, Loader2, Search } from 'lucide-react';
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
    currentMessageId,
    setCurrentMessage,
    currentLabelId,
    searchQuery,
    setSearchQuery,
  } = useEmailStore();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load messages when label or account changes
  useEffect(() => {
    loadMessages();
  }, [accountId, currentLabelId]);

  async function loadMessages() {
    setLoading(true);
    setError(null);

    try {
      const labelIds = currentLabelId ? [currentLabelId] : undefined;
      const result = await api.listEmailMessages(accountId, {
        maxResults: 50,
        labelIds,
        query: searchQuery || undefined,
      });

      // Fetch full details for each message (in production, use batch or pagination)
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

      const validMessages = messagesWithDetails.filter((m): m is api.EmailMessage => m !== null);

      // Auto-classify messages (force V2 pour appliquer nouvelles règles)
      const classifiedMessages = await Promise.all(
        validMessages.map(async (msg) => {
          try {
            // Force reclassification pour appliquer V2 (cal.com business, etc.)
            const classification = await api.classifyEmail(msg.id, accountId, true);
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

      setMessages(classifiedMessages);
    } catch (err) {
      console.error('Failed to load messages:', err);
      setError('Impossible de charger les messages');
    } finally {
      setLoading(false);
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
    <div className="w-96 border-r border-border/30 flex flex-col">
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
      <div className="flex-1 overflow-y-auto">
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
                  className={`w-full text-left px-4 py-3 hover:bg-border/10 transition-colors ${
                    isActive ? 'bg-accent-cyan/5' : ''
                  } ${isUnread ? 'bg-background/40' : ''}`}
                >
                  <div className="flex items-start justify-between gap-2 mb-1">
                    <div className="flex items-center gap-2 flex-1 min-w-0">
                      {message.is_starred && <Star className="w-3 h-3 text-yellow-400 shrink-0" />}
                      {message.priority && (
                        <EmailPriorityBadge
                          priority={message.priority}
                          score={message.priority_score || undefined}
                          className="shrink-0"
                        />
                      )}
                      <span
                        className={`text-sm truncate ${
                          isUnread ? 'font-semibold text-text' : 'text-text-muted'
                        }`}
                      >
                        {message.from_name || message.from_email}
                      </span>
                    </div>
                    <span className="text-xs text-text-muted shrink-0">{formatDate(message.date)}</span>
                  </div>

                  <div className="flex items-center gap-2 mb-1">
                    <p
                      className={`text-sm truncate flex-1 ${
                        isUnread ? 'font-medium text-text' : 'text-text-muted'
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
