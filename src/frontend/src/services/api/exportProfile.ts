/**
 * THÉRÈSE v2 - Profil d'export DOCX (chantier 5).
 * Pilote langue, polices, couleurs, footer et marges des exports
 * déterministes (Atelier documentaire + conversations).
 */
import { API_BASE, apiFetch, ApiError } from './core';

export interface ExportMargins {
  top: number;
  bottom: number;
  left: number;
  right: number;
}

export interface ExportProfile {
  version: number;
  language: string;
  body_font: string;
  body_size_pt: number;
  heading_font: string;
  title_color: string;
  heading_color: string;
  h2_color: string;
  body_color: string;
  footer_text: string;
  margins_cm: ExportMargins;
}

export interface ExportProfileResponse {
  profile: ExportProfile;
  warning: string | null;
}

async function _json(response: Response): Promise<ExportProfileResponse> {
  if (!response.ok) {
    const message = await response.text().catch(() => null);
    throw new ApiError(response.status, response.statusText, message || undefined);
  }
  return response.json() as Promise<ExportProfileResponse>;
}

export async function getExportProfile(): Promise<ExportProfileResponse> {
  return _json(await apiFetch(`${API_BASE}/api/config/export-profile`));
}

export async function saveExportProfile(
  profile: ExportProfile
): Promise<ExportProfileResponse> {
  return _json(
    await apiFetch(`${API_BASE}/api/config/export-profile`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(profile),
    })
  );
}

export async function resetExportProfile(): Promise<void> {
  const response = await apiFetch(`${API_BASE}/api/config/export-profile`, {
    method: 'DELETE',
  });
  if (!response.ok) {
    throw new ApiError(response.status, response.statusText);
  }
}
