/**
 * THÉRÈSE v2 - API Service
 *
 * Handles all communication with the Python FastAPI backend.
 */

export const API_BASE = 'http://127.0.0.1:8000';

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
  const response = await fetch(url, {
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
  const response = await fetch(url, {
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
  limit = 50
): Promise<Contact[]> {
  return request<Contact[]>(`/api/memory/contacts?offset=${offset}&limit=${limit}`);
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
}

export interface WorkingDirectory {
  path: string | null;
  exists: boolean;
}

export async function getProfile(): Promise<UserProfile | null> {
  const response = await fetch(`${API_BASE}/api/config/profile`);
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
  const response = await fetch(url);
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

  const response = await fetch(`${API_BASE}/api/voice/transcribe`, {
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
  return `${API_BASE}/api/images/download/${imageId}`;
}

export async function downloadGeneratedImage(imageId: string): Promise<void> {
  const { save } = await import('@tauri-apps/plugin-dialog');
  const { writeFile } = await import('@tauri-apps/plugin-fs');

  const url = getImageDownloadUrl(imageId);

  const response = await fetch(url);
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
  type: 'advisor_start' | 'advisor_chunk' | 'advisor_done' | 'synthesis_start' | 'synthesis_chunk' | 'done' | 'error';
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
  const response = await fetch(url, {
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
