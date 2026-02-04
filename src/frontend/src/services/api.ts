/**
 * THÉRÈSE v2 - API Service
 *
 * Handles all communication with the Python FastAPI backend.
 */

export const API_BASE = 'http://127.0.0.1:8000';

// Auth token de session (SEC-010)
let _sessionToken: string | null = null;

export async function initializeAuth(): Promise<void> {
  try {
    const response = await fetch(`${API_BASE}/api/auth/token`);
    if (response.ok) {
      const data = await response.json();
      _sessionToken = data.token;
      console.log('Auth token loaded');
    }
  } catch (e) {
    console.warn('Could not load auth token:', e);
  }
}

function apiFetch(url: string, options: RequestInit = {}): Promise<Response> {
  const headers = new Headers(options.headers);
  if (_sessionToken) {
    headers.set('X-Therese-Token', _sessionToken);
  }
  return fetch(url, { ...options, headers });
}

// Types
export interface Contact {
  id: string;
  first_name: string | null;
  last_name: string | null;
  company: string | null;
  email: string | null;
  phone: string | null;
  notes: string | null;
  tags: string | null;
  created_at: string;
  updated_at: string;
  // RGPD fields (Phase 6)
  rgpd_base_legale?: string | null; // consentement, contrat, interet_legitime, obligation_legale
  rgpd_date_collecte?: string | null;
  rgpd_date_expiration?: string | null;
  rgpd_consentement?: boolean;
}

export interface Project {
  id: string;
  name: string;
  description: string | null;
  contact_id: string | null;
  status: string;
  budget: number | null;
  notes: string | null;
  tags: string | null;
  created_at: string;
  updated_at: string;
}

// E3-05: Memory Scope Types
export type MemoryScope = 'global' | 'project' | 'conversation';

export interface ScopeFilter {
  scope?: MemoryScope;
  scope_id?: string;
  include_global?: boolean;
}

// E3-06: Delete Response
export interface DeleteResponse {
  deleted: boolean;
  id: string;
  cascade_deleted: Record<string, number>;
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
  include_memory?: boolean;
  stream?: boolean;
}

export interface ChatResponse {
  id: string;
  conversation_id: string;
  role: 'assistant';
  content: string;
  tokens_in?: number;
  tokens_out?: number;
  model?: string;
  created_at: string;
}

export interface ExtractedContact {
  name: string;
  company: string | null;
  role: string | null;
  email: string | null;
  phone: string | null;
  confidence: number;
}

export interface ExtractedProject {
  name: string;
  description: string | null;
  budget: number | null;
  status: string | null;
  confidence: number;
}

export interface DetectedEntities {
  contacts: ExtractedContact[];
  projects: ExtractedProject[];
}

export interface StreamChunk {
  type: 'text' | 'done' | 'error' | 'status' | 'tool_result' | 'entities_detected';
  content: string;
  conversation_id?: string;
  message_id?: string;
  entities?: DetectedEntities;
  tool_name?: string;  // For tool_result type
  usage?: {
    input_tokens: number;
    output_tokens: number;
    cost_eur: number;
    model: string;
  };
  uncertainty?: {
    is_uncertain: boolean;
    confidence_level: 'high' | 'medium' | 'low';
    confidence_score: number;
    uncertainty_phrases: string[];
  };
}

export interface HealthStatus {
  status: string;
  version: string;
}

export interface Stats {
  entities: {
    contacts: number;
    projects: number;
    conversations: number;
    messages: number;
    files: number;
  };
  uptime_seconds: number;
  data_dir: string;
  db_path: string;
}

// API Error
export class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    message?: string
  ) {
    super(message || `${status} ${statusText}`);
    this.name = 'ApiError';
  }
}

// HTTP helpers
async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const response = await apiFetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });

  if (!response.ok) {
    const message = await response.text().catch(() => null);
    throw new ApiError(response.status, response.statusText, message || undefined);
  }

  return response.json();
}

// Health & Status
export async function checkHealth(): Promise<HealthStatus> {
  return request<HealthStatus>('/health');
}

export async function getStats(): Promise<Stats> {
  return request<Stats>('/api/config/stats');
}

// Chat - Non-streaming
export async function sendMessage(req: ChatRequest): Promise<ChatResponse> {
  return request<ChatResponse>('/api/chat/send', {
    method: 'POST',
    body: JSON.stringify({ ...req, stream: false }),
  });
}

// Chat - Streaming (SSE)
export async function* streamMessage(
  req: ChatRequest
): AsyncGenerator<StreamChunk> {
  const url = `${API_BASE}/api/chat/send`;
  const response = await apiFetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ...req, stream: true }),
  });

  if (!response.ok) {
    const errorText = await response.text().catch(() => null);
    throw new ApiError(response.status, response.statusText, errorText || undefined);
  }

  const reader = response.body?.getReader();
  if (!reader) throw new Error('No response body');

  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6).trim();
          if (!data || data === '[DONE]') continue;
          try {
            const chunk = JSON.parse(data) as StreamChunk;
            yield chunk;
            // Stop on done or error
            if (chunk.type === 'done' || chunk.type === 'error') {
              return;
            }
          } catch {
            // Ignore parse errors for malformed chunks
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

// Conversations
export interface ConversationResponse {
  id: string;
  title: string | null;
  summary: string | null;
  message_count: number;
  created_at: string;
  updated_at: string;
}

export interface MessageResponse {
  id: string;
  conversation_id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  tokens_in: number | null;
  tokens_out: number | null;
  model: string | null;
  created_at: string;
}

export async function listConversations(
  limit = 50,
  offset = 0
): Promise<ConversationResponse[]> {
  return request<ConversationResponse[]>(
    `/api/chat/conversations?limit=${limit}&offset=${offset}`
  );
}

export async function getConversation(id: string): Promise<ConversationResponse> {
  return request<ConversationResponse>(`/api/chat/conversations/${id}`);
}

export async function createConversation(title?: string): Promise<ConversationResponse> {
  return request<ConversationResponse>('/api/chat/conversations', {
    method: 'POST',
    body: JSON.stringify({ title: title || 'Nouvelle conversation' }),
  });
}

export async function getConversationMessages(
  conversationId: string,
  limit = 100
): Promise<MessageResponse[]> {
  return request<MessageResponse[]>(
    `/api/chat/conversations/${conversationId}/messages?limit=${limit}`
  );
}

export async function deleteConversation(id: string): Promise<void> {
  await request<{ deleted: boolean }>(`/api/chat/conversations/${id}`, {
    method: 'DELETE',
  });
}

// Contacts
export async function listContacts(
  offset = 0,
  limit = 50,
  options?: { hasSource?: boolean }
): Promise<Contact[]> {
  const params = new URLSearchParams({
    offset: offset.toString(),
    limit: limit.toString(),
  });
  if (options?.hasSource !== undefined) {
    params.set('has_source', options.hasSource.toString());
  }
  return request<Contact[]>(`/api/memory/contacts?${params.toString()}`);
}

export async function getContact(id: string): Promise<Contact> {
  return request<Contact>(`/api/memory/contacts/${id}`);
}

export async function createContact(
  data: Partial<Contact>
): Promise<Contact> {
  return request<Contact>('/api/memory/contacts', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateContact(
  id: string,
  data: Partial<Contact>
): Promise<Contact> {
  return request<Contact>(`/api/memory/contacts/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function deleteContact(id: string): Promise<void> {
  await request<{ ok: boolean }>(`/api/memory/contacts/${id}`, {
    method: 'DELETE',
  });
}

// E3-05: List contacts with scope filter
export async function listContactsWithScope(
  offset = 0,
  limit = 50,
  scopeFilter?: ScopeFilter
): Promise<Contact[]> {
  const params = new URLSearchParams({
    offset: offset.toString(),
    limit: limit.toString(),
  });

  if (scopeFilter?.scope) {
    params.set('scope', scopeFilter.scope);
  }
  if (scopeFilter?.scope_id) {
    params.set('scope_id', scopeFilter.scope_id);
  }
  if (scopeFilter?.include_global !== undefined) {
    params.set('include_global', scopeFilter.include_global.toString());
  }

  return request<Contact[]>(`/api/memory/contacts?${params.toString()}`);
}

// E3-06: Delete contact with cascade option
export async function deleteContactWithCascade(
  id: string,
  cascade = false
): Promise<DeleteResponse> {
  return request<DeleteResponse>(
    `/api/memory/contacts/${id}?cascade=${cascade}`,
    { method: 'DELETE' }
  );
}

// Projects
export async function listProjects(
  offset = 0,
  limit = 50
): Promise<Project[]> {
  return request<Project[]>(`/api/memory/projects?offset=${offset}&limit=${limit}`);
}

export async function getProject(id: string): Promise<Project> {
  return request<Project>(`/api/memory/projects/${id}`);
}

export async function createProject(
  data: Partial<Project>
): Promise<Project> {
  return request<Project>('/api/memory/projects', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function updateProject(
  id: string,
  data: Partial<Project>
): Promise<Project> {
  return request<Project>(`/api/memory/projects/${id}`, {
    method: 'PUT',
    body: JSON.stringify(data),
  });
}

export async function deleteProject(id: string): Promise<void> {
  await request<{ ok: boolean }>(`/api/memory/projects/${id}`, {
    method: 'DELETE',
  });
}

// E3-05: List projects with scope filter
export async function listProjectsWithScope(
  offset = 0,
  limit = 50,
  scopeFilter?: ScopeFilter
): Promise<Project[]> {
  const params = new URLSearchParams({
    offset: offset.toString(),
    limit: limit.toString(),
  });

  if (scopeFilter?.scope) {
    params.set('scope', scopeFilter.scope);
  }
  if (scopeFilter?.scope_id) {
    params.set('scope_id', scopeFilter.scope_id);
  }
  if (scopeFilter?.include_global !== undefined) {
    params.set('include_global', scopeFilter.include_global.toString());
  }

  return request<Project[]>(`/api/memory/projects?${params.toString()}`);
}

// E3-06: Delete project with cascade option
export async function deleteProjectWithCascade(
  id: string,
  cascade = false
): Promise<DeleteResponse> {
  return request<DeleteResponse>(
    `/api/memory/projects/${id}?cascade=${cascade}`,
    { method: 'DELETE' }
  );
}

// Memory Search
export async function searchMemory(
  query: string,
  types: string[] = ['contacts', 'projects']
): Promise<{ contacts?: Contact[]; projects?: Project[] }> {
  return request('/api/memory/search', {
    method: 'POST',
    body: JSON.stringify({ query, types }),
  });
}

// Configuration
export async function getPreferences(): Promise<Record<string, unknown>> {
  return request('/api/config/preferences');
}

export async function setPreference(
  key: string,
  value: unknown,
  category = 'general'
): Promise<void> {
  await request('/api/config/preferences', {
    method: 'POST',
    body: JSON.stringify({ key, value, category }),
  });
}

export async function getApiKeys(): Promise<Record<string, boolean>> {
  // Get config to check if API keys are set
  const config = await request<{
    has_anthropic_key: boolean;
    has_mistral_key: boolean;
    has_openai_key: boolean;
    has_gemini_key: boolean;
    has_groq_key: boolean;
    has_grok_key: boolean;
    has_openai_image_key: boolean;
    has_gemini_image_key: boolean;
  }>('/api/config/');
  return {
    anthropic: config.has_anthropic_key,
    mistral: config.has_mistral_key,
    openai: config.has_openai_key,
    gemini: config.has_gemini_key,
    groq: config.has_groq_key,
    grok: config.has_grok_key,
    openai_image: config.has_openai_image_key,
    gemini_image: config.has_gemini_image_key,
  };
}

export async function setApiKey(
  provider: string,
  key: string
): Promise<void> {
  await request('/api/config/api-key', {
    method: 'POST',
    body: JSON.stringify({ provider, api_key: key }),
  });
}

// Files
export interface FileMetadata {
  id: string;
  path: string;
  name: string;
  extension: string;
  size: number;
  mime_type: string | null;
  chunk_count: number | null;
  indexed_at: string | null;
  created_at: string;
}

export async function listFiles(
  limit = 50,
  offset = 0
): Promise<FileMetadata[]> {
  return request<FileMetadata[]>(`/api/files/?limit=${limit}&offset=${offset}`);
}

export async function indexFile(path: string): Promise<FileMetadata> {
  return request<FileMetadata>('/api/files/index', {
    method: 'POST',
    body: JSON.stringify({ path }),
  });
}

export async function getFile(id: string): Promise<FileMetadata> {
  return request<FileMetadata>(`/api/files/${id}`);
}

export async function getFileContent(
  id: string
): Promise<{ id: string; path: string; name: string; content: string; truncated: boolean }> {
  return request(`/api/files/${id}/content`);
}

export async function deleteFile(id: string): Promise<void> {
  await request<{ deleted: boolean }>(`/api/files/${id}`, {
    method: 'DELETE',
  });
}

// User Profile
export interface UserProfile {
  name: string;
  nickname: string | null;
  company: string | null;
  role: string | null;
  context: string | null;
  email: string | null;
  location: string | null;
  address: string | null;
  siren: string | null;
  tva_intra: string | null;
  display_name: string;
}

export interface UserProfileUpdate {
  name: string;
  nickname?: string;
  company?: string;
  role?: string;
  context?: string;
  email?: string;
  location?: string;
  address?: string;
  siren?: string;
  tva_intra?: string;
}

export interface WorkingDirectory {
  path: string | null;
  exists: boolean;
}

export async function getProfile(): Promise<UserProfile | null> {
  const response = await apiFetch(`${API_BASE}/api/config/profile`);
  if (response.status === 204 || response.status === 404) {
    return null;
  }
  if (!response.ok) {
    throw new ApiError(response.status, response.statusText);
  }
  const data = await response.json();
  return data || null;
}

export async function setProfile(profile: UserProfileUpdate): Promise<UserProfile> {
  return request<UserProfile>('/api/config/profile', {
    method: 'POST',
    body: JSON.stringify(profile),
  });
}

export async function deleteProfile(): Promise<void> {
  await request<{ deleted: boolean }>('/api/config/profile', {
    method: 'DELETE',
  });
}

export async function importClaudeMd(filePath: string): Promise<UserProfile> {
  return request<UserProfile>('/api/config/profile/import-claude-md', {
    method: 'POST',
    body: JSON.stringify({ file_path: filePath }),
  });
}

export async function getWorkingDirectory(): Promise<WorkingDirectory> {
  return request<WorkingDirectory>('/api/config/working-directory');
}

export async function setWorkingDirectory(path: string): Promise<WorkingDirectory> {
  return request<WorkingDirectory>('/api/config/working-directory', {
    method: 'POST',
    body: JSON.stringify({ path }),
  });
}

// Skills
export interface SkillInfo {
  skill_id: string;
  name: string;
  description: string;
  format: string;
}

export interface SkillExecuteRequest {
  prompt: string;
  title?: string;
  template?: string;
  context?: Record<string, unknown>;
  inputs?: Record<string, any>;  // Inputs structurés pour skills enrichis
}

export interface SkillExecuteResponse {
  success: boolean;
  file_id: string;
  file_name: string;
  file_size: number;
  mime_type: string;
  download_url: string;
  error?: string;
}

export async function listSkills(): Promise<SkillInfo[]> {
  return request<SkillInfo[]>('/api/skills/list');
}

export async function getSkillInfo(skillId: string): Promise<SkillInfo> {
  return request<SkillInfo>(`/api/skills/info/${skillId}`);
}

export async function executeSkill(
  skillId: string,
  req: SkillExecuteRequest
): Promise<SkillExecuteResponse> {
  return request<SkillExecuteResponse>(`/api/skills/execute/${skillId}`, {
    method: 'POST',
    body: JSON.stringify(req),
  });
}

export function getSkillDownloadUrl(fileId: string): string {
  return `${API_BASE}/api/skills/download/${fileId}`;
}

export async function downloadSkillFile(fileId: string, fallbackFilename?: string): Promise<void> {
  // Import Tauri APIs dynamically (for SSR compatibility)
  const { save } = await import('@tauri-apps/plugin-dialog');
  const { writeFile } = await import('@tauri-apps/plugin-fs');

  const url = getSkillDownloadUrl(fileId);

  // Fetch the file
  const response = await apiFetch(url);
  if (!response.ok) {
    throw new ApiError(response.status, response.statusText);
  }

  // Get filename from Content-Disposition header or use fallback
  const disposition = response.headers.get('Content-Disposition');
  let filename = fallbackFilename || 'document.docx';
  if (disposition) {
    const match = disposition.match(/filename="?([^";\n]+)"?/);
    if (match) filename = match[1];
  }

  // Determine file extension for filter
  const ext = filename.split('.').pop() || 'docx';
  const filterName = {
    docx: 'Document Word',
    pptx: 'Présentation PowerPoint',
    xlsx: 'Tableur Excel',
    pdf: 'Document PDF',
  }[ext] || 'Document';

  // Show save dialog
  const savePath = await save({
    defaultPath: filename,
    filters: [{
      name: filterName,
      extensions: [ext],
    }],
  });

  if (!savePath) {
    // User cancelled
    return;
  }

  // Download as blob and convert to Uint8Array
  const blob = await response.blob();
  const arrayBuffer = await blob.arrayBuffer();
  const uint8Array = new Uint8Array(arrayBuffer);

  // Write file using Tauri FS plugin
  await writeFile(savePath, uint8Array);
}

// Skills Enrichis - Schemas et Inputs structurés
export interface InputField {
  type: 'text' | 'textarea' | 'select' | 'number' | 'file';
  label: string;
  placeholder?: string;
  required: boolean;
  options?: string[];
  default?: string | null;
  help_text?: string | null;
}

export interface SkillSchema {
  skill_id: string;
  output_type: 'text' | 'file' | 'analysis';
  schema: Record<string, InputField>;
}

export async function getSkillInputSchema(skillId: string): Promise<SkillSchema> {
  return request<SkillSchema>(`/api/skills/schema/${skillId}`);
}

// LLM Configuration
export type LLMProvider = 'anthropic' | 'openai' | 'gemini' | 'mistral' | 'grok' | 'ollama';

export interface LLMConfig {
  provider: LLMProvider;
  model: string;
  available_models: string[];
}

export interface OllamaModel {
  name: string;
  size: number | null;
  modified_at: string | null;
  digest: string | null;
}

export interface OllamaStatus {
  available: boolean;
  base_url: string;
  models: OllamaModel[];
  error: string | null;
}

export async function getLLMConfig(): Promise<LLMConfig> {
  return request<LLMConfig>('/api/config/llm');
}

export async function setLLMConfig(
  provider: LLMProvider,
  model: string
): Promise<LLMConfig> {
  return request<LLMConfig>('/api/config/llm', {
    method: 'POST',
    body: JSON.stringify({ provider, model }),
  });
}

export async function getOllamaStatus(): Promise<OllamaStatus> {
  return request<OllamaStatus>('/api/config/ollama/status');
}

// Onboarding
export interface OnboardingStatus {
  completed: boolean;
  completed_at: string | null;
}

export async function getOnboardingStatus(): Promise<OnboardingStatus> {
  return request<OnboardingStatus>('/api/config/onboarding-complete');
}

export async function completeOnboarding(): Promise<OnboardingStatus> {
  return request<OnboardingStatus>('/api/config/onboarding-complete', {
    method: 'POST',
  });
}

// Voice Transcription (Groq Whisper)
export interface TranscriptionResponse {
  text: string;
  duration_seconds?: number;
  language?: string;
}

export async function transcribeAudio(audioBlob: Blob): Promise<string> {
  const formData = new FormData();
  formData.append('audio', audioBlob, 'recording.webm');

  const response = await apiFetch(`${API_BASE}/api/voice/transcribe`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const message = await response.text().catch(() => null);
    throw new ApiError(response.status, response.statusText, message || undefined);
  }

  const data = await response.json() as TranscriptionResponse;
  return data.text;
}

export async function hasGroqKey(): Promise<boolean> {
  const config = await request<{ has_groq_key: boolean }>('/api/config/');
  return config.has_groq_key;
}

// Web Search
export interface WebSearchStatus {
  enabled: boolean;
  providers: {
    gemini: string;
    others: string;
  };
  description: string;
}

export async function getWebSearchStatus(): Promise<WebSearchStatus> {
  return request<WebSearchStatus>('/api/config/web-search');
}

export async function setWebSearchEnabled(enabled: boolean): Promise<{ success: boolean; enabled: boolean }> {
  return request<{ success: boolean; enabled: boolean }>(`/api/config/web-search?enabled=${enabled}`, {
    method: 'POST',
  });
}

// Image Generation
export type ImageProvider = 'gpt-image-1.5' | 'nanobanan-pro';

export interface ImageGenerateRequest {
  prompt: string;
  provider?: ImageProvider;
  // OpenAI options
  size?: '1024x1024' | '1536x1024' | '1024x1536';
  quality?: 'low' | 'medium' | 'high';
  // Gemini options
  aspect_ratio?: string;
  image_size?: '1K' | '2K' | '4K';
}

export interface ImageResponse {
  id: string;
  provider: string;
  file_name: string;
  file_size: number;
  mime_type: string;
  created_at: string;
  prompt: string;
  download_url: string;
}

export interface ImageProviderStatus {
  openai_available: boolean;
  gemini_available: boolean;
  active_provider: string | null;
}

export async function getImageStatus(): Promise<ImageProviderStatus> {
  return request<ImageProviderStatus>('/api/images/status');
}

export async function generateImage(req: ImageGenerateRequest): Promise<ImageResponse> {
  return request<ImageResponse>('/api/images/generate', {
    method: 'POST',
    body: JSON.stringify(req),
  });
}

export function getImageDownloadUrl(imageId: string): string {
  // SEC-010: Inclure le token dans l'URL pour les balises <img> qui ne supportent pas les headers
  const tokenParam = _sessionToken ? `?token=${encodeURIComponent(_sessionToken)}` : '';
  return `${API_BASE}/api/images/download/${imageId}${tokenParam}`;
}

export async function downloadGeneratedImage(imageId: string): Promise<void> {
  const { save } = await import('@tauri-apps/plugin-dialog');
  const { writeFile } = await import('@tauri-apps/plugin-fs');

  const url = getImageDownloadUrl(imageId);

  const response = await apiFetch(url);
  if (!response.ok) {
    throw new ApiError(response.status, response.statusText);
  }

  const disposition = response.headers.get('Content-Disposition');
  let filename = 'image.png';
  if (disposition) {
    const match = disposition.match(/filename="?([^";\n]+)"?/);
    if (match) filename = match[1];
  }

  const savePath = await save({
    defaultPath: filename,
    filters: [{ name: 'Image', extensions: ['png', 'jpg', 'jpeg'] }],
  });

  if (!savePath) return;

  const blob = await response.blob();
  const arrayBuffer = await blob.arrayBuffer();
  const uint8Array = new Uint8Array(arrayBuffer);

  await writeFile(savePath, uint8Array);
}

export async function listGeneratedImages(limit = 50): Promise<{ images: ImageResponse[]; total: number }> {
  return request<{ images: ImageResponse[]; total: number }>(`/api/images/list?limit=${limit}`);
}

// Board de Décision Stratégique
export type AdvisorRole = 'analyst' | 'strategist' | 'devil' | 'pragmatic' | 'visionary';

export interface AdvisorInfo {
  role: AdvisorRole;
  name: string;
  emoji: string;
  color: string;
  personality: string;
}

export interface BoardRequest {
  question: string;
  context?: string;
  advisors?: AdvisorRole[];
}

export interface BoardDeliberationChunk {
  type: 'web_search_start' | 'web_search_done' | 'advisor_start' | 'advisor_chunk' | 'advisor_done' | 'synthesis_start' | 'synthesis_chunk' | 'done' | 'error';
  role?: AdvisorRole;
  name?: string;
  emoji?: string;
  provider?: string;  // LLM provider used (anthropic, openai, gemini, mistral, ollama)
  content: string;
}

export interface BoardSynthesis {
  consensus_points: string[];
  divergence_points: string[];
  recommendation: string;
  confidence: 'high' | 'medium' | 'low';
  next_steps: string[];
}

export interface BoardDecisionResponse {
  id: string;
  question: string;
  context?: string;
  recommendation: string;
  confidence: string;
  created_at: string;
}

export async function listAdvisors(): Promise<AdvisorInfo[]> {
  return request<AdvisorInfo[]>('/api/board/advisors');
}

export async function getAdvisor(role: AdvisorRole): Promise<AdvisorInfo> {
  return request<AdvisorInfo>(`/api/board/advisors/${role}`);
}

export async function* streamDeliberation(
  req: BoardRequest
): AsyncGenerator<BoardDeliberationChunk> {
  const url = `${API_BASE}/api/board/deliberate`;
  const response = await apiFetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  });

  if (!response.ok) {
    const errorText = await response.text().catch(() => null);
    throw new ApiError(response.status, response.statusText, errorText || undefined);
  }

  const reader = response.body?.getReader();
  if (!reader) throw new Error('No response body');

  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const data = line.slice(6).trim();
          if (!data || data === '[DONE]') continue;
          try {
            const chunk = JSON.parse(data) as BoardDeliberationChunk;
            yield chunk;
            if (chunk.type === 'done' || chunk.type === 'error') {
              return;
            }
          } catch {
            // Ignore parse errors
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

export async function listBoardDecisions(limit = 50): Promise<BoardDecisionResponse[]> {
  return request<BoardDecisionResponse[]>(`/api/board/decisions?limit=${limit}`);
}

export async function getBoardDecision(id: string): Promise<{
  id: string;
  question: string;
  context?: string;
  opinions: Array<{
    role: AdvisorRole;
    name: string;
    emoji: string;
    content: string;
  }>;
  synthesis: BoardSynthesis;
  created_at: string;
}> {
  return request(`/api/board/decisions/${id}`);
}

export async function deleteBoardDecision(id: string): Promise<void> {
  await request<{ deleted: boolean }>(`/api/board/decisions/${id}`, {
    method: 'DELETE',
  });
}

// ==================== Calculators API ====================

export interface ROIResult {
  investment: number;
  gain: number;
  roi_percent: number;
  profit: number;
  interpretation: string;
}

export interface ICEResult {
  impact: number;
  confidence: number;
  ease: number;
  score: number;
  interpretation: string;
}

export interface RICEResult {
  reach: number;
  impact: number;
  confidence: number;
  effort: number;
  score: number;
  interpretation: string;
}

export interface NPVResult {
  initial_investment: number;
  cash_flows: number[];
  discount_rate: number;
  npv: number;
  interpretation: string;
}

export interface BreakEvenResult {
  fixed_costs: number;
  variable_cost_per_unit: number;
  price_per_unit: number;
  break_even_units: number;
  break_even_revenue: number;
  interpretation: string;
}

export async function calculateROI(
  investment: number,
  gain: number
): Promise<ROIResult> {
  return request('/api/calc/roi', {
    method: 'POST',
    body: JSON.stringify({ investment, gain }),
  });
}

export async function calculateICE(
  impact: number,
  confidence: number,
  ease: number
): Promise<ICEResult> {
  return request('/api/calc/ice', {
    method: 'POST',
    body: JSON.stringify({ impact, confidence, ease }),
  });
}

export async function calculateRICE(
  reach: number,
  impact: number,
  confidence: number,
  effort: number
): Promise<RICEResult> {
  return request('/api/calc/rice', {
    method: 'POST',
    body: JSON.stringify({ reach, impact, confidence, effort }),
  });
}

export async function calculateNPV(
  initial_investment: number,
  cash_flows: number[],
  discount_rate: number
): Promise<NPVResult> {
  return request('/api/calc/npv', {
    method: 'POST',
    body: JSON.stringify({ initial_investment, cash_flows, discount_rate }),
  });
}

export async function calculateBreakEven(
  fixed_costs: number,
  variable_cost_per_unit: number,
  price_per_unit: number
): Promise<BreakEvenResult> {
  return request('/api/calc/break-even', {
    method: 'POST',
    body: JSON.stringify({ fixed_costs, variable_cost_per_unit, price_per_unit }),
  });
}

export interface CalculatorInfo {
  name: string;
  endpoint: string;
  description: string;
  formula: string;
  params: string[];
}

export async function getCalculatorsHelp(): Promise<{ calculators: CalculatorInfo[] }> {
  return request('/api/calc/help');
}

// ==================== MCP (Model Context Protocol) API ====================

export type MCPServerStatus = 'stopped' | 'starting' | 'running' | 'error';

export interface MCPTool {
  name: string;
  description: string;
  input_schema: Record<string, unknown>;
  server_id: string;
  server_name?: string;
}

export interface MCPServer {
  id: string;
  name: string;
  command: string;
  args: string[];
  env: Record<string, string>;
  enabled: boolean;
  status: MCPServerStatus;
  tools: MCPTool[];
  error: string | null;
  created_at: string;
}

export interface MCPServerCreate {
  name: string;
  command: string;
  args?: string[];
  env?: Record<string, string>;
  enabled?: boolean;
}

export interface MCPPreset {
  id: string;
  name: string;
  description: string;
  category?: string;
  popular?: boolean;
  url?: string;
  command: string;
  args: string[];
  env_required?: string[];
  installed: boolean;
}

export interface MCPStatus {
  total_servers: number;
  running_servers: number;
  total_tools: number;
  servers: Record<string, {
    name: string;
    status: MCPServerStatus;
    tools_count: number;
  }>;
}

export interface ToolCallResult {
  tool_name: string;
  server_id: string;
  success: boolean;
  result: unknown;
  error: string | null;
  execution_time_ms: number;
}

// MCP Servers
export async function listMCPServers(): Promise<MCPServer[]> {
  return request<MCPServer[]>('/api/mcp/servers');
}

export async function createMCPServer(server: MCPServerCreate): Promise<MCPServer> {
  return request<MCPServer>('/api/mcp/servers', {
    method: 'POST',
    body: JSON.stringify(server),
  });
}

export async function getMCPServer(serverId: string): Promise<MCPServer> {
  return request<MCPServer>(`/api/mcp/servers/${serverId}`);
}

export async function updateMCPServer(
  serverId: string,
  updates: Partial<MCPServerCreate>
): Promise<MCPServer> {
  return request<MCPServer>(`/api/mcp/servers/${serverId}`, {
    method: 'PUT',
    body: JSON.stringify(updates),
  });
}

export async function deleteMCPServer(serverId: string): Promise<void> {
  await request<{ deleted: boolean }>(`/api/mcp/servers/${serverId}`, {
    method: 'DELETE',
  });
}

export async function startMCPServer(serverId: string): Promise<MCPServer> {
  return request<MCPServer>(`/api/mcp/servers/${serverId}/start`, {
    method: 'POST',
  });
}

export async function stopMCPServer(serverId: string): Promise<MCPServer> {
  return request<MCPServer>(`/api/mcp/servers/${serverId}/stop`, {
    method: 'POST',
  });
}

export async function restartMCPServer(serverId: string): Promise<MCPServer> {
  return request<MCPServer>(`/api/mcp/servers/${serverId}/restart`, {
    method: 'POST',
  });
}

// MCP Tools
export async function listMCPTools(): Promise<MCPTool[]> {
  return request<MCPTool[]>('/api/mcp/tools');
}

export async function callMCPTool(
  toolName: string,
  args: Record<string, unknown> = {}
): Promise<ToolCallResult> {
  return request<ToolCallResult>('/api/mcp/tools/call', {
    method: 'POST',
    body: JSON.stringify({ tool_name: toolName, arguments: args }),
  });
}

// MCP Status
export async function getMCPStatus(): Promise<MCPStatus> {
  return request<MCPStatus>('/api/mcp/status');
}

// MCP Presets
export async function listMCPPresets(): Promise<MCPPreset[]> {
  return request<MCPPreset[]>('/api/mcp/presets');
}

export async function installMCPPreset(
  presetId: string,
  env?: Record<string, string>
): Promise<MCPServer> {
  return request<MCPServer>(`/api/mcp/presets/${presetId}/install`, {
    method: 'POST',
    body: JSON.stringify(env || {}),
  });
}

// ==================== Performance API (US-PERF-01 to US-PERF-05) ====================

export interface PerformanceMetrics {
  total_requests: number;
  total_tokens: number;
  active_streams: number;
  avg_first_token_ms: number;
  p95_first_token_ms: number;
  recent_metrics_count: number;
  meets_sla: boolean;
}

export interface StreamingMetric {
  conversation_id: string;
  first_token_ms: number | null;
  total_time_ms: number;
  total_tokens: number;
  tokens_per_second: number;
  provider: string;
  model: string;
}

export interface MemoryStats {
  uptime_hours: number;
  gc_stats: unknown[];
  last_cleanup_ago_minutes: number;
  registered_cleanups: number;
}

export interface PowerSettings {
  health_check_interval: number;
  conversation_sync_interval: number;
  battery_saver_mode: boolean;
  reduce_animations: boolean;
}

export interface SearchResult {
  id: string;
  title: string;
  score: number;
}

export interface PerformanceStatus {
  streaming: PerformanceMetrics;
  memory: MemoryStats;
  search_index: {
    indexed_conversations: number;
    unique_words: number;
    total_entries: number;
  };
  power: PowerSettings;
  conversations_total: number;
}

// Get performance metrics (US-PERF-01)
export async function getPerformanceMetrics(): Promise<PerformanceMetrics> {
  return request<PerformanceMetrics>('/api/perf/metrics');
}

// Get recent streaming metrics
export async function getRecentMetrics(limit = 20): Promise<{
  metrics: StreamingMetric[];
  count: number;
}> {
  return request(`/api/perf/metrics/recent?limit=${limit}`);
}

// Get conversation count (US-PERF-02)
export async function getConversationsCount(): Promise<{ total: number }> {
  return request<{ total: number }>('/api/perf/conversations/count');
}

// Search conversations (US-PERF-04)
export async function searchConversations(
  query: string,
  limit = 50
): Promise<{
  results: SearchResult[];
  source: string;
  total: number;
}> {
  return request(`/api/perf/conversations/search?q=${encodeURIComponent(query)}&limit=${limit}`);
}

// Reindex conversations (US-PERF-04)
export async function reindexConversations(): Promise<{
  indexed: number;
  stats: {
    indexed_conversations: number;
    unique_words: number;
    total_entries: number;
  };
}> {
  return request('/api/perf/conversations/reindex', { method: 'POST' });
}

// Get memory stats (US-PERF-03)
export async function getMemoryStats(): Promise<MemoryStats> {
  return request<MemoryStats>('/api/perf/memory');
}

// Trigger memory cleanup (US-PERF-03)
export async function triggerMemoryCleanup(): Promise<{
  success: boolean;
  results: Record<string, unknown>;
  stats: MemoryStats;
}> {
  return request('/api/perf/memory/cleanup', { method: 'POST' });
}

// Get power settings (US-PERF-05)
export async function getPowerSettings(): Promise<PowerSettings> {
  return request<PowerSettings>('/api/perf/power');
}

// Update power settings (US-PERF-05)
export async function updatePowerSettings(
  settings: Partial<PowerSettings>
): Promise<PowerSettings> {
  const params = new URLSearchParams();
  if (settings.health_check_interval !== undefined) {
    params.append('health_check_interval', settings.health_check_interval.toString());
  }
  if (settings.conversation_sync_interval !== undefined) {
    params.append('conversation_sync_interval', settings.conversation_sync_interval.toString());
  }
  if (settings.battery_saver_mode !== undefined) {
    params.append('battery_saver_mode', settings.battery_saver_mode.toString());
  }
  if (settings.reduce_animations !== undefined) {
    params.append('reduce_animations', settings.reduce_animations.toString());
  }
  return request<PowerSettings>(`/api/perf/power?${params.toString()}`, {
    method: 'POST',
  });
}

// Enable/disable battery saver (US-PERF-05)
export async function setBatterySaver(enabled: boolean): Promise<{
  battery_saver_enabled: boolean;
  settings: PowerSettings;
}> {
  return request(`/api/perf/power/battery-saver?enabled=${enabled}`, {
    method: 'POST',
  });
}

// Get combined performance status
export async function getPerformanceStatus(): Promise<PerformanceStatus> {
  return request<PerformanceStatus>('/api/perf/status');
}

// ==================== Personalisation API (US-PERS-01 to US-PERS-05) ====================

// US-PERS-02: Prompt Templates
export interface PromptTemplate {
  id: string;
  name: string;
  prompt: string;
  category: string;
  icon: string | null;
  created_at: string;
  updated_at: string;
}

export interface PromptTemplateCreate {
  name: string;
  prompt: string;
  category?: string;
  icon?: string;
}

export async function listPromptTemplates(category?: string): Promise<PromptTemplate[]> {
  const url = category
    ? `/api/personalisation/templates?category=${encodeURIComponent(category)}`
    : '/api/personalisation/templates';
  return request<PromptTemplate[]>(url);
}

export async function createPromptTemplate(template: PromptTemplateCreate): Promise<PromptTemplate> {
  return request<PromptTemplate>('/api/personalisation/templates', {
    method: 'POST',
    body: JSON.stringify(template),
  });
}

export async function getPromptTemplate(id: string): Promise<PromptTemplate> {
  return request<PromptTemplate>(`/api/personalisation/templates/${id}`);
}

export async function updatePromptTemplate(
  id: string,
  updates: Partial<PromptTemplateCreate>
): Promise<PromptTemplate> {
  return request<PromptTemplate>(`/api/personalisation/templates/${id}`, {
    method: 'PUT',
    body: JSON.stringify(updates),
  });
}

export async function deletePromptTemplate(id: string): Promise<void> {
  await request<{ deleted: boolean }>(`/api/personalisation/templates/${id}`, {
    method: 'DELETE',
  });
}

// US-PERS-04: LLM Behavior Settings
export interface LLMBehaviorSettings {
  custom_system_prompt: string;
  use_custom_system_prompt: boolean;
  response_style: 'concise' | 'detailed' | 'creative';
  language: 'french' | 'english' | 'auto';
  include_memory_context: boolean;
  max_history_messages: number;
}

export async function getLLMBehavior(): Promise<LLMBehaviorSettings> {
  return request<LLMBehaviorSettings>('/api/personalisation/llm-behavior');
}

export async function setLLMBehavior(settings: LLMBehaviorSettings): Promise<LLMBehaviorSettings> {
  return request<LLMBehaviorSettings>('/api/personalisation/llm-behavior', {
    method: 'POST',
    body: JSON.stringify(settings),
  });
}

// US-PERS-05: Feature Visibility Settings
export interface FeatureVisibilitySettings {
  show_board: boolean;
  show_calculators: boolean;
  show_image_generation: boolean;
  show_voice_input: boolean;
  show_file_browser: boolean;
  show_mcp_tools: boolean;
  show_guided_prompts: boolean;
  show_entity_suggestions: boolean;
}

export async function getFeatureVisibility(): Promise<FeatureVisibilitySettings> {
  return request<FeatureVisibilitySettings>('/api/personalisation/features');
}

export async function setFeatureVisibility(
  settings: FeatureVisibilitySettings
): Promise<FeatureVisibilitySettings> {
  return request<FeatureVisibilitySettings>('/api/personalisation/features', {
    method: 'POST',
    body: JSON.stringify(settings),
  });
}

// Combined personalisation status
export interface PersonalisationStatus {
  templates_count: number;
  templates_by_category: Record<string, number>;
  llm_behavior: LLMBehaviorSettings;
  feature_visibility: FeatureVisibilitySettings;
}

export async function getPersonalisationStatus(): Promise<PersonalisationStatus> {
  return request<PersonalisationStatus>('/api/personalisation/status');
}

// ==================== Escalation & Limites API (US-ESC-01 to US-ESC-05) ====================

// US-ESC-02: Cost Estimation
export interface CostEstimate {
  model: string;
  input_tokens: number;
  output_tokens: number;
  estimated_cost_eur: number;
}

export async function estimateCost(
  model: string,
  inputTokens: number,
  outputTokens: number
): Promise<CostEstimate> {
  return request<CostEstimate>('/api/escalation/estimate-cost', {
    method: 'POST',
    body: JSON.stringify({
      model,
      input_tokens: inputTokens,
      output_tokens: outputTokens,
    }),
  });
}

export interface TokenPrice {
  input_per_1m: number;
  output_per_1m: number;
  input_per_1k: number;
  output_per_1k: number;
}

export async function getTokenPrices(): Promise<{
  prices: Record<string, TokenPrice>;
  currency: string;
}> {
  return request('/api/escalation/prices');
}

// US-ESC-03: Token Limits
export interface TokenLimits {
  max_input_tokens: number;
  max_output_tokens: number;
  daily_input_limit: number;
  daily_output_limit: number;
  monthly_budget_eur: number;
  warn_at_percentage: number;
}

export async function getTokenLimits(): Promise<TokenLimits> {
  return request<TokenLimits>('/api/escalation/limits');
}

export async function setTokenLimits(limits: TokenLimits): Promise<TokenLimits> {
  return request<TokenLimits>('/api/escalation/limits', {
    method: 'POST',
    body: JSON.stringify(limits),
  });
}

export interface LimitCheckResult {
  allowed: boolean;
  warnings: string[];
  errors: string[];
}

export async function checkTokenLimits(
  inputTokens: number,
  outputTokens?: number
): Promise<LimitCheckResult> {
  const params = new URLSearchParams({ input_tokens: inputTokens.toString() });
  if (outputTokens !== undefined) {
    params.append('output_tokens', outputTokens.toString());
  }
  return request<LimitCheckResult>(`/api/escalation/check-limits?${params.toString()}`, {
    method: 'POST',
  });
}

// US-ESC-04: Usage History
export interface DailyUsage {
  date: string;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  cost_eur: number;
  input_limit: number;
  output_limit: number;
  input_usage_pct: number;
  output_usage_pct: number;
}

export interface MonthlyUsage {
  month: string;
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  cost_eur: number;
  budget_eur: number;
  budget_usage_pct: number;
}

export interface UsageRecord {
  timestamp: string;
  conversation_id: string;
  model: string;
  provider: string;
  input_tokens: number;
  output_tokens: number;
  cost_eur: number;
  context_truncated: boolean;
  truncated_messages: number;
}

export async function getDailyUsage(): Promise<DailyUsage> {
  return request<DailyUsage>('/api/escalation/usage/daily');
}

export async function getMonthlyUsage(): Promise<MonthlyUsage> {
  return request<MonthlyUsage>('/api/escalation/usage/monthly');
}

export async function getUsageHistory(
  limit = 50,
  conversationId?: string
): Promise<{ history: UsageRecord[]; count: number }> {
  const params = new URLSearchParams({ limit: limit.toString() });
  if (conversationId) {
    params.append('conversation_id', conversationId);
  }
  return request(`/api/escalation/usage/history?${params.toString()}`);
}

export interface UsageStats {
  daily: DailyUsage;
  monthly: MonthlyUsage;
  limits: TokenLimits;
  history_count: number;
}

export async function getUsageStats(): Promise<UsageStats> {
  return request<UsageStats>('/api/escalation/usage/stats');
}

// US-ESC-01: Uncertainty Detection
export interface UncertaintyResult {
  is_uncertain: boolean;
  uncertainty_phrases: string[];
  confidence_score: number;
  confidence_level: 'high' | 'medium' | 'low';
  should_verify: boolean;
}

export async function checkUncertainty(response: string): Promise<UncertaintyResult> {
  return request<UncertaintyResult>('/api/escalation/check-uncertainty', {
    method: 'POST',
    body: JSON.stringify({ response }),
  });
}

// US-ESC-05: Context Info
export interface ContextInfo {
  context_limits: Record<string, number>;
  truncation_policy: {
    strategy: string;
    description: string;
    keep_system_prompt: boolean;
    keep_last_n_messages: number;
    warning_threshold_pct: number;
  };
  recommendation: string;
}

export async function getContextInfo(): Promise<ContextInfo> {
  return request<ContextInfo>('/api/escalation/context-info');
}

// Combined escalation status
export interface EscalationStatus {
  daily_usage: DailyUsage;
  monthly_usage: MonthlyUsage;
  limits: TokenLimits;
  recent_history_count: number;
}

export async function getEscalationStatus(): Promise<EscalationStatus> {
  return request<EscalationStatus>('/api/escalation/status');
}


// ============================================================
// Email API (Phase 1 Frontend)
// ============================================================

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
  // Smart Email Features (US-EMAIL-08, US-EMAIL-10)
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

// Email Setup Wizard (Phase 1.2)
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

export async function sendEmail(accountId: string, request: SendEmailRequest): Promise<any> {
  const response = await apiFetch(`${API_BASE}/api/email/messages?account_id=${accountId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  if (!response.ok) throw new Error('Failed to send email');
  return response.json();
}

export async function createDraft(accountId: string, request: SendEmailRequest): Promise<any> {
  const response = await apiFetch(`${API_BASE}/api/email/messages/draft?account_id=${accountId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
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


// =============================================================================
// CALENDAR API (Phase 2)
// =============================================================================

export interface Calendar {
  id: string;
  account_id: string;
  summary: string;
  description: string | null;
  timezone: string;
  primary: boolean;
  synced_at: string;
}

export interface CalendarEvent {
  id: string;
  calendar_id: string;
  summary: string;
  description: string | null;
  location: string | null;
  start_datetime: string | null; // ISO datetime
  end_datetime: string | null;
  start_date: string | null; // YYYY-MM-DD
  end_date: string | null;
  all_day: boolean;
  attendees: string[] | null;
  recurrence: string[] | null; // RRULE
  status: string; // confirmed, tentative, cancelled
  synced_at: string;
}

export interface CreateEventRequest {
  calendar_id?: string;
  summary: string;
  description?: string;
  location?: string;
  start_datetime?: string;
  end_datetime?: string;
  start_date?: string;
  end_date?: string;
  attendees?: string[];
  recurrence?: string[];
}

export interface UpdateEventRequest {
  summary?: string;
  description?: string;
  location?: string;
  start_datetime?: string;
  end_datetime?: string;
  start_date?: string;
  end_date?: string;
  attendees?: string[];
  recurrence?: string[];
}

export interface CalendarSyncResponse {
  calendars_synced: number;
  events_synced: number;
  synced_at: string;
}

// Calendars

export async function listCalendars(accountId: string): Promise<Calendar[]> {
  const response = await apiFetch(`${API_BASE}/api/calendar/calendars?account_id=${accountId}`);
  if (!response.ok) throw new Error(`Failed to list calendars: ${response.statusText}`);
  return response.json();
}

export async function getCalendar(calendarId: string, accountId: string): Promise<Calendar> {
  const response = await apiFetch(`${API_BASE}/api/calendar/calendars/${calendarId}?account_id=${accountId}`);
  if (!response.ok) throw new Error(`Failed to get calendar: ${response.statusText}`);
  return response.json();
}

export async function createCalendar(
  accountId: string,
  summary: string,
  description?: string,
  timezone: string = 'Europe/Paris'
): Promise<Calendar> {
  const response = await apiFetch(`${API_BASE}/api/calendar/calendars`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ account_id: accountId, summary, description, timezone }),
  });
  if (!response.ok) throw new Error(`Failed to create calendar: ${response.statusText}`);
  return response.json();
}

export async function deleteCalendar(calendarId: string, accountId: string): Promise<any> {
  const response = await apiFetch(`${API_BASE}/api/calendar/calendars/${calendarId}?account_id=${accountId}`, {
    method: 'DELETE',
  });
  if (!response.ok) throw new Error(`Failed to delete calendar: ${response.statusText}`);
  return response.json();
}

// Events

export async function listEvents(
  accountId: string,
  calendarId: string = 'primary',
  params?: {
    time_min?: string;
    time_max?: string;
    max_results?: number;
  }
): Promise<CalendarEvent[]> {
  const queryParams = new URLSearchParams({
    account_id: accountId,
    calendar_id: calendarId,
    ...(params?.time_min && { time_min: params.time_min }),
    ...(params?.time_max && { time_max: params.time_max }),
    ...(params?.max_results && { max_results: params.max_results.toString() }),
  });

  const response = await apiFetch(`${API_BASE}/api/calendar/events?${queryParams}`);
  if (!response.ok) throw new Error(`Failed to list events: ${response.statusText}`);
  return response.json();
}

export async function getEvent(eventId: string, calendarId: string, accountId: string): Promise<CalendarEvent> {
  const response = await apiFetch(`${API_BASE}/api/calendar/events/${eventId}?calendar_id=${calendarId}&account_id=${accountId}`);
  if (!response.ok) throw new Error(`Failed to get event: ${response.statusText}`);
  return response.json();
}

export async function createEvent(request: CreateEventRequest, accountId: string): Promise<CalendarEvent> {
  const response = await apiFetch(`${API_BASE}/api/calendar/events?account_id=${accountId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  if (!response.ok) throw new Error(`Failed to create event: ${response.statusText}`);
  return response.json();
}

export async function updateEvent(
  eventId: string,
  request: UpdateEventRequest,
  calendarId: string,
  accountId: string
): Promise<CalendarEvent> {
  const response = await apiFetch(`${API_BASE}/api/calendar/events/${eventId}?calendar_id=${calendarId}&account_id=${accountId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  if (!response.ok) throw new Error(`Failed to update event: ${response.statusText}`);
  return response.json();
}

export async function deleteEvent(eventId: string, calendarId: string, accountId: string): Promise<any> {
  const response = await apiFetch(`${API_BASE}/api/calendar/events/${eventId}?calendar_id=${calendarId}&account_id=${accountId}`, {
    method: 'DELETE',
  });
  if (!response.ok) throw new Error(`Failed to delete event: ${response.statusText}`);
  return response.json();
}

export async function quickAddEvent(text: string, calendarId: string, accountId: string): Promise<CalendarEvent> {
  const response = await apiFetch(`${API_BASE}/api/calendar/events/quick-add?account_id=${accountId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ calendar_id: calendarId, text }),
  });
  if (!response.ok) throw new Error(`Failed to quick add event: ${response.statusText}`);
  return response.json();
}

// Sync

export async function syncCalendar(accountId: string): Promise<CalendarSyncResponse> {
  const response = await apiFetch(`${API_BASE}/api/calendar/sync?account_id=${accountId}`, {
    method: 'POST',
  });
  if (!response.ok) throw new Error(`Failed to sync calendar: ${response.statusText}`);
  return response.json();
}

export async function getCalendarSyncStatus(accountId: string): Promise<any> {
  const response = await apiFetch(`${API_BASE}/api/calendar/sync/status?account_id=${accountId}`);
  if (!response.ok) throw new Error(`Failed to get sync status: ${response.statusText}`);
  return response.json();
}


// =============================================================================
// TASKS API (Phase 3)
// =============================================================================

export interface Task {
  id: string;
  title: string;
  description: string | null;
  status: 'todo' | 'in_progress' | 'done' | 'cancelled';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  due_date: string | null; // ISO datetime
  project_id: string | null;
  tags: string[] | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface CreateTaskRequest {
  title: string;
  description?: string;
  status?: string;
  priority?: string;
  due_date?: string;
  project_id?: string;
  tags?: string[];
}

export interface UpdateTaskRequest {
  title?: string;
  description?: string;
  status?: string;
  priority?: string;
  due_date?: string;
  project_id?: string;
  tags?: string[];
}

export async function listTasks(params?: {
  status?: string;
  priority?: string;
  project_id?: string;
}): Promise<Task[]> {
  const queryParams = new URLSearchParams();
  if (params?.status) queryParams.set('status', params.status);
  if (params?.priority) queryParams.set('priority', params.priority);
  if (params?.project_id) queryParams.set('project_id', params.project_id);

  const response = await apiFetch(`${API_BASE}/api/tasks?${queryParams}`);
  if (!response.ok) throw new Error(`Failed to list tasks: ${response.statusText}`);
  return response.json();
}

export async function getTask(taskId: string): Promise<Task> {
  const response = await apiFetch(`${API_BASE}/api/tasks/${taskId}`);
  if (!response.ok) throw new Error(`Failed to get task: ${response.statusText}`);
  return response.json();
}

export async function createTask(request: CreateTaskRequest): Promise<Task> {
  const response = await apiFetch(`${API_BASE}/api/tasks`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  if (!response.ok) throw new Error(`Failed to create task: ${response.statusText}`);
  return response.json();
}

export async function updateTask(taskId: string, request: UpdateTaskRequest): Promise<Task> {
  const response = await apiFetch(`${API_BASE}/api/tasks/${taskId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  if (!response.ok) throw new Error(`Failed to update task: ${response.statusText}`);
  return response.json();
}

export async function deleteTask(taskId: string): Promise<any> {
  const response = await apiFetch(`${API_BASE}/api/tasks/${taskId}`, {
    method: 'DELETE',
  });
  if (!response.ok) throw new Error(`Failed to delete task: ${response.statusText}`);
  return response.json();
}

export async function completeTask(taskId: string): Promise<Task> {
  const response = await apiFetch(`${API_BASE}/api/tasks/${taskId}/complete`, {
    method: 'PATCH',
  });
  if (!response.ok) throw new Error(`Failed to complete task: ${response.statusText}`);
  return response.json();
}

export async function uncompleteTask(taskId: string): Promise<Task> {
  const response = await apiFetch(`${API_BASE}/api/tasks/${taskId}/uncomplete`, {
    method: 'PATCH',
  });
  if (!response.ok) throw new Error(`Failed to uncomplete task: ${response.statusText}`);
  return response.json();
}


// ============================================================
// Invoices API (Phase 4 Frontend)
// ============================================================

export interface InvoiceLine {
  id: string;
  invoice_id: string;
  description: string;
  quantity: number;
  unit_price_ht: number;
  tva_rate: number;
  total_ht: number;
  total_ttc: number;
}

export interface Invoice {
  id: string;
  invoice_number: string;
  contact_id: string;
  issue_date: string;
  due_date: string;
  status: 'draft' | 'sent' | 'paid' | 'overdue' | 'cancelled';
  subtotal_ht: number;
  total_tax: number;
  total_ttc: number;
  notes: string | null;
  payment_date: string | null;
  created_at: string;
  updated_at: string;
  lines: InvoiceLine[];
}

export interface InvoiceLineRequest {
  description: string;
  quantity: number;
  unit_price_ht: number;
  tva_rate: number;
}

export interface CreateInvoiceRequest {
  contact_id: string;
  issue_date?: string;
  due_date?: string;
  lines: InvoiceLineRequest[];
  notes?: string;
}

export interface UpdateInvoiceRequest {
  contact_id?: string;
  issue_date?: string;
  due_date?: string;
  status?: string;
  lines?: InvoiceLineRequest[];
  notes?: string;
}

export async function listInvoices(params?: {
  status?: string;
  contact_id?: string;
}): Promise<Invoice[]> {
  const queryParams = new URLSearchParams();
  if (params?.status) queryParams.set('status', params.status);
  if (params?.contact_id) queryParams.set('contact_id', params.contact_id);

  const response = await apiFetch(`${API_BASE}/api/invoices?${queryParams}`);
  if (!response.ok) throw new Error(`Failed to list invoices: ${response.statusText}`);
  return response.json();
}

export async function getInvoice(invoiceId: string): Promise<Invoice> {
  const response = await apiFetch(`${API_BASE}/api/invoices/${invoiceId}`);
  if (!response.ok) throw new Error(`Failed to get invoice: ${response.statusText}`);
  return response.json();
}

export async function createInvoice(request: CreateInvoiceRequest): Promise<Invoice> {
  const response = await apiFetch(`${API_BASE}/api/invoices`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  if (!response.ok) throw new Error(`Failed to create invoice: ${response.statusText}`);
  return response.json();
}

export async function updateInvoice(invoiceId: string, request: UpdateInvoiceRequest): Promise<Invoice> {
  const response = await apiFetch(`${API_BASE}/api/invoices/${invoiceId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  if (!response.ok) throw new Error(`Failed to update invoice: ${response.statusText}`);
  return response.json();
}

export async function deleteInvoice(invoiceId: string): Promise<any> {
  const response = await apiFetch(`${API_BASE}/api/invoices/${invoiceId}`, {
    method: 'DELETE',
  });
  if (!response.ok) throw new Error(`Failed to delete invoice: ${response.statusText}`);
  return response.json();
}

export async function markInvoicePaid(invoiceId: string, paymentDate?: string): Promise<Invoice> {
  const response = await apiFetch(`${API_BASE}/api/invoices/${invoiceId}/mark-paid`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ payment_date: paymentDate }),
  });
  if (!response.ok) throw new Error(`Failed to mark invoice paid: ${response.statusText}`);
  return response.json();
}

export async function generateInvoicePDF(invoiceId: string): Promise<{ pdf_path: string; invoice_number: string }> {
  const response = await apiFetch(`${API_BASE}/api/invoices/${invoiceId}/pdf`);
  if (!response.ok) throw new Error(`Failed to generate PDF: ${response.statusText}`);
  return response.json();
}

export async function sendInvoiceByEmail(invoiceId: string): Promise<any> {
  const response = await apiFetch(`${API_BASE}/api/invoices/${invoiceId}/send`, {
    method: 'POST',
  });
  if (!response.ok) throw new Error(`Failed to send invoice: ${response.statusText}`);
  return response.json();
}

// =============================================================================
// CRM API (Phase 5)
// =============================================================================

// Types CRM
export interface ContactResponse extends Contact {
  stage: string;
  score: number;
  source: string | null;
  last_interaction: string | null;
}

export interface ActivityResponse {
  id: string;
  contact_id: string;
  type: string;
  title: string;
  description: string | null;
  extra_data: string | null;
  created_at: string;
}

export interface DeliverableResponse {
  id: string;
  project_id: string;
  title: string;
  description: string | null;
  status: string;
  due_date: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface PipelineStats {
  total_contacts: number;
  stages: Record<string, { count: number; avg_score: number }>;
}

// Activities API
export async function listActivities(params: {
  contact_id?: string;
  type?: string;
  skip?: number;
  limit?: number;
}): Promise<ActivityResponse[]> {
  const query = new URLSearchParams();
  if (params.contact_id) query.append('contact_id', params.contact_id);
  if (params.type) query.append('type', params.type);
  if (params.skip) query.append('skip', params.skip.toString());
  if (params.limit) query.append('limit', params.limit.toString());

  const response = await apiFetch(`${API_BASE}/crm/activities?${query}`);
  if (!response.ok) throw new Error(`Failed to list activities: ${response.statusText}`);
  return response.json();
}

export async function createActivity(data: {
  contact_id: string;
  type: string;
  title: string;
  description?: string;
  extra_data?: string;
}): Promise<ActivityResponse> {
  const response = await apiFetch(`${API_BASE}/crm/activities`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error(`Failed to create activity: ${response.statusText}`);
  return response.json();
}

export async function deleteActivity(activityId: string): Promise<void> {
  const response = await apiFetch(`${API_BASE}/crm/activities/${activityId}`, {
    method: 'DELETE',
  });
  if (!response.ok) throw new Error(`Failed to delete activity: ${response.statusText}`);
}

// Deliverables API
export async function listDeliverables(params: {
  project_id?: string;
  status?: string;
}): Promise<DeliverableResponse[]> {
  const query = new URLSearchParams();
  if (params.project_id) query.append('project_id', params.project_id);
  if (params.status) query.append('status', params.status);

  const response = await apiFetch(`${API_BASE}/crm/deliverables?${query}`);
  if (!response.ok) throw new Error(`Failed to list deliverables: ${response.statusText}`);
  return response.json();
}

export async function createDeliverable(data: {
  project_id: string;
  title: string;
  description?: string;
  status?: string;
  due_date?: string;
}): Promise<DeliverableResponse> {
  const response = await apiFetch(`${API_BASE}/crm/deliverables`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error(`Failed to create deliverable: ${response.statusText}`);
  return response.json();
}

export async function updateDeliverable(
  deliverableId: string,
  data: Partial<{
    title: string;
    description: string;
    status: string;
    due_date: string;
  }>
): Promise<DeliverableResponse> {
  const response = await apiFetch(`${API_BASE}/crm/deliverables/${deliverableId}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) throw new Error(`Failed to update deliverable: ${response.statusText}`);
  return response.json();
}

export async function deleteDeliverable(deliverableId: string): Promise<void> {
  const response = await apiFetch(`${API_BASE}/crm/deliverables/${deliverableId}`, {
    method: 'DELETE',
  });
  if (!response.ok) throw new Error(`Failed to delete deliverable: ${response.statusText}`);
}

// Pipeline API
export async function updateContactStage(
  contactId: string,
  stage: string
): Promise<ContactResponse> {
  const response = await apiFetch(`${API_BASE}/crm/contacts/${contactId}/stage`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ stage }),
  });
  if (!response.ok) throw new Error(`Failed to update contact stage: ${response.statusText}`);
  return response.json();
}

export async function recalculateContactScore(contactId: string): Promise<{
  contact_id: string;
  old_score: number;
  new_score: number;
  reason: string;
}> {
  const response = await apiFetch(`${API_BASE}/crm/contacts/${contactId}/recalculate-score`, {
    method: 'POST',
  });
  if (!response.ok) throw new Error(`Failed to recalculate score: ${response.statusText}`);
  return response.json();
}

export async function getPipelineStats(): Promise<PipelineStats> {
  const response = await apiFetch(`${API_BASE}/crm/pipeline/stats`);
  if (!response.ok) throw new Error(`Failed to get pipeline stats: ${response.statusText}`);
  return response.json();
}

// ============================================================
// Smart Email Features API
// ============================================================

/**
 * Classifie un email par priorité (Rouge/Orange/Vert).
 * US-EMAIL-08, US-EMAIL-10
 */
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
  if (!response.ok) throw new Error(`Failed to classify email: ${response.statusText}`);
  return response.json();
}

/**
 * Génère une proposition de réponse intelligente via LLM.
 * US-EMAIL-09
 */
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
  if (!response.ok) throw new Error(`Failed to generate response: ${response.statusText}`);
  return response.json();
}

/**
 * Change manuellement la priorité d'un email.
 * US-EMAIL-10
 */
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
  if (!response.ok) throw new Error(`Failed to update priority: ${response.statusText}`);
  return response.json();
}

/**
 * Récupère les statistiques d'emails par priorité.
 * US-EMAIL-12
 */
export async function getEmailStats(accountId: string): Promise<{
  high: number;
  medium: number;
  low: number;
  total_unread: number;
  total: number;
}> {
  const response = await apiFetch(`${API_BASE}/api/email/messages/stats?account_id=${accountId}`);
  if (!response.ok) throw new Error(`Failed to get email stats: ${response.statusText}`);
  return response.json();
}


// ============================================================
// CRM Sync (Google Sheets)
// ============================================================

export interface CRMSyncConfig {
  spreadsheet_id: string | null;
  last_sync: string | null;
  has_token: boolean;
  configured: boolean;
}

export interface CRMSyncStats {
  contacts_created: number;
  contacts_updated: number;
  projects_created: number;
  projects_updated: number;
  deliverables_created: number;
  deliverables_updated: number;
  errors: string[];
  total_synced: number;
}

export interface CRMSyncResponse {
  success: boolean;
  message: string;
  stats: CRMSyncStats | null;
  sync_time: string | null;
}

export async function getCRMSyncConfig(): Promise<CRMSyncConfig> {
  const response = await apiFetch(`${API_BASE}/api/crm/sync/config`);
  if (!response.ok) throw new Error(`Failed to get CRM sync config: ${response.statusText}`);
  return response.json();
}

export async function setCRMSpreadsheetId(spreadsheetId: string): Promise<CRMSyncConfig> {
  const response = await apiFetch(`${API_BASE}/api/crm/sync/config`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ spreadsheet_id: spreadsheetId }),
  });
  if (!response.ok) throw new Error(`Failed to set spreadsheet ID: ${response.statusText}`);
  return response.json();
}

export async function initiateCRMOAuth(): Promise<{
  auth_url: string;
  state: string;
  message: string;
}> {
  const response = await apiFetch(`${API_BASE}/api/crm/sync/connect`, {
    method: 'POST',
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `Failed to initiate OAuth: ${response.statusText}`);
  }
  return response.json();
}

export async function handleCRMOAuthCallback(state: string, code: string): Promise<{
  success: boolean;
  message: string;
}> {
  const params = new URLSearchParams({ state, code });
  const response = await apiFetch(`${API_BASE}/api/crm/sync/callback?${params}`);
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `OAuth callback failed: ${response.statusText}`);
  }
  return response.json();
}

export async function syncCRM(): Promise<CRMSyncResponse> {
  const response = await apiFetch(`${API_BASE}/api/crm/sync`, {
    method: 'POST',
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `CRM sync failed: ${response.statusText}`);
  }
  return response.json();
}

// ============================================================
// RGPD API (Phase 6)
// ============================================================

export type RGPDBaseLegale = 'consentement' | 'contrat' | 'interet_legitime' | 'obligation_legale';

export interface RGPDExportResponse {
  contact: Record<string, unknown>;
  activities: Record<string, unknown>[];
  projects: Record<string, unknown>[];
  tasks: Record<string, unknown>[];
  exported_at: string;
}

export interface RGPDAnonymizeResponse {
  success: boolean;
  message: string;
  contact_id: string;
}

export interface RGPDRenewConsentResponse {
  success: boolean;
  message: string;
  new_expiration: string;
}

export interface RGPDStatsResponse {
  total_contacts: number;
  par_base_legale: {
    consentement: number;
    contrat: number;
    interet_legitime: number;
    obligation_legale: number;
    non_defini: number;
  };
  sans_info_rgpd: number;
  expires_ou_bientot: number;
  avec_consentement: number;
}

export interface RGPDInferResponse {
  success: boolean;
  base_legale: RGPDBaseLegale;
  date_expiration: string;
}

/**
 * Exporte toutes les donnees d'un contact (droit de portabilite RGPD).
 */
export async function exportContactRGPD(contactId: string): Promise<RGPDExportResponse> {
  const response = await apiFetch(`${API_BASE}/api/rgpd/export/${contactId}`);
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `RGPD export failed: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Anonymise un contact (droit a l'oubli RGPD).
 */
export async function anonymizeContact(contactId: string, reason: string): Promise<RGPDAnonymizeResponse> {
  const response = await apiFetch(`${API_BASE}/api/rgpd/anonymize/${contactId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reason }),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `RGPD anonymize failed: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Renouvelle le consentement RGPD d'un contact (+3 ans).
 */
export async function renewContactConsent(contactId: string): Promise<RGPDRenewConsentResponse> {
  const response = await apiFetch(`${API_BASE}/api/rgpd/renew-consent/${contactId}`, {
    method: 'POST',
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `RGPD renew consent failed: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Met a jour les champs RGPD d'un contact.
 */
export async function updateContactRGPD(
  contactId: string,
  data: { rgpd_base_legale?: RGPDBaseLegale; rgpd_consentement?: boolean }
): Promise<{ success: boolean; message: string }> {
  const response = await apiFetch(`${API_BASE}/api/rgpd/${contactId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `RGPD update failed: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Recupere les statistiques RGPD globales.
 */
export async function getRGPDStats(): Promise<RGPDStatsResponse> {
  const response = await apiFetch(`${API_BASE}/api/rgpd/stats`);
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `RGPD stats failed: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Infere automatiquement la base legale RGPD d'un contact.
 */
export async function inferContactRGPD(contactId: string): Promise<RGPDInferResponse> {
  const response = await apiFetch(`${API_BASE}/api/rgpd/infer/${contactId}`, {
    method: 'POST',
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || `RGPD infer failed: ${response.statusText}`);
  }
  return response.json();
}
