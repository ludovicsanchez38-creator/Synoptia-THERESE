/** Opérations globales de portabilité, sauvegarde et effacement des données. */

import { API_BASE, ApiError, apiFetch, request } from './core';

export interface BackupMetadata {
  backup_name: string;
  created_at: string;
  app_version?: string;
  archive_path?: string;
  included?: string[];
  size_bytes?: number;
  exists?: boolean;
}

export interface BackupStatus {
  has_backups: boolean;
  last_backup: BackupMetadata | null;
  days_since_backup?: number;
  recommendation: string | null;
}

export interface BackupCreateResponse {
  success: boolean;
  backup_name: string;
  path: string;
  created_at: string;
  included: string[];
}

export interface RestoreBackupResponse {
  success: boolean;
  restored_from: string;
  restored_at: string;
  safety_backup: string;
  note: string;
}

export type DataExportResult = 'desktop_saved' | 'browser_download_started' | 'cancelled';

function filenameFromDisposition(disposition: string | null): string {
  const match = disposition?.match(/filename="?([^";\n]+)"?/);
  return match?.[1] || `therese-export-${new Date().toISOString().slice(0, 10)}.json`;
}

export async function downloadAllData(): Promise<DataExportResult> {
  const response = await apiFetch(`${API_BASE}/api/data/export`);
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new ApiError(
      response.status,
      response.statusText,
      payload.detail || payload.message || `Erreur ${response.status}`,
    );
  }

  const filename = filenameFromDisposition(response.headers.get('Content-Disposition'));
  const blob = await response.blob();
  const isTauriRuntime = typeof window !== 'undefined'
    && ('__TAURI__' in window || '__TAURI_INTERNALS__' in window);

  if (isTauriRuntime) {
    const [{ save }, { writeFile }] = await Promise.all([
      import('@tauri-apps/plugin-dialog'),
      import('@tauri-apps/plugin-fs'),
    ]);
    const savePath = await save({
      defaultPath: filename,
      filters: [{ name: 'Export JSON Thérèse', extensions: ['json'] }],
    });
    if (!savePath) return 'cancelled';
    await writeFile(savePath, new Uint8Array(await blob.arrayBuffer()));
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

export async function listBackups(): Promise<BackupMetadata[]> {
  const response = await request<{ backups: BackupMetadata[] }>('/api/data/backups');
  return response.backups;
}

export function getBackupStatus(): Promise<BackupStatus> {
  return request<BackupStatus>('/api/data/backup/status');
}

export function createBackup(): Promise<BackupCreateResponse> {
  return request<BackupCreateResponse>('/api/data/backup', { method: 'POST' });
}

export function restoreBackup(backupName: string): Promise<RestoreBackupResponse> {
  return request<RestoreBackupResponse>(
    `/api/data/restore/${encodeURIComponent(backupName)}?confirm=true`,
    { method: 'POST' },
  );
}

export function deleteBackup(backupName: string): Promise<{ deleted: boolean; backup_name: string }> {
  return request(`/api/data/backups/${encodeURIComponent(backupName)}`, { method: 'DELETE' });
}

export function deleteAllData(): Promise<{ deleted: boolean; message: string; note: string }> {
  return request('/api/data/all?confirm=true', { method: 'DELETE' });
}
