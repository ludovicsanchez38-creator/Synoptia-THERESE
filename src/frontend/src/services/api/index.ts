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
  initApiBase,
  getApiBase,
  initializeAuth,
  apiFetch,
  request,
  getSessionToken,
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

// Voice - Transcription audio
export {
  transcribeAudio,
  type TranscriptionResponse,
} from './voice';

// Images - Génération d'images IA
export {
  generateImage,
  getImageStatus,
  getImageDownloadUrl,
  downloadGeneratedImage,
  listGeneratedImages,
  type ImageProvider,
  type ImageGenerateRequest,
  type ImageResponse,
  type ImageProviderStatus,
} from './images';

// Board - Décision stratégique
export {
  listAdvisors,
  getAdvisor,
  streamDeliberation,
  listBoardDecisions,
  getBoardDecision,
  deleteBoardDecision,
  type AdvisorRole,
  type AdvisorInfo,
  type BoardRequest,
  type BoardDeliberationChunk,
  type BoardSynthesis,
  type BoardDecisionResponse,
} from './board';

// Calculators - Calculatrices business
export {
  calculateROI,
  calculateICE,
  calculateRICE,
  calculateNPV,
  calculateBreakEven,
  getCalculatorsHelp,
  type ROIResult,
  type ICEResult,
  type RICEResult,
  type NPVResult,
  type BreakEvenResult,
  type CalculatorInfo,
} from './calculators';

// MCP - Model Context Protocol
export {
  listMCPServers,
  createMCPServer,
  getMCPServer,
  updateMCPServer,
  deleteMCPServer,
  startMCPServer,
  stopMCPServer,
  restartMCPServer,
  listMCPTools,
  callMCPTool,
  getMCPStatus,
  listMCPPresets,
  installMCPPreset,
  type MCPServerStatus,
  type MCPTool,
  type MCPServer,
  type MCPServerCreate,
  type MCPPreset,
  type MCPStatus,
  type ToolCallResult,
} from './mcp';

// Performance - Métriques et optimisation
export {
  getPerformanceMetrics,
  getRecentMetrics,
  getConversationsCount,
  searchConversations,
  reindexConversations,
  getMemoryStats,
  triggerMemoryCleanup,
  getPowerSettings,
  updatePowerSettings,
  setBatterySaver,
  getPerformanceStatus,
  type PerformanceMetrics,
  type StreamingMetric,
  type MemoryStats,
  type PowerSettings,
  type SearchResult,
  type PerformanceStatus,
} from './performance';

// Personalisation - Templates et comportement
export {
  listPromptTemplates,
  createPromptTemplate,
  getPromptTemplate,
  updatePromptTemplate,
  deletePromptTemplate,
  getLLMBehavior,
  setLLMBehavior,
  getFeatureVisibility,
  setFeatureVisibility,
  getPersonalisationStatus,
  type PromptTemplate,
  type PromptTemplateCreate,
  type LLMBehaviorSettings,
  type FeatureVisibilitySettings,
  type PersonalisationStatus,
} from './personalisation';

// Escalation - Limites et coûts
export {
  estimateCost,
  getTokenPrices,
  getTokenLimits,
  setTokenLimits,
  checkTokenLimits,
  getDailyUsage,
  getMonthlyUsage,
  getUsageHistory,
  getUsageStats,
  checkUncertainty,
  getContextInfo,
  getEscalationStatus,
  type CostEstimate,
  type TokenPrice,
  type TokenLimits,
  type LimitCheckResult,
  type DailyUsage,
  type MonthlyUsage,
  type UsageRecord,
  type UsageStats,
  type UncertaintyResult,
  type ContextInfo,
  type EscalationStatus,
} from './escalation';

// Email - Gmail OAuth et messages
export {
  getEmailSetupStatus,
  validateEmailCredentials,
  generateEmailSetupGuide,
  initiateEmailOAuth,
  reauthorizeEmail,
  handleEmailOAuthCallback,
  getEmailAuthStatus,
  disconnectEmailAccount,
  listEmailMessages,
  getEmailMessage,
  sendEmail,
  createDraft,
  modifyEmailMessage,
  deleteEmailMessage,
  listEmailLabels,
  createEmailLabel,
  updateEmailLabel,
  deleteEmailLabel,
  classifyEmail,
  generateEmailResponse,
  updateEmailPriority,
  getEmailStats,
  type EmailAccount,
  type EmailMessage,
  type EmailLabel,
  type OAuthFlowData,
  type SendEmailRequest,
  type GoogleCredentials,
  type SetupStatus,
  type ValidationResult,
  type ValidateCredentialsResponse,
  type GenerateGuideResponse,
} from './email';

// Calendar - Google Calendar
export {
  listCalendars,
  getCalendar,
  createCalendar,
  deleteCalendar,
  listEvents,
  getEvent,
  createEvent,
  updateEvent,
  deleteEvent,
  quickAddEvent,
  syncCalendar,
  getCalendarSyncStatus,
  type Calendar,
  type CalendarEvent,
  type CreateEventRequest,
  type UpdateEventRequest,
  type CalendarSyncResponse,
} from './calendar';

// Tasks - Gestion de tâches
export {
  listTasks,
  getTask,
  createTask,
  updateTask,
  deleteTask,
  completeTask,
  uncompleteTask,
  type Task,
  type CreateTaskRequest,
  type UpdateTaskRequest,
} from './tasks';

// Invoices - Facturation
export {
  listInvoices,
  getInvoice,
  createInvoice,
  updateInvoice,
  deleteInvoice,
  markInvoicePaid,
  generateInvoicePDF,
  sendInvoiceByEmail,
  type InvoiceLine,
  type Invoice,
  type InvoiceLineRequest,
  type CreateInvoiceRequest,
  type UpdateInvoiceRequest,
} from './invoices';

// CRM - Contact creation + push
export {
  createCRMContact,
  type CreateCRMContactRequest,
} from './crm';

// CRM Extended - Activities, deliverables, pipeline, sync
export {
  listActivities,
  createActivity,
  deleteActivity,
  listDeliverables,
  createDeliverable,
  updateDeliverable,
  deleteDeliverable,
  updateContactStage,
  recalculateContactScore,
  getPipelineStats,
  getCRMSyncConfig,
  setCRMSpreadsheetId,
  initiateCRMOAuth,
  handleCRMOAuthCallback,
  syncCRM,
  type ContactResponse,
  type ActivityResponse,
  type DeliverableResponse,
  type PipelineStats,
  type CRMSyncConfig,
  type CRMSyncStats,
  type CRMSyncResponse,
} from './crm-extended';

// RGPD - Conformité données personnelles
export {
  exportContactRGPD,
  anonymizeContact,
  renewContactConsent,
  updateContactRGPD,
  getRGPDStats,
  inferContactRGPD,
  type RGPDBaseLegale,
  type RGPDExportResponse,
  type RGPDAnonymizeResponse,
  type RGPDRenewConsentResponse,
  type RGPDStatsResponse,
  type RGPDInferResponse,
} from './rgpd';
