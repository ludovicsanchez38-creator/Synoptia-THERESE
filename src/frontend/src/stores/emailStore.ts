/**
 * THÉRÈSE v2 - Email Store
 *
 * Zustand store for email management.
 * Phase 1 Frontend - Email
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { EmailAccount, EmailMessage, EmailLabel } from '../services/api';

interface EmailStore {
  // Accounts
  accounts: EmailAccount[];
  currentAccountId: string | null;
  setAccounts: (accounts: EmailAccount[]) => void;
  addAccount: (account: EmailAccount) => void;
  removeAccount: (accountId: string) => void;
  setCurrentAccount: (accountId: string | null) => void;

  // Messages
  messages: EmailMessage[];
  currentMessageId: string | null;
  setMessages: (messages: EmailMessage[]) => void;
  addMessage: (message: EmailMessage) => void;
  updateMessage: (messageId: string, updates: Partial<EmailMessage>) => void;
  removeMessage: (messageId: string) => void;
  setCurrentMessage: (messageId: string | null) => void;

  // Labels
  labels: EmailLabel[];
  currentLabelId: string | null;
  setLabels: (labels: EmailLabel[]) => void;
  addLabel: (label: EmailLabel) => void;
  updateLabel: (labelId: string, updates: Partial<EmailLabel>) => void;
  removeLabel: (labelId: string) => void;
  setCurrentLabel: (labelId: string | null) => void;

  // UI State
  isEmailPanelOpen: boolean;
  isComposing: boolean;
  draftRecipients: string[];
  draftSubject: string;
  draftBody: string;
  draftIsHtml: boolean;
  toggleEmailPanel: () => void;
  setIsComposing: (isComposing: boolean) => void;
  setDraftRecipients: (recipients: string[]) => void;
  setDraftSubject: (subject: string) => void;
  setDraftBody: (body: string) => void;
  setDraftIsHtml: (isHtml: boolean) => void;
  clearDraft: () => void;
  startComposing: (recipients: string[], subject: string, body: string) => void;

  // Auth
  needsReauth: boolean;
  setNeedsReauth: (needsReauth: boolean) => void;

  // Filters & Search
  searchQuery: string;
  selectedLabels: string[];
  setSearchQuery: (query: string) => void;
  setSelectedLabels: (labels: string[]) => void;
  toggleLabel: (labelId: string) => void;

  // Pagination
  pageToken: string | null;
  hasMore: boolean;
  setPageToken: (token: string | null) => void;
  setHasMore: (hasMore: boolean) => void;
}

export const useEmailStore = create<EmailStore>()(
  persist(
    (set, get) => ({
      // Accounts
      accounts: [],
      currentAccountId: null,
      setAccounts: (accounts) => set({ accounts }),
      addAccount: (account) => set({ accounts: [...get().accounts, account] }),
      removeAccount: (accountId) =>
        set({
          accounts: get().accounts.filter((a) => a.id !== accountId),
          currentAccountId: get().currentAccountId === accountId ? null : get().currentAccountId,
        }),
      setCurrentAccount: (accountId) => set({ currentAccountId: accountId }),

      // Messages
      messages: [],
      currentMessageId: null,
      setMessages: (messages) => set({ messages }),
      addMessage: (message) => set({ messages: [message, ...get().messages] }),
      updateMessage: (messageId, updates) =>
        set({
          messages: get().messages.map((m) => (m.id === messageId ? { ...m, ...updates } : m)),
        }),
      removeMessage: (messageId) =>
        set({
          messages: get().messages.filter((m) => m.id !== messageId),
          currentMessageId: get().currentMessageId === messageId ? null : get().currentMessageId,
        }),
      setCurrentMessage: (messageId) => set({ currentMessageId: messageId }),

      // Labels
      labels: [],
      currentLabelId: null,
      setLabels: (labels) => set({ labels }),
      addLabel: (label) => set({ labels: [...get().labels, label] }),
      updateLabel: (labelId, updates) =>
        set({
          labels: get().labels.map((l) => (l.id === labelId ? { ...l, ...updates } : l)),
        }),
      removeLabel: (labelId) =>
        set({
          labels: get().labels.filter((l) => l.id !== labelId),
          currentLabelId: get().currentLabelId === labelId ? null : get().currentLabelId,
        }),
      setCurrentLabel: (labelId) => set({ currentLabelId: labelId }),

      // UI State
      isEmailPanelOpen: false,
      isComposing: false,
      draftRecipients: [],
      draftSubject: '',
      draftBody: '',
      draftIsHtml: false,
      toggleEmailPanel: () => set({ isEmailPanelOpen: !get().isEmailPanelOpen }),
      setIsComposing: (isComposing) => set({ isComposing }),
      setDraftRecipients: (recipients) => set({ draftRecipients: recipients }),
      setDraftSubject: (subject) => set({ draftSubject: subject }),
      setDraftBody: (body) => set({ draftBody: body }),
      setDraftIsHtml: (isHtml) => set({ draftIsHtml: isHtml }),
      clearDraft: () =>
        set({
          draftRecipients: [],
          draftSubject: '',
          draftBody: '',
          draftIsHtml: false,
          isComposing: false,
        }),
      startComposing: (recipients, subject, body) =>
        set({
          draftRecipients: recipients,
          draftSubject: subject,
          draftBody: body,
          draftIsHtml: false,
          isComposing: true,
        }),

      // Auth
      needsReauth: false,
      setNeedsReauth: (needsReauth) => set({ needsReauth }),

      // Filters & Search
      searchQuery: '',
      selectedLabels: [],
      setSearchQuery: (query) => set({ searchQuery: query }),
      setSelectedLabels: (labels) => set({ selectedLabels: labels }),
      toggleLabel: (labelId) => {
        const { selectedLabels } = get();
        if (selectedLabels.includes(labelId)) {
          set({ selectedLabels: selectedLabels.filter((l) => l !== labelId) });
        } else {
          set({ selectedLabels: [...selectedLabels, labelId] });
        }
      },

      // Pagination
      pageToken: null,
      hasMore: false,
      setPageToken: (token) => set({ pageToken: token }),
      setHasMore: (hasMore) => set({ hasMore }),
    }),
    {
      name: 'therese-email-store',
      partialize: (state) => ({
        accounts: state.accounts,
        currentAccountId: state.currentAccountId,
        currentLabelId: state.currentLabelId,
        labels: state.labels,
        messages: state.messages,
      }),
    }
  )
);
