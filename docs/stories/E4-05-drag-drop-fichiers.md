# Story E4-05 : Implémenter le drag & drop de fichiers

## Description

En tant que **utilisateur**,
Je veux **déposer des fichiers par glisser-déposer**,
Afin de **intégrer rapidement mes documents dans THÉRÈSE**.

## Contexte technique

- **Composants impactés** : Frontend React, Tauri Events
- **Dépendances** : E1-01, E4-01
- **Fichiers concernés** :
  - `src/frontend/src/components/files/DropZone.tsx` (nouveau)
  - `src/frontend/src/hooks/useFileDrop.ts` (nouveau)
  - `src-tauri/src/lib.rs` (màj events)

## Critères d'acceptation

- [ ] Drag & drop depuis le Finder/Explorer
- [ ] Zone de drop visible avec feedback visuel
- [ ] Support multiple fichiers
- [ ] Validation des types acceptés (PDF, DOCX, TXT, MD)
- [ ] Affichage progression pour gros fichiers
- [ ] Intégration avec le file browser

## Notes techniques

### Hook useFileDrop

```typescript
// hooks/useFileDrop.ts
import { useState, useCallback } from 'react';
import { listen } from '@tauri-apps/api/event';
import { readFile } from '@tauri-apps/plugin-fs';

interface DroppedFile {
  name: string;
  path: string;
  size: number;
  type: string;
}

interface UseFileDropOptions {
  acceptedTypes?: string[];
  maxSize?: number;
  onDrop?: (files: DroppedFile[]) => void;
  onError?: (error: string) => void;
}

const DEFAULT_ACCEPTED = ['.pdf', '.docx', '.doc', '.txt', '.md'];
const DEFAULT_MAX_SIZE = 50 * 1024 * 1024; // 50 Mo

export function useFileDrop(options: UseFileDropOptions = {}) {
  const {
    acceptedTypes = DEFAULT_ACCEPTED,
    maxSize = DEFAULT_MAX_SIZE,
    onDrop,
    onError,
  } = options;

  const [isDragging, setIsDragging] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [droppedFiles, setDroppedFiles] = useState<DroppedFile[]>([]);

  // Écouter les events Tauri
  useEffect(() => {
    const unlistenDragEnter = listen('tauri://file-drop-hover', () => {
      setIsDragging(true);
    });

    const unlistenDragLeave = listen('tauri://file-drop-cancelled', () => {
      setIsDragging(false);
    });

    const unlistenDrop = listen<string[]>('tauri://file-drop', async (event) => {
      setIsDragging(false);
      setIsProcessing(true);

      try {
        const validFiles = await validateFiles(event.payload, acceptedTypes, maxSize);
        setDroppedFiles(validFiles);
        onDrop?.(validFiles);
      } catch (error) {
        onError?.(error instanceof Error ? error.message : 'Erreur lors du drop');
      } finally {
        setIsProcessing(false);
      }
    });

    return () => {
      unlistenDragEnter.then(fn => fn());
      unlistenDragLeave.then(fn => fn());
      unlistenDrop.then(fn => fn());
    };
  }, [acceptedTypes, maxSize, onDrop, onError]);

  return {
    isDragging,
    isProcessing,
    droppedFiles,
    clearFiles: () => setDroppedFiles([]),
  };
}

async function validateFiles(
  paths: string[],
  acceptedTypes: string[],
  maxSize: number
): Promise<DroppedFile[]> {
  const validFiles: DroppedFile[] = [];

  for (const path of paths) {
    const name = path.split('/').pop() || '';
    const ext = '.' + name.split('.').pop()?.toLowerCase();

    // Vérifier le type
    if (!acceptedTypes.includes(ext)) {
      console.warn(`Type non accepté: ${ext}`);
      continue;
    }

    // Vérifier la taille (via Tauri)
    const metadata = await invoke<{ size: number }>('get_file_metadata', { path });
    if (metadata.size > maxSize) {
      console.warn(`Fichier trop gros: ${name} (${metadata.size} bytes)`);
      continue;
    }

    validFiles.push({
      name,
      path,
      size: metadata.size,
      type: ext.slice(1),
    });
  }

  return validFiles;
}
```

### Composant DropZone

```tsx
// components/files/DropZone.tsx
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, FileCheck, Loader } from 'lucide-react';
import { useFileDrop } from '../../hooks/useFileDrop';

interface DropZoneProps {
  onFilesDropped: (files: DroppedFile[]) => void;
  className?: string;
  children?: React.ReactNode;
}

export function DropZone({ onFilesDropped, className, children }: DropZoneProps) {
  const { isDragging, isProcessing, droppedFiles } = useFileDrop({
    onDrop: onFilesDropped,
    onError: (error) => toast.error(error),
  });

  return (
    <div className={cn('relative', className)}>
      {children}

      {/* Overlay de drop */}
      <AnimatePresence>
        {isDragging && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 z-50 flex items-center justify-center bg-bg/90 backdrop-blur-sm border-2 border-dashed border-accent-cyan rounded-xl"
          >
            <div className="text-center">
              <Upload className="w-12 h-12 text-accent-cyan mx-auto mb-4" />
              <p className="text-lg text-text">Déposez vos fichiers ici</p>
              <p className="text-sm text-text-muted mt-2">
                PDF, DOCX, TXT, Markdown
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Indicateur de traitement */}
      <AnimatePresence>
        {isProcessing && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 z-50 flex items-center justify-center bg-bg/90"
          >
            <Loader className="w-8 h-8 text-accent-cyan animate-spin" />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
```

### Intégration dans le chat

```tsx
// components/chat/ChatArea.tsx (màj)
import { DropZone } from '../files/DropZone';

export function ChatArea() {
  const handleFilesDropped = async (files: DroppedFile[]) => {
    for (const file of files) {
      // Parser le fichier
      const parsed = await api.post(`/files/parse/${file.type}`, {
        file_path: file.path,
      });

      // Ajouter au contexte du chat
      addToContext({
        type: 'file',
        name: file.name,
        path: file.path,
        preview: parsed.text.slice(0, 500),
      });

      toast.success(`${file.name} ajouté au contexte`);
    }
  };

  return (
    <DropZone onFilesDropped={handleFilesDropped} className="flex-1">
      <div className="flex flex-col h-full">
        {/* Messages */}
        <MessageList />

        {/* Input */}
        <ChatInput />
      </div>
    </DropZone>
  );
}
```

### Commande Tauri pour métadonnées

```rust
// src-tauri/src/lib.rs (ajout)
use std::fs;

#[tauri::command]
fn get_file_metadata(path: &str) -> Result<FileMetadata, String> {
    let metadata = fs::metadata(path)
        .map_err(|e| e.to_string())?;

    Ok(FileMetadata {
        size: metadata.len(),
        is_dir: metadata.is_dir(),
        modified: metadata.modified()
            .ok()
            .and_then(|t| t.duration_since(std::time::UNIX_EPOCH).ok())
            .map(|d| d.as_secs()),
    })
}

#[derive(serde::Serialize)]
struct FileMetadata {
    size: u64,
    is_dir: bool,
    modified: Option<u64>,
}

// Dans la fonction main
fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            get_file_metadata,
            // ... autres commandes
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
```

### Indicateur de fichiers ajoutés

```tsx
// components/chat/ContextFiles.tsx
export function ContextFiles({ files, onRemove }: ContextFilesProps) {
  if (files.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-2 px-4 py-2 border-t border-border">
      {files.map((file) => (
        <motion.div
          key={file.path}
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.8, opacity: 0 }}
          className="flex items-center gap-2 px-3 py-1.5 bg-surface-elevated rounded-full text-sm"
        >
          <FileIcon type={file.type} className="w-4 h-4" />
          <span className="text-text truncate max-w-[150px]">{file.name}</span>
          <button
            onClick={() => onRemove(file.path)}
            className="p-0.5 hover:bg-surface rounded-full"
          >
            <X size={12} className="text-text-muted" />
          </button>
        </motion.div>
      ))}
    </div>
  );
}
```

## Estimation

- **Complexité** : S
- **Points** : 3

## Maquette

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   ┌─────────────────────────────────────────────────────┐   │
│   │                                                     │   │
│   │           ↓ Déposez vos fichiers ici ↓             │   │
│   │                                                     │   │
│   │              PDF, DOCX, TXT, Markdown               │   │
│   │                                                     │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                             │
├─────────────────────────────────────────────────────────────┤
│ [📄 rapport.pdf ×] [📝 notes.md ×]                          │
├─────────────────────────────────────────────────────────────┤
│ 💬 Message...                                          [→]  │
└─────────────────────────────────────────────────────────────┘
```

## Definition of Done

- [ ] Drag & drop fonctionne
- [ ] Validation types/taille
- [ ] Feedback visuel pendant drop
- [ ] Fichiers ajoutés au contexte
- [ ] Tests E2E

---

*Sprint : 4*
*Assigné : Agent Dev Frontend*
