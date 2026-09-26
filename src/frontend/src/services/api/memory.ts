/**
 * THÉRÈSE v2 - Memory API Module
 *
 * Contacts, projects, and memory search.
 * Sprint 2 - PERF-2.2: Extracted from monolithic api.ts
 */

import { ApiError, request } from './core';
import type { CalendarEvent } from './calendar';

// Types
export interface Contact {
  id: string;
  first_name: string | null;
  last_name: string | null;
  company: string | null;
  email: string | null;
  phone: string | null;
  // B2 : le champ existe en base depuis toujours ; sans lui ici, aucune valeur
  // saisie ne remontait jusqu'à l'API.
  address: string | null;
  notes: string | null;
  tags: string[] | null;
  stage: string;
  score: number;
  source: string | null;
  last_interaction: string | null;
  created_at: string;
  updated_at: string;
  // Scope fields (E3-05) - présents côté backend
  scope?: string;
  scope_id?: string | null;
  // RGPD fields (Phase 6)
  rgpd_base_legale?: string | null;
  rgpd_date_collecte?: string | null;
  rgpd_date_expiration?: string | null;
  rgpd_consentement?: boolean;
  /** P-133 : la prochaine relance décidée, jour civil (le moteur la ramène à 09:00). */
  next_follow_up?: string | null;
}

export interface Project {
  id: string;
  name: string;
  description: string | null;
  contact_id: string | null;
  status: string;
  budget: number | null;
  notes: string | null;
  tags: string[] | null;
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
  // B-1391 : `version_lue` = updated_at de la version affichée (409 si périmée).
  data: Partial<Contact> & { version_lue?: string }
): Promise<Contact> {
  return request<Contact>(`/api/memory/contacts/${id}`, {
    method: 'PATCH',
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

/**
 * P-148 : ce que rassemble un projet, en une lecture
 * (`GET /api/memory/projects/{id}/ensemble`). Une famille dont la lecture a
 * échoué vaut `null` et se nomme dans `indisponibles` : une panne n'est pas
 * un vide.
 */
export interface FamilleListee<T> {
  total: number;
  elements: T[];
}

export interface ConversationDuProjet {
  id: string;
  titre: string | null;
  mise_a_jour: string;
}

export interface DocumentDuProjet {
  id: string;
  titre: string;
  statut: string;
  mise_a_jour: string;
}

export interface TacheDuProjet {
  id: string;
  titre: string;
  statut: string;
  /** Jour décidé, sans fuseau (comme `Task.due_date`). */
  echeance: string | null;
  en_retard: boolean;
}

export interface ContactDuProjet {
  id: string;
  /** Champs séparés : en démonstration, l'écran applique maskContact. */
  first_name: string | null;
  last_name: string | null;
  company: string | null;
  /** Le contact associé au projet (sinon, un contact rangé dans le projet). */
  associe: boolean;
}

export interface EnsembleDuProjet {
  conversations: FamilleListee<ConversationDuProjet> | null;
  documents: FamilleListee<DocumentDuProjet> | null;
  taches: (FamilleListee<TacheDuProjet> & { ouvertes: number; en_retard: number }) | null;
  /** `total` : personnes distinctes ; `ranges` : contacts rangés dans le projet. */
  contacts: (FamilleListee<ContactDuProjet> & { ranges: number }) | null;
  livrables: { total: number } | null;
  /** `deposes` : dans le dépôt de THÉRÈSE, effacés avec le projet ; `indexes_sur_place` : restent sur le disque. */
  fichiers: { total: number; deposes: number; indexes_sur_place: number } | null;
  /** Le dossier synchronisé rattaché, que la suppression détache. */
  dossier_synchronise: { rattache: boolean } | null;
  rendez_vous: { total: number } | null;
  sous_dossiers: { total: number } | null;
  planning: { total: number } | null;
  indisponibles: string[];
}

export async function lireLEnsembleDuProjet(id: string, limite = 5): Promise<EnsembleDuProjet> {
  return request<EnsembleDuProjet>(
    `/api/memory/projects/${encodeURIComponent(id)}/ensemble?limite=${limite}`,
  );
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
    method: 'PATCH',
    body: JSON.stringify(data),
  });
}

export async function deleteProject(id: string): Promise<void> {
  // Incident du 30/08 : les deux écrans appelaient la route sans cascade et
  // laissaient les fichiers du dossier sur un identifiant mort.
  await request<{ ok: boolean }>(`/api/memory/projects/${id}?cascade=true`, {
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
/**
 * Un résultat de recherche mémoire (forme réelle renvoyée par le backend).
 * Avant : searchMemory était typé `{ contacts? }` mais renvoyait `{ results }`,
 * donc `res.contacts` était toujours undefined -> moitié sémantique morte en UI
 * (régression trouvée par Syn). On expose désormais la vraie forme.
 */
export interface MemorySearchHit {
  id: string;
  entity_type: string; // 'contact' | 'project' | ...
  title: string;
  content: string;
  score: number;
  metadata?: Record<string, unknown> | null;
}

export interface MemorySearchResponse {
  query: string;
  results: MemorySearchHit[];
  total: number;
  search_time_ms: number;
}

/**
 * Le serveur attend `entity_types` au SINGULIER (MemorySearchRequest).
 * Le client parlait de `types` au pluriel : Pydantic ignore en silence un
 * champ inconnu, donc le filtre n'etait jamais applique et la recherche
 * restait plafonnee au defaut de 10 resultats.
 */
const TYPES_SERVEUR: Record<string, string> = {
  contacts: 'contact',
  projects: 'project',
  conversations: 'conversation',
  files: 'file',
};

export async function searchMemory(
  query: string,
  types: string[] = ['contacts', 'projects']
): Promise<MemorySearchResponse> {
  const entity_types = types.map((type) => TYPES_SERVEUR[type] ?? type);
  return request<MemorySearchResponse>('/api/memory/search', {
    method: 'POST',
    body: JSON.stringify({ query, entity_types }),
  });
}

// Import/Export VCF Contacts

/** B-1381 : le moteur a refusé le fichier ; son message est fait pour l'écran. */
export class ImportVcardRefuse extends Error {}

/** B-1381 : le message d'échec d'un import vCard, le même aux deux boutons. */
export function messageDEchecDImportVcard(erreur: unknown): string {
  return erreur instanceof ImportVcardRefuse
    ? erreur.message
    : 'L’import a échoué. Vérifie le fichier et réessaie.';
}

/**
 * Import vCard, commun au Pipeline et à Contacts (B-1381 : une route, une
 * règle de doublon, un bilan).
 */
export async function importVCFFile(
  file: File,
  updateExisting = true,
): Promise<{ created: number; updated: number; skipped: number; deja_a_jour: number; total: number; message: string }> {
  const formData = new FormData();
  formData.append('file', file);

  const { API_BASE, apiFetch } = await import('./core');
  const response = await apiFetch(
    `${API_BASE}/api/memory/contacts/import?update_existing=${updateExisting}`,
    { method: 'POST', body: formData },
  );
  if (!response.ok) {
    const d = await response.json().catch(() => ({}));
    const raison = typeof d.detail === 'string' ? d.detail : typeof d.message === 'string' ? d.message : '';
    if (response.status === 400 && raison) throw new ImportVcardRefuse(raison);
    throw new Error(raison || `Erreur ${response.status}`);
  }
  return response.json();
}

export async function exportVCFFile(): Promise<Blob> {
  const { API_BASE, apiFetch } = await import('./core');
  const response = await apiFetch(`${API_BASE}/api/memory/contacts/export`);
  if (!response.ok) {
    const d = await response.json().catch(() => ({}));
    throw new Error(d.detail || d.message || `Erreur ${response.status}`);
  }
  return response.blob();
}

export type VCFDownloadResult = 'desktop_saved' | 'browser_download_started';

function getVCFFilenameFromDisposition(disposition: string | null, parDefaut = 'therese-contacts.vcf'): string {
  if (!disposition) {
    return parDefaut;
  }

  const match = disposition.match(/filename="?([^";\n]+)"?/);
  return match?.[1] || parDefaut;
}

function buildVCFVariantFilename(filename: string, index: number): string {
  const dotIndex = filename.lastIndexOf('.');
  if (dotIndex <= 0) {
    return `${filename}-${index}`;
  }

  const base = filename.slice(0, dotIndex);
  const extension = filename.slice(dotIndex);
  return `${base}-${index}${extension}`;
}

async function saveVCFFileInDownloads(blob: Blob, filename: string): Promise<void> {
  const [{ downloadDir, join }, { exists, writeFile }] = await Promise.all([
    import('@tauri-apps/api/path'),
    import('@tauri-apps/plugin-fs'),
  ]);

  const downloadsPath = await downloadDir();
  let candidateFilename = filename;
  let targetPath = await join(downloadsPath, candidateFilename);
  let suffix = 2;

  while (await exists(targetPath)) {
    candidateFilename = buildVCFVariantFilename(filename, suffix);
    targetPath = await join(downloadsPath, candidateFilename);
    suffix += 1;
  }

  const arrayBuffer = await blob.arrayBuffer();
  await writeFile(targetPath, new Uint8Array(arrayBuffer));
}

export async function downloadVCFFile(): Promise<VCFDownloadResult> {
  const { API_BASE, apiFetch } = await import('./core');
  const response = await apiFetch(`${API_BASE}/api/memory/contacts/export`);
  if (!response.ok) {
    const d = await response.json().catch(() => ({}));
    throw new ApiError(response.status, response.statusText, d.detail || d.message || `Erreur ${response.status}`);
  }

  const filename = getVCFFilenameFromDisposition(response.headers.get('Content-Disposition'));
  return enregistrerLeTelechargement(await response.blob(), filename);
}

/**
 * P-137 : le moteur exporte les contacts en tableur, étapes comprises
 * (`POST /api/crm/export/contacts`) ; aucune surface ne l'appelait. Le
 * classeur se range dans Téléchargements, comme le vCard.
 */
export async function downloadContactsTableur(): Promise<VCFDownloadResult> {
  const { API_BASE, apiFetch } = await import('./core');
  const response = await apiFetch(`${API_BASE}/api/crm/export/contacts?format=xlsx`, { method: 'POST' });
  if (!response.ok) {
    const d = await response.json().catch(() => ({}));
    throw new ApiError(response.status, response.statusText, d.detail || d.message || `Erreur ${response.status}`);
  }
  const filename = getVCFFilenameFromDisposition(response.headers.get('Content-Disposition'), 'contacts.xlsx');
  return enregistrerLeTelechargement(await response.blob(), filename);
}

async function enregistrerLeTelechargement(blob: Blob, filename: string): Promise<VCFDownloadResult> {
  const isTauriRuntime = typeof window !== 'undefined' && ('__TAURI__' in window || '__TAURI_INTERNALS__' in window);

  if (isTauriRuntime) {
    await saveVCFFileInDownloads(blob, filename);
    return 'desktop_saved';
  }

  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = filename;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  URL.revokeObjectURL(url);
  return 'browser_download_started';
}

/**
 * P-116 : les prochaines séances d'un contact, rapprochées par son adresse
 * e-mail parmi les participants (même règle que Préparer et le brief).
 */
export async function listerLesSeancesDuContact(contactId: string): Promise<CalendarEvent[]> {
  return request<CalendarEvent[]>(`/api/memory/contacts/${encodeURIComponent(contactId)}/seances`);
}

/** P-130 : une ligne du tableur écartée ou signalée par le moteur. */
export interface LigneDImport {
  row: number;
  column: string | null;
  message: string;
  data?: Record<string, unknown> | null;
}

export interface ApercuImportContacts {
  total_rows: number;
  sample_rows: Record<string, unknown>[];
  detected_columns: string[];
  column_mapping: Record<string, string>;
  validation_errors: LigneDImport[];
  can_import: boolean;
}

export interface ResultatImportContacts {
  success: boolean;
  created: number;
  updated: number;
  skipped: number;
  errors: LigneDImport[];
  total_rows: number;
  message: string;
}

async function envoyerLeTableur<T>(chemin: string, fichier: File): Promise<T> {
  const formData = new FormData();
  formData.append('file', fichier);
  const { API_BASE, apiFetch } = await import('./core');
  const response = await apiFetch(`${API_BASE}${chemin}`, { method: 'POST', body: formData });
  if (!response.ok) {
    const d = await response.json().catch(() => ({}));
    const raison = typeof d.detail === 'string' ? d.detail : typeof d.message === 'string' ? d.message : '';
    throw new Error(raison || `Erreur ${response.status}`);
  }
  return response.json() as Promise<T>;
}

/** P-130 : aperçu sans écriture (colonnes reconnues, lignes écartées). */
export function apercuImportContacts(fichier: File): Promise<ApercuImportContacts> {
  return envoyerLeTableur<ApercuImportContacts>('/api/crm/import/contacts/preview', fichier);
}

/** P-130 : import d'un tableur CSV, Excel ou JSON (fiches existantes mises à jour). */
export function importerContactsTableur(fichier: File): Promise<ResultatImportContacts> {
  return envoyerLeTableur<ResultatImportContacts>('/api/crm/import/contacts', fichier);
}
