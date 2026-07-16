/**
 * THÉRÈSE v2 - Images API Module
 *
 * Génération et gestion d'images IA.
 */

import { API_BASE, apiFetch, ApiError, request } from './core';

export type ImageProvider = 'gpt-image-2' | 'nanobanan-pro' | 'fal-flux-pro';

export interface ImageGenerateRequest {
  prompt: string;
  provider?: ImageProvider;
  size?: '1024x1024' | '1536x1024' | '1024x1536';
  quality?: 'low' | 'medium' | 'high';
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
  fal_available: boolean;
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
  // US-001 : plus de ?token= dans l'URL (le token ne doit jamais transiter en
  // clair dans une URL ni finir dans le DOM/les logs). L'authentification passe
  // par l'en-tete X-Therese-Token via apiFetch ; pour un affichage <img>, passer
  // par fetchImageObjectUrl (fetch authentifie -> blob).
  return `${API_BASE}/api/images/download/${imageId}`;
}

/**
 * Récupère une image en blob authentifié (en-tête X-Therese-Token) et renvoie
 * une object URL utilisable dans un <img src>. À révoquer (URL.revokeObjectURL)
 * après usage. US-001 : remplace l'ancien <img src={url}?token=...> qui exposait
 * le token dans le DOM. `downloadUrl` = sortie de getImageDownloadUrl(id).
 */
export async function fetchImageObjectUrl(downloadUrl: string): Promise<string> {
  const response = await apiFetch(downloadUrl);
  if (!response.ok) {
    throw new ApiError(response.status, response.statusText);
  }
  const blob = await response.blob();
  return URL.createObjectURL(blob);
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
