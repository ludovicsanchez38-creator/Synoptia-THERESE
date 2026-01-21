# Story E4-01 : Créer le file browser (navigation dossiers)

## Description

En tant que **utilisateur**,
Je veux **naviguer dans mes fichiers depuis THÉRÈSE**,
Afin de **accéder rapidement à mes documents**.

## Contexte technique

- **Composants impactés** : Frontend React, Tauri FS API
- **Dépendances** : E1-01, E1-05
- **Fichiers concernés** :
  - `src/frontend/src/components/files/FileBrowser.tsx` (nouveau)
  - `src/frontend/src/stores/fileStore.ts` (nouveau)
  - `src-tauri/tauri.conf.json` (màj permissions)

## Critères d'acceptation

- [ ] Arborescence de fichiers affichée
- [ ] Navigation par clic sur dossiers
- [ ] Breadcrumb pour le chemin actuel
- [ ] Icônes différentes par type de fichier
- [ ] Tri par nom/date/taille
- [ ] Recherche dans le dossier courant
- [ ] Raccourci ⌘⇧F pour ouvrir le browser

## Notes techniques

### Permissions Tauri

```json
// src-tauri/tauri.conf.json
{
  "tauri": {
    "allowlist": {
      "fs": {
        "all": false,
        "readDir": true,
        "readFile": true,
        "scope": ["$HOME/Documents/**", "$HOME/Desktop/**", "$DOWNLOAD/**"]
      },
      "path": {
        "all": true
      }
    }
  }
}
```

### Store fichiers

```typescript
// stores/fileStore.ts
import { create } from 'zustand';
import { readDir, FileEntry } from '@tauri-apps/plugin-fs';
import { homeDir, join } from '@tauri-apps/api/path';

interface FileItem {
  name: string;
  path: string;
  isDirectory: boolean;
  size?: number;
  modified?: Date;
  extension?: string;
}

interface FileStore {
  currentPath: string;
  files: FileItem[];
  isLoading: boolean;
  isPanelOpen: boolean;
  sortBy: 'name' | 'date' | 'size';
  sortOrder: 'asc' | 'desc';

  setPath: (path: string) => Promise<void>;
  navigateUp: () => Promise<void>;
  togglePanel: () => void;
  setSortBy: (sort: 'name' | 'date' | 'size') => void;
  refresh: () => Promise<void>;
}

export const useFileStore = create<FileStore>((set, get) => ({
  currentPath: '',
  files: [],
  isLoading: false,
  isPanelOpen: false,
  sortBy: 'name',
  sortOrder: 'asc',

  setPath: async (path: string) => {
    set({ isLoading: true });
    try {
      const entries = await readDir(path);
      const files = entries.map((entry) => ({
        name: entry.name || '',
        path: entry.path,
        isDirectory: entry.isDirectory || false,
        extension: entry.name?.split('.').pop()?.toLowerCase(),
      }));

      // Trier
      const sorted = sortFiles(files, get().sortBy, get().sortOrder);
      set({ currentPath: path, files: sorted, isLoading: false });
    } catch (error) {
      console.error('Failed to read directory:', error);
      set({ isLoading: false });
    }
  },

  navigateUp: async () => {
    const current = get().currentPath;
    const parent = current.split('/').slice(0, -1).join('/');
    if (parent) {
      await get().setPath(parent);
    }
  },

  togglePanel: () => set((state) => ({ isPanelOpen: !state.isPanelOpen })),

  setSortBy: (sortBy) => {
    const files = sortFiles(get().files, sortBy, get().sortOrder);
    set({ sortBy, files });
  },

  refresh: async () => {
    const path = get().currentPath;
    if (path) {
      await get().setPath(path);
    }
  },
}));

function sortFiles(files: FileItem[], by: string, order: string): FileItem[] {
  const sorted = [...files].sort((a, b) => {
    // Dossiers d'abord
    if (a.isDirectory !== b.isDirectory) {
      return a.isDirectory ? -1 : 1;
    }
    // Puis par critère
    if (by === 'name') {
      return a.name.localeCompare(b.name);
    }
    if (by === 'date') {
      return (a.modified?.getTime() || 0) - (b.modified?.getTime() || 0);
    }
    return (a.size || 0) - (b.size || 0);
  });

  return order === 'desc' ? sorted.reverse() : sorted;
}
```

### Composant FileBrowser

```tsx
// components/files/FileBrowser.tsx
import { Folder, File, ChevronRight, Search, ArrowUp } from 'lucide-react';
import { useFileStore } from '../../stores/fileStore';

const FILE_ICONS: Record<string, string> = {
  pdf: '📄',
  docx: '📝',
  doc: '📝',
  xlsx: '📊',
  xls: '📊',
  txt: '📃',
  md: '📑',
  png: '🖼️',
  jpg: '🖼️',
  jpeg: '🖼️',
};

export function FileBrowser() {
  const { currentPath, files, isLoading, setPath, navigateUp, sortBy, setSortBy } = useFileStore();
  const [search, setSearch] = useState('');

  const filteredFiles = files.filter((f) =>
    f.name.toLowerCase().includes(search.toLowerCase())
  );

  const handleClick = (file: FileItem) => {
    if (file.isDirectory) {
      setPath(file.path);
    } else {
      // Ouvrir le fichier
      openFile(file.path);
    }
  };

  return (
    <div className="flex flex-col h-full bg-surface">
      {/* Header */}
      <div className="p-4 border-b border-border">
        <div className="flex items-center gap-2 mb-3">
          <button onClick={navigateUp} className="p-2 hover:bg-surface-elevated rounded">
            <ArrowUp size={16} />
          </button>
          <Breadcrumb path={currentPath} onNavigate={setPath} />
        </div>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <input
            type="text"
            placeholder="Rechercher..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-surface-elevated rounded-lg text-sm"
          />
        </div>
      </div>

      {/* Sort controls */}
      <div className="flex items-center gap-2 px-4 py-2 text-xs text-text-muted border-b border-border">
        <span>Trier par:</span>
        {['name', 'date', 'size'].map((s) => (
          <button
            key={s}
            onClick={() => setSortBy(s as any)}
            className={cn(
              'px-2 py-1 rounded',
              sortBy === s && 'bg-surface-elevated text-text'
            )}
          >
            {s === 'name' ? 'Nom' : s === 'date' ? 'Date' : 'Taille'}
          </button>
        ))}
      </div>

      {/* File list */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="p-4 text-center text-text-muted">Chargement...</div>
        ) : filteredFiles.length === 0 ? (
          <div className="p-4 text-center text-text-muted">Aucun fichier</div>
        ) : (
          filteredFiles.map((file) => (
            <FileRow key={file.path} file={file} onClick={() => handleClick(file)} />
          ))
        )}
      </div>
    </div>
  );
}

function FileRow({ file, onClick }: { file: FileItem; onClick: () => void }) {
  const icon = file.isDirectory ? (
    <Folder className="w-5 h-5 text-accent-cyan" />
  ) : (
    <span className="text-lg">{FILE_ICONS[file.extension || ''] || '📄'}</span>
  );

  return (
    <button
      onClick={onClick}
      className="w-full flex items-center gap-3 px-4 py-2 hover:bg-surface-elevated text-left"
    >
      {icon}
      <span className="flex-1 truncate text-text">{file.name}</span>
      {!file.isDirectory && file.size && (
        <span className="text-xs text-text-muted">{formatSize(file.size)}</span>
      )}
    </button>
  );
}

function Breadcrumb({ path, onNavigate }: { path: string; onNavigate: (p: string) => void }) {
  const parts = path.split('/').filter(Boolean);

  return (
    <div className="flex items-center gap-1 text-sm overflow-x-auto">
      {parts.map((part, i) => (
        <Fragment key={i}>
          {i > 0 && <ChevronRight size={14} className="text-text-muted" />}
          <button
            onClick={() => onNavigate('/' + parts.slice(0, i + 1).join('/'))}
            className="text-text-muted hover:text-text truncate max-w-[100px]"
          >
            {part}
          </button>
        </Fragment>
      ))}
    </div>
  );
}
```

## Estimation

- **Complexité** : M
- **Points** : 5

## Maquette

```
┌─────────────────────────────────────────────────────────┐
│ [↑] /Users/ludo/Documents/Clients                       │
├─────────────────────────────────────────────────────────┤
│ 🔍 Rechercher...                                        │
├─────────────────────────────────────────────────────────┤
│ Trier par: [Nom] Date Taille                            │
├─────────────────────────────────────────────────────────┤
│ 📁 Pierre Heninger                                      │
│ 📁 Célia Galas                                          │
│ 📁 ADEOS                                                │
│ 📄 contrat-type.pdf                         45 Ko       │
│ 📝 notes-prospect.docx                      12 Ko       │
│ 📊 budget-2026.xlsx                         28 Ko       │
└─────────────────────────────────────────────────────────┘
```

## Definition of Done

- [ ] Navigation fonctionne
- [ ] Permissions Tauri configurées
- [ ] Tri et recherche actifs
- [ ] Icônes par type
- [ ] ⌘⇧F toggle le panneau

---

*Sprint : 4*
*Assigné : Agent Dev Frontend*
