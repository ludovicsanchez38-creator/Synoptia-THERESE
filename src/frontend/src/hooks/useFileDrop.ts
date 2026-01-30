/**
 * THÉRÈSE v2 - File Drop Hook
 *
 * Handles Tauri file drop events for drag & drop functionality.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { listen, type UnlistenFn } from '@tauri-apps/api/event';

export interface DroppedFile {
  path: string;
  name: string;
  size?: number;
  mimeType?: string;
}

export interface FileDropState {
  isDragging: boolean;
  droppedFiles: DroppedFile[];
  error: string | null;
}

export interface UseFileDropOptions {
  onDrop?: (files: DroppedFile[]) => void;
  onError?: (error: string) => void;
  disabled?: boolean;
}

interface TauriFileDrop {
  paths: string[];
  position: { x: number; y: number };
}

/**
 * Extract file name from path
 */
function getFileName(path: string): string {
  const parts = path.split(/[/\\]/);
  return parts[parts.length - 1] || path;
}

/**
 * Guess MIME type from extension
 */
function getMimeType(path: string): string {
  const ext = path.split('.').pop()?.toLowerCase() || '';
  const mimeTypes: Record<string, string> = {
    // Text
    txt: 'text/plain',
    md: 'text/markdown',
    json: 'application/json',
    csv: 'text/csv',
    // Code
    py: 'text/x-python',
    js: 'text/javascript',
    ts: 'text/typescript',
    tsx: 'text/typescript-jsx',
    jsx: 'text/javascript-jsx',
    html: 'text/html',
    css: 'text/css',
    // Documents
    pdf: 'application/pdf',
    doc: 'application/msword',
    docx: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    xls: 'application/vnd.ms-excel',
    xlsx: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    ppt: 'application/vnd.ms-powerpoint',
    pptx: 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    // Images
    png: 'image/png',
    jpg: 'image/jpeg',
    jpeg: 'image/jpeg',
    gif: 'image/gif',
    svg: 'image/svg+xml',
    webp: 'image/webp',
  };
  return mimeTypes[ext] || 'application/octet-stream';
}

/**
 * Hook for handling file drops in Tauri
 */
export function useFileDrop(options: UseFileDropOptions = {}): FileDropState & {
  clearFiles: () => void;
  clearError: () => void;
} {
  const { onDrop, onError, disabled = false } = options;

  const [isDragging, setIsDragging] = useState(false);
  const [droppedFiles, setDroppedFiles] = useState<DroppedFile[]>([]);
  const [error, setError] = useState<string | null>(null);

  // Use refs to avoid recreating listeners when callbacks change
  const onDropRef = useRef(onDrop);
  const onErrorRef = useRef(onError);
  const disabledRef = useRef(disabled);
  const unlistenRef = useRef<UnlistenFn[]>([]);
  const isSetupRef = useRef(false);

  // Keep refs updated
  useEffect(() => {
    onDropRef.current = onDrop;
    onErrorRef.current = onError;
    disabledRef.current = disabled;
  }, [onDrop, onError, disabled]);

  // Clear files
  const clearFiles = useCallback(() => {
    setDroppedFiles([]);
  }, []);

  // Clear error
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Set up Tauri listeners ONCE
  useEffect(() => {
    // Prevent double setup (React StrictMode)
    if (isSetupRef.current) return;
    isSetupRef.current = true;

    const setupListeners = async () => {
      try {
        // Listen for drag hover
        const unlistenHover = await listen<TauriFileDrop>(
          'tauri://drag-over',
          () => {
            if (!disabledRef.current) {
              setIsDragging(true);
            }
          }
        );

        // Listen for drag leave
        const unlistenLeave = await listen<void>('tauri://drag-leave', () => {
          setIsDragging(false);
        });

        // Listen for file drop
        const unlistenDrop = await listen<TauriFileDrop>(
          'tauri://drag-drop',
          (event) => {
            setIsDragging(false);
            if (disabledRef.current) return;
            if (!event.payload?.paths) return;

            try {
              const files: DroppedFile[] = event.payload.paths.map((path) => ({
                path,
                name: getFileName(path),
                mimeType: getMimeType(path),
              }));

              setDroppedFiles(files);
              setError(null);
              onDropRef.current?.(files);
            } catch (err) {
              const errorMsg = err instanceof Error ? err.message : 'Erreur lors du drop';
              setError(errorMsg);
              onErrorRef.current?.(errorMsg);
            }
          }
        );

        unlistenRef.current = [unlistenHover, unlistenLeave, unlistenDrop];
      } catch (err) {
        console.error('Failed to setup file drop listeners:', err);
      }
    };

    setupListeners();

    // Cleanup
    return () => {
      unlistenRef.current.forEach((unlisten) => unlisten());
      unlistenRef.current = [];
      isSetupRef.current = false;
    };
  }, []); // Empty deps - setup once only

  return {
    isDragging,
    droppedFiles,
    error,
    clearFiles,
    clearError,
  };
}
