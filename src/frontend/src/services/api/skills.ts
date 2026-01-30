/**
 * THÉRÈSE v2 - Skills API Module
 *
 * Skills execution and management.
 * Sprint 2 - PERF-2.2: Extracted from monolithic api.ts
 */

import { API_BASE, apiFetch, request, ApiError } from './core';

// Types
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
  inputs?: Record<string, any>;
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

// Skills API
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
  const { save } = await import('@tauri-apps/plugin-dialog');
  const { writeFile } = await import('@tauri-apps/plugin-fs');

  const url = getSkillDownloadUrl(fileId);

  const response = await apiFetch(url);
  if (!response.ok) {
    throw new ApiError(response.status, response.statusText);
  }

  const disposition = response.headers.get('Content-Disposition');
  let filename = fallbackFilename || 'document.docx';
  if (disposition) {
    const match = disposition.match(/filename="?([^";\n]+)"?/);
    if (match) filename = match[1];
  }

  const ext = filename.split('.').pop() || 'docx';
  const filterName = {
    docx: 'Document Word',
    pptx: 'Présentation PowerPoint',
    xlsx: 'Tableur Excel',
    pdf: 'Document PDF',
  }[ext] || 'Document';

  const savePath = await save({
    defaultPath: filename,
    filters: [{
      name: filterName,
      extensions: [ext],
    }],
  });

  if (!savePath) return;

  const blob = await response.blob();
  const arrayBuffer = await blob.arrayBuffer();
  const uint8Array = new Uint8Array(arrayBuffer);

  await writeFile(savePath, uint8Array);
}

export async function getSkillInputSchema(skillId: string): Promise<SkillSchema> {
  return request<SkillSchema>(`/api/skills/schema/${skillId}`);
}
