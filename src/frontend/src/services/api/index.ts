/**
 * THÉRÈSE v2 - API Module Index
 *
 * Re-exports all API modules for convenient importing.
 * Sprint 2 - PERF-2.2: Modular API structure
 *
 * Usage:
 *   import { streamMessage, Contact, checkHealth } from '../services/api';
 *
 * Or import specific modules:
 *   import { streamMessage } from '../services/api/chat';
 *   import { Contact, listContacts } from '../services/api/memory';
 */

// Core - Base types, helpers, auth
export {
  API_BASE,
  initializeAuth,
  apiFetch,
  request,
  ApiError,
  checkHealth,
  getStats,
  type HealthStatus,
  type Stats,
} from './core';

// Chat - Messaging and conversations
export {
  sendMessage,
  streamMessage,
  listConversations,
  getConversation,
  createConversation,
  getConversationMessages,
  deleteConversation,
  type ChatMessage,
  type ChatRequest,
  type ChatResponse,
  type ExtractedContact,
  type ExtractedProject,
  type DetectedEntities,
  type StreamChunk,
  type ConversationResponse,
  type MessageResponse,
} from './chat';

// Memory - Contacts and projects
export {
  listContacts,
  getContact,
  createContact,
  updateContact,
  deleteContact,
  listContactsWithScope,
  deleteContactWithCascade,
  listProjects,
  getProject,
  createProject,
  updateProject,
  deleteProject,
  listProjectsWithScope,
  deleteProjectWithCascade,
  searchMemory,
  type Contact,
  type Project,
  type MemoryScope,
  type ScopeFilter,
  type DeleteResponse,
} from './memory';

// Config - Settings, profile, LLM config
export {
  getPreferences,
  setPreference,
  getApiKeys,
  setApiKey,
  getProfile,
  setProfile,
  deleteProfile,
  importClaudeMd,
  getWorkingDirectory,
  setWorkingDirectory,
  getLLMConfig,
  setLLMConfig,
  getOllamaStatus,
  getOnboardingStatus,
  completeOnboarding,
  getWebSearchStatus,
  setWebSearchEnabled,
  hasGroqKey,
  type UserProfile,
  type UserProfileUpdate,
  type WorkingDirectory,
  type LLMProvider,
  type LLMConfig,
  type OllamaModel,
  type OllamaStatus,
  type OnboardingStatus,
  type WebSearchStatus,
} from './config';

// Files - File management
export {
  listFiles,
  indexFile,
  getFile,
  getFileContent,
  deleteFile,
  type FileMetadata,
} from './files';

// Skills - Document generation
export {
  listSkills,
  getSkillInfo,
  executeSkill,
  getSkillDownloadUrl,
  downloadSkillFile,
  getSkillInputSchema,
  type SkillInfo,
  type SkillExecuteRequest,
  type SkillExecuteResponse,
  type InputField,
  type SkillSchema,
} from './skills';

// Commands - User commands
export {
  listUserCommands,
  getUserCommand,
  createUserCommand,
  updateUserCommand,
  deleteUserCommand,
  type UserCommand,
  type CreateCommandRequest,
} from './commands';
