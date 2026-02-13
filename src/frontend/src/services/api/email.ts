/**
 * THÉRÈSE v2 - Email API Module
 *
 * Gestion email Gmail OAuth, messages, labels et fonctionnalités intelligentes.
 */

import { API_BASE, apiFetch } from './core';

export interface EmailAccount {
  id: string;
  email: string;
  provider: string;
  scopes: string[];
  created_at: string;
  last_sync: string | null;
}

export interface EmailMessage {
  id: string;
  thread_id: string;
  subject: string | null;
  from_email: string;
  from_name: string | null;
  to_emails: string[];
  cc_emails?: string[];
  bcc_emails?: string[];
  date: string;
  labels: string[];
  is_read: boolean;
  is_starred: boolean;
  is_draft: boolean;
  has_attachments: boolean;
  snippet: string | null;
  body_plain: string | null;
  body_html: string | null;
  priority?: 'high' | 'medium' | 'low' | null;
  priority_score?: number | null;
  priority_reason?: string | null;
  category?: 'transactional' | 'administrative' | 'business' | 'promotional' | 'newsletter' | null;
}

export interface EmailLabel {
  id: string;
  name: string;
  type: 'system' | 'user';
  messagesTotal: number;
  messagesUnread: number;
}

export interface OAuthFlowData {
  auth_url: string;
  state: string;
  redirect_uri: string;
}

export interface SendEmailRequest {
  to: string[];
  subject: string;
  body: string;
  cc?: string[];
  bcc?: string[];
  html?: boolean;
}

export interface GoogleCredentials {
  client_id: string;
  client_secret: string;
  source: 'mcp' | 'manual';
}

export interface SetupStatus {
  has_gmail: boolean;
  has_smtp: boolean;
  gmail_email: string | null;
  smtp_email: string | null;
  google_credentials: GoogleCredentials | null;
}

export interface ValidationResult {
  valid: boolean;
  field: string;
  message: string;
}

export interface ValidateCredentialsResponse {
  client_id: ValidationResult;
  client_secret: ValidationResult;
  all_valid: boolean;
}

export interface GenerateGuideResponse {
  message: string;
}

// Setup
export async function getEmailSetupStatus(): Promise<SetupStatus> {
  const response = await apiFetch(`${API_BASE}/api/email/setup/status`);
  if (!response.ok) throw new Error('Failed to get setup status');
  return response.json();
}

export async function validateEmailCredentials(
  clientId: string,
  clientSecret: string
): Promise<ValidateCredentialsResponse> {
  const response = await apiFetch(`${API_BASE}/api/email/setup/validate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ client_id: clientId, client_secret: clientSecret }),
  });
  if (!response.ok) throw new Error('Failed to validate credentials');
  return response.json();
}

export async function generateEmailSetupGuide(
  provider: string,
  hasProject: boolean
): Promise<GenerateGuideResponse> {
  const response = await apiFetch(`${API_BASE}/api/email/setup/guide`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ provider, has_project: hasProject }),
  });
  if (!response.ok) throw new Error('Failed to generate guide');
  return response.json();
}

// SMTP/IMAP Setup
export interface SmtpSetupRequest {
  email: string;
  password: string;
  imap_host: string;
  imap_port: number;
  smtp_host: string;
  smtp_port: number;
  smtp_use_tls: boolean;
}

export interface EmailProviderConfig {
  name: string;
  imap_host: string;
  imap_port: number;
  smtp_host: string;
  smtp_port: number;
  smtp_use_tls: boolean;
}

export async function setupSmtpAccount(request: SmtpSetupRequest): Promise<EmailAccount> {
  const response = await apiFetch(`${API_BASE}/api/email/auth/imap-setup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail || 'Échec de la configuration SMTP');
  }
  return response.json();
}

export async function testSmtpConnection(request: SmtpSetupRequest): Promise<{ success: boolean; message: string }> {
  const response = await apiFetch(`${API_BASE}/api/email/auth/test-connection`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail || 'Échec du test de connexion');
  }
  return response.json();
}

export async function getEmailProviders(): Promise<EmailProviderConfig[]> {
  const response = await apiFetch(`${API_BASE}/api/email/providers`);
  if (!response.ok) throw new Error('Failed to get providers');
  return response.json();
}

// OAuth
export async function initiateEmailOAuth(clientId: string, clientSecret: string): Promise<OAuthFlowData> {
  const response = await apiFetch(`${API_BASE}/api/email/auth/initiate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ client_id: clientId, client_secret: clientSecret }),
  });
  if (!response.ok) throw new Error('Failed to initiate OAuth');
  return response.json();
}

export async function reauthorizeEmail(accountId: string): Promise<OAuthFlowData> {
  const response = await apiFetch(`${API_BASE}/api/email/auth/reauthorize/${accountId}`, {
    method: 'POST',
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({ detail: 'Échec de la réautorisation' }));
    throw new Error(data.detail || 'Échec de la réautorisation');
  }
  return response.json();
}

export async function handleEmailOAuthCallback(state: string, code: string): Promise<EmailAccount> {
  const response = await apiFetch(`${API_BASE}/api/email/auth/callback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ state, code }),
  });
  if (!response.ok) throw new Error('Failed to complete OAuth');
  return response.json();
}

export async function getEmailAuthStatus(): Promise<{ connected: boolean; accounts: EmailAccount[] }> {
  const response = await apiFetch(`${API_BASE}/api/email/auth/status`);
  if (!response.ok) throw new Error('Failed to get auth status');
  return response.json();
}

export async function disconnectEmailAccount(accountId: string): Promise<void> {
  const response = await apiFetch(`${API_BASE}/api/email/auth/disconnect/${accountId}`, {
    method: 'DELETE',
  });
  if (!response.ok) throw new Error('Failed to disconnect account');
}

// Messages
export async function listEmailMessages(
  accountId: string,
  params?: {
    maxResults?: number;
    pageToken?: string;
    query?: string;
    labelIds?: string[];
  }
): Promise<{ messages: { id: string; threadId: string }[]; nextPageToken?: string }> {
  const searchParams = new URLSearchParams({ account_id: accountId });
  if (params?.maxResults) searchParams.set('max_results', params.maxResults.toString());
  if (params?.pageToken) searchParams.set('page_token', params.pageToken);
  if (params?.query) searchParams.set('query', params.query);
  if (params?.labelIds) searchParams.set('label_ids', params.labelIds.join(','));

  const response = await apiFetch(`${API_BASE}/api/email/messages?${searchParams}`);
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail || data.message || `Erreur ${response.status}`);
  }
  return response.json();
}

export async function getEmailMessage(accountId: string, messageId: string): Promise<EmailMessage> {
  const response = await apiFetch(`${API_BASE}/api/email/messages/${messageId}?account_id=${accountId}`);
  if (!response.ok) throw new Error('Failed to get message');
  return response.json();
}

export async function sendEmail(accountId: string, req: SendEmailRequest): Promise<any> {
  const response = await apiFetch(`${API_BASE}/api/email/messages?account_id=${accountId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
  if (!response.ok) throw new Error('Failed to send email');
  return response.json();
}

export async function createDraft(accountId: string, req: SendEmailRequest): Promise<any> {
  const response = await apiFetch(`${API_BASE}/api/email/messages/draft?account_id=${accountId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });
  if (!response.ok) throw new Error('Failed to create draft');
  return response.json();
}

export async function modifyEmailMessage(
  accountId: string,
  messageId: string,
  params: {
    addLabelIds?: string[];
    removeLabelIds?: string[];
  }
): Promise<any> {
  const response = await apiFetch(`${API_BASE}/api/email/messages/${messageId}?account_id=${accountId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail || data.message || `Erreur ${response.status}`);
  }
  return response.json();
}

export async function deleteEmailMessage(
  accountId: string,
  messageId: string,
  permanent: boolean = false
): Promise<void> {
  const response = await apiFetch(
    `${API_BASE}/api/email/messages/${messageId}?account_id=${accountId}&permanent=${permanent}`,
    { method: 'DELETE' }
  );
  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new Error(data.detail || data.message || `Erreur ${response.status}`);
  }
}

// Labels
export async function listEmailLabels(accountId: string): Promise<EmailLabel[]> {
  const response = await apiFetch(`${API_BASE}/api/email/labels?account_id=${accountId}`);
  if (!response.ok) throw new Error('Failed to list labels');
  return response.json();
}

export async function createEmailLabel(accountId: string, name: string): Promise<EmailLabel> {
  const response = await apiFetch(`${API_BASE}/api/email/labels?account_id=${accountId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  });
  if (!response.ok) throw new Error('Failed to create label');
  return response.json();
}

export async function updateEmailLabel(accountId: string, labelId: string, name: string): Promise<EmailLabel> {
  const response = await apiFetch(`${API_BASE}/api/email/labels/${labelId}?account_id=${accountId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name }),
  });
  if (!response.ok) throw new Error('Failed to update label');
  return response.json();
}

export async function deleteEmailLabel(accountId: string, labelId: string): Promise<void> {
  const response = await apiFetch(`${API_BASE}/api/email/labels/${labelId}?account_id=${accountId}`, {
    method: 'DELETE',
  });
  if (!response.ok) throw new Error('Failed to delete label');
}

// Smart Email Features
export async function classifyEmail(
  messageId: string,
  accountId: string,
  forceReclassify: boolean = false
): Promise<{
  message_id: string;
  priority: 'high' | 'medium' | 'low';
  category?: 'transactional' | 'administrative' | 'business' | 'promotional' | 'newsletter';
  score: number;
  reason: string;
  signals?: Record<string, any>;
  cached: boolean;
}> {
  const response = await apiFetch(
    `${API_BASE}/api/email/messages/${messageId}/classify?account_id=${accountId}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ force_reclassify: forceReclassify }),
    }
  );
  if (!response.ok) { const d = await response.json().catch(() => ({})); throw new Error(d.detail || d.message || `Erreur ${response.status}`); }
  return response.json();
}

export async function generateEmailResponse(
  messageId: string,
  accountId: string,
  tone: 'formal' | 'friendly' | 'neutral' = 'formal',
  length: 'short' | 'medium' | 'detailed' = 'medium'
): Promise<{
  message_id: string;
  draft: string;
  tone: string;
  length: string;
}> {
  const response = await apiFetch(
    `${API_BASE}/api/email/messages/${messageId}/generate-response?account_id=${accountId}`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tone, length }),
    }
  );
  if (!response.ok) { const d = await response.json().catch(() => ({})); throw new Error(d.detail || d.message || `Erreur ${response.status}`); }
  return response.json();
}

export async function updateEmailPriority(
  messageId: string,
  accountId: string,
  priority: 'high' | 'medium' | 'low'
): Promise<{
  message_id: string;
  priority: string;
  score: number;
  reason: string;
}> {
  const response = await apiFetch(
    `${API_BASE}/api/email/messages/${messageId}/priority?account_id=${accountId}`,
    {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ priority }),
    }
  );
  if (!response.ok) { const d = await response.json().catch(() => ({})); throw new Error(d.detail || d.message || `Erreur ${response.status}`); }
  return response.json();
}

export async function getEmailStats(accountId: string): Promise<{
  high: number;
  medium: number;
  low: number;
  total_unread: number;
  total: number;
}> {
  const response = await apiFetch(`${API_BASE}/api/email/messages/stats?account_id=${accountId}`);
  if (!response.ok) { const d = await response.json().catch(() => ({})); throw new Error(d.detail || d.message || `Erreur ${response.status}`); }
  return response.json();
}
