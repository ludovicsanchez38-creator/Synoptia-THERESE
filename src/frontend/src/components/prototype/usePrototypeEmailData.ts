import { useCallback, useEffect, useRef, useState } from 'react';
import {
  createDraft,
  generateEmailResponse,
  getEmailAuthStatus,
  getEmailMessage,
  listEmailMessages,
  type EmailAccount,
  type EmailMessage,
  type SendEmailRequest,
} from '../../services/api/email';
import { useEmailStore } from '../../stores/emailStore';
import { mapEmailList } from './emailReadModels';
import type { ReadResource } from './usePrototypeReadData';

export interface EmailInboxData {
  accounts: EmailAccount[];
  currentAccount: EmailAccount | null;
  messages: EmailMessage[];
  failedMessages: number;
}

export type EmailTone = 'formal' | 'friendly' | 'neutral';
export type EmailLength = 'short' | 'medium' | 'detailed';

export function usePrototypeEmailData(enabled = true) {
  const [inboxResource, setInboxResource] = useState<ReadResource<EmailInboxData>>({
    status: 'loading', data: null, error: null,
  });
  const [messageResource, setMessageResource] = useState<ReadResource<EmailMessage> | null>(null);
  const [selectedMessageId, setSelectedMessageId] = useState<string | null>(null);
  const inboxRequestId = useRef(0);
  const messageRequestId = useRef(0);

  const refreshInbox = useCallback(async () => {
    const requestId = ++inboxRequestId.current;
    setInboxResource({ status: 'loading', data: null, error: null });
    try {
      const status = await getEmailAuthStatus();
      if (requestId !== inboxRequestId.current) return;

      useEmailStore.getState().setAccounts(status.accounts);
      if (status.accounts.length === 0) {
        useEmailStore.getState().setCurrentAccount(null);
        useEmailStore.getState().setMessages([]);
        setInboxResource({
          status: 'ready',
          data: { accounts: [], currentAccount: null, messages: [], failedMessages: 0 },
          error: null,
        });
        return;
      }

      const store = useEmailStore.getState();
      const currentAccount = status.accounts.find((account) => account.id === store.currentAccountId) ?? status.accounts[0];
      store.setCurrentAccount(currentAccount.id);

      const response = await listEmailMessages(currentAccount.id, {
        maxResults: 30,
        labelIds: ['INBOX'],
      });
      if (requestId !== inboxRequestId.current) return;

      const messages = mapEmailList(response.messages, useEmailStore.getState().messages);
      useEmailStore.getState().setMessages(messages);
      setInboxResource({
        status: 'ready',
        data: {
          accounts: status.accounts,
          currentAccount,
          messages,
          failedMessages: response.messages.length - messages.length,
        },
        error: null,
      });
    } catch {
      if (requestId !== inboxRequestId.current) return;
      setInboxResource({
        status: 'error',
        data: null,
        error: 'Impossible de charger les messages pour le moment.',
      });
    }
  }, []);

  const openMessage = useCallback(async (messageId: string) => {
    const currentAccountId = useEmailStore.getState().currentAccountId;
    if (!currentAccountId) {
      setMessageResource({ status: 'error', data: null, error: 'Aucun compte email actif.' });
      return;
    }

    setSelectedMessageId(messageId);
    const requestId = ++messageRequestId.current;
    setMessageResource({ status: 'loading', data: null, error: null });
    try {
      const message = await getEmailMessage(currentAccountId, messageId);
      if (requestId !== messageRequestId.current) return;
      useEmailStore.getState().updateMessage(messageId, message);
      setMessageResource({ status: 'ready', data: message, error: null });
    } catch {
      if (requestId !== messageRequestId.current) return;
      setMessageResource({
        status: 'error',
        data: null,
        error: 'Impossible de charger le contenu complet de ce message.',
      });
    }
  }, []);

  const retryMessage = useCallback(async () => {
    if (selectedMessageId) await openMessage(selectedMessageId);
  }, [openMessage, selectedMessageId]);

  const generateDraft = useCallback(async (
    messageId: string,
    tone: EmailTone,
    length: EmailLength,
  ) => {
    const accountId = useEmailStore.getState().currentAccountId;
    if (!accountId) throw new Error('Aucun compte email actif.');
    const result = await generateEmailResponse(messageId, accountId, tone, length);
    return result.draft;
  }, []);

  const saveDraft = useCallback(async (request: SendEmailRequest) => {
    const accountId = useEmailStore.getState().currentAccountId;
    if (!accountId) throw new Error('Aucun compte email actif.');
    return createDraft(accountId, request);
  }, []);

  useEffect(() => {
    if (!enabled) return undefined;
    void refreshInbox();
    return () => {
      inboxRequestId.current += 1;
      messageRequestId.current += 1;
    };
  }, [enabled, refreshInbox]);

  return {
    inboxResource,
    messageResource,
    selectedMessageId,
    refreshInbox,
    openMessage,
    retryMessage,
    generateDraft,
    saveDraft,
  };
}
