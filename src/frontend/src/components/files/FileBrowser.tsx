/**
 * THERESE v2 - File Browser Component
 *
 * Native file browser using Tauri fs API for navigating local directories.
 */

import { useState, useEffect, useCallback } from 'react';
import { readDir, stat } from '@tauri-apps/plugin-fs';
import { homeDir, resolve } from '@tauri-apps/api/path';
import { open } from '@tauri-apps/plugin-dialog';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Folder,
  FolderOpen,
  File,
  FileText,
  FileCode,
  FileImage,
  FileSpreadsheet,
  FileType,
  ChevronRight,
  Home,
  HardDrive,
  RefreshCw,
  FolderUp,
  Search,
  Database,
  Loader2,
  AlertCircle,
} from 'lucide-react';
import { Button } from '../ui/Button';
import { cn } from '../../lib/utils';
import { indexFile, getWorkingDirectory, type FileMetadata } from '../../services/api';
import { staggerContainer, staggerItem, fadeIn } from '../../lib/animations';

export interface FileEntry {
  name: string;
  path: string;
  isDirectory: boolean;
  isFile: boolean;
  size?: number;
  extension?: string;
}

interface FileBrowserProps {
  onFileSelect?: (file: FileEntry) => void;
  onFileIndex?: (metadata: FileMetadata) => void;
  className?: string;
}

// File icon mapping by extension
function getFileIcon(extension?: string) {
  if (!extension) return File;

  const ext = extension.toLowerCase();

  // Code files
  if (['.py', '.js', '.ts', '.tsx', '.jsx', '.html', '.css', '.scss', '.json', '.yaml', '.yml', '.sh', '.rs', '.go', '.java', '.c', '.cpp', '.h'].includes(ext)) {
    return FileCode;
  }

  // Document files
  if (['.pdf', '.doc', '.docx', '.txt', '.md', '.rtf'].includes(ext)) {
    return FileText;
  }

  // Spreadsheet files
  if (['.xls', '.xlsx', '.csv', '.tsv'].includes(ext)) {
    return FileSpreadsheet;
  }

  // Image files
  if (['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.ico'].includes(ext)) {
    return FileImage;
  }

  // Presentation files
  if (['.ppt', '.pptx'].includes(ext)) {
    return FileType;
  }

  return File;
}

// Format file size
function formatSize(bytes?: number): string {
  if (!bytes) return '';
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  return (bytes / (1024 * 1024 * 1024)).toFixed(1) + ' GB';
}

// Check if file is indexable
function isIndexable(extension?: string): boolean {
  if (!extension) return false;
  const indexableExtensions = [
    '.txt', '.md', '.json', '.csv', '.tsv',
    '.py', '.js', '.ts', '.tsx', '.jsx', '.html', '.css', '.scss',
    '.yaml', '.yml', '.toml', '.xml', '.sql',
    '.pdf', '.doc', '.docx',
    '.sh', '.bash', '.zsh',
  ];
  return indexableExtensions.includes(extension.toLowerCase());
}

export function FileBrowser({ onFileSelect, onFileIndex, className }: FileBrowserProps) {
  const [currentPath, setCurrentPath] = useState<string>('');
  const [entries, setEntries] = useState<FileEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [indexingFile, setIndexingFile] = useState<string | null>(null);
  const [expandedFolders] = useState<Set<string>>(new Set());

  // Load directory contents
  const loadDirectory = useCallback(async (path: string) => {
    setLoading(true);
    setError(null);

    try {
      const dirEntries = await readDir(path);

      // Map entries and get additional info
      const mappedEntries: FileEntry[] = await Promise.all(
        dirEntries.map(async (entry) => {
          const fullPath = await resolve(path, entry.name);
          let size: number | undefined;

          // Get file size for files
          if (!entry.isDirectory) {
            try {
              const fileStat = await stat(fullPath);
              size = fileStat.size;
            } catch {
              // Ignore stat errors (permission denied, etc.)
            }
          }

          const extension = entry.isDirectory ? undefined : '.' + (entry.name.split('.').pop() || '');

          return {
            name: entry.name,
            path: fullPath,
            isDirectory: entry.isDirectory || false,
            isFile: !entry.isDirectory,
            size,
            extension,
          };
        })
      );

      // Sort: folders first, then files, alphabetically
      mappedEntries.sort((a, b) => {
        if (a.isDirectory && !b.isDirectory) return -1;
        if (!a.isDirectory && b.isDirectory) return 1;
        return a.name.localeCompare(b.name);
      });

      // Filter hidden files (starting with .)
      const visibleEntries = mappedEntries.filter(e => !e.name.startsWith('.'));

      setEntries(visibleEntries);
    } catch (err) {
      console.error('Failed to read directory:', err);
      setError('Impossible de lire ce répertoire');
      setEntries([]);
      // Fallback : revenir au répertoire home
      try {
        const home = await homeDir();
        if (path !== home) {
          setCurrentPath(home);
          const fallbackEntries = await readDir(home);
          const mapped: FileEntry[] = await Promise.all(
            fallbackEntries.map(async (entry) => {
              const fullPath = await resolve(home, entry.name);
              const extension = entry.isDirectory ? undefined : '.' + (entry.name.split('.').pop() || '');
              return { name: entry.name, path: fullPath, isDirectory: entry.isDirectory || false, isFile: !entry.isDirectory, extension };
            })
          );
          mapped.sort((a, b) => {
            if (a.isDirectory && !b.isDirectory) return -1;
            if (!a.isDirectory && b.isDirectory) return 1;
            return a.name.localeCompare(b.name);
          });
          setEntries(mapped.filter(e => !e.name.startsWith('.')));
        }
      } catch {
        // Impossible de charger le home non plus
      }
    } finally {
      setLoading(false);
    }
  }, []);

  // Initialize with working directory (from settings) or home directory
  useEffect(() => {
    async function init() {
      try {
        // First, try to get the configured working directory
        const workingDir = await getWorkingDirectory().catch(() => null);
        if (workingDir?.path && workingDir.exists) {
          setCurrentPath(workingDir.path);
          await loadDirectory(workingDir.path);
          return;
        }

        // Fallback to home directory
        const home = await homeDir();
        setCurrentPath(home);
        await loadDirectory(home);
      } catch (err) {
        console.error('Failed to get home directory:', err);
        setError('Impossible de charger le répertoire personnel');
      }
    }
    init();
  }, [loadDirectory]);

  // Navigate to directory
  const navigateTo = useCallback(async (path: string) => {
    setCurrentPath(path);
    await loadDirectory(path);
  }, [loadDirectory]);

  // Go up one level
  const goUp = useCallback(async () => {
    const parts = currentPath.split('/').filter(Boolean);
    if (parts.length > 1) {
      const parentPath = '/' + parts.slice(0, -1).join('/');
      await navigateTo(parentPath);
    }
  }, [currentPath, navigateTo]);

  // Go to home
  const goHome = useCallback(async () => {
    const home = await homeDir();
    await navigateTo(home);
  }, [navigateTo]);

  // Open folder picker
  const openFolderPicker = useCallback(async () => {
    try {
      const selected = await open({
        directory: true,
        multiple: false,
      });

      if (selected && typeof selected === 'string') {
        await navigateTo(selected);
      }
    } catch (err) {
      console.error('Folder picker error:', err);
    }
  }, [navigateTo]);

  // Handle file click
  const handleEntryClick = useCallback(async (entry: FileEntry) => {
    if (entry.isDirectory) {
      await navigateTo(entry.path);
    } else {
      onFileSelect?.(entry);
    }
  }, [navigateTo, onFileSelect]);

  // Index a file
  const handleIndexFile = useCallback(async (entry: FileEntry) => {
    if (!entry.isFile) return;

    setIndexingFile(entry.path);
    try {
      const metadata = await indexFile(entry.path);
      onFileIndex?.(metadata);
    } catch (err) {
      console.error('Failed to index file:', err);
      setError("Erreur d'indexation: " + entry.name);
    } finally {
      setIndexingFile(null);
    }
  }, [onFileIndex]);

  // Filter entries by search
  const filteredEntries = entries.filter(e =>
    e.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Breadcrumb parts
  const pathParts = currentPath.split('/').filter(Boolean);

  return (
    <div className={cn('flex flex-col h-full', className)}>
      {/* Toolbar */}
      <div className="flex items-center gap-2 p-3 border-b border-border/50">
        <Button
          variant="ghost"
          size="icon"
          onClick={goHome}
          title="Répertoire personnel"
          className="h-8 w-8"
        >
          <Home className="w-4 h-4" />
        </Button>

        <Button
          variant="ghost"
          size="icon"
          onClick={goUp}
          title="Remonter"
          className="h-8 w-8"
          disabled={pathParts.length <= 1}
        >
          <FolderUp className="w-4 h-4" />
        </Button>

        <Button
          variant="ghost"
          size="icon"
          onClick={() => loadDirectory(currentPath)}
          title="Actualiser"
          className="h-8 w-8"
        >
          <RefreshCw className={cn('w-4 h-4', loading && 'animate-spin')} />
        </Button>

        <Button
          variant="ghost"
          size="icon"
          onClick={openFolderPicker}
          title="Ouvrir un dossier"
          className="h-8 w-8"
        >
          <HardDrive className="w-4 h-4" />
        </Button>

        <div className="flex-1" />

        {/* Search */}
        <div className="relative">
          <Search className="absolute left-2 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-text-muted" />
          <input
            type="text"
            placeholder="Filtrer..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-32 pl-7 pr-2 py-1 text-xs bg-background/60 border border-border/50 rounded-md text-text placeholder:text-text-muted focus:outline-none focus:border-accent-cyan/50"
          />
        </div>
      </div>

      {/* Breadcrumb */}
      <div className="flex items-center gap-1 px-3 py-2 text-xs text-text-muted overflow-x-auto border-b border-border/30">
        <button
          onClick={goHome}
          className="hover:text-accent-cyan transition-colors"
        >
          ~
        </button>
        {pathParts.map((part, index) => (
          <span key={index} className="flex items-center">
            <ChevronRight className="w-3 h-3 mx-1 flex-shrink-0" />
            <button
              onClick={() => navigateTo('/' + pathParts.slice(0, index + 1).join('/'))}
              className="hover:text-accent-cyan transition-colors truncate max-w-[100px]"
              title={part}
            >
              {part}
            </button>
          </span>
        ))}
      </div>

      {/* Error message */}
      <AnimatePresence>
        {error && (
          <motion.div
            variants={fadeIn}
            initial="initial"
            animate="animate"
            exit="exit"
            className="mx-3 mt-2 p-2 rounded-lg bg-error/10 border border-error/20 flex items-center gap-2"
          >
            <AlertCircle className="w-4 h-4 text-error flex-shrink-0" />
            <p className="text-xs text-error">{error}</p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* File list */}
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="flex items-center justify-center h-32">
            <Loader2 className="w-6 h-6 text-accent-cyan animate-spin" />
          </div>
        ) : filteredEntries.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-32 text-text-muted">
            <Folder className="w-8 h-8 mb-2 opacity-50" />
            <p className="text-sm">
              {searchQuery ? 'Aucun resultat' : 'Dossier vide'}
            </p>
          </div>
        ) : (
          <motion.div
            variants={staggerContainer}
            initial="initial"
            animate="animate"
            className="divide-y divide-border/20"
          >
            {filteredEntries.map((entry) => {
              const Icon = entry.isDirectory
                ? (expandedFolders.has(entry.path) ? FolderOpen : Folder)
                : getFileIcon(entry.extension);
              const canIndex = entry.isFile && isIndexable(entry.extension);
              const isIndexing = indexingFile === entry.path;

              return (
                <motion.div
                  key={entry.path}
                  variants={staggerItem}
                  className={cn(
                    'flex items-center gap-2 px-3 py-2 hover:bg-background/40 transition-colors cursor-pointer group',
                    isIndexing && 'opacity-50'
                  )}
                  onClick={() => handleEntryClick(entry)}
                >
                  {/* Icon */}
                  <div className={cn(
                    'flex-shrink-0',
                    entry.isDirectory ? 'text-accent-cyan' : 'text-text-muted'
                  )}>
                    <Icon className="w-4 h-4" />
                  </div>

                  {/* Name */}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-text truncate">{entry.name}</p>
                    {entry.isFile && entry.size !== undefined && (
                      <p className="text-xs text-text-muted">{formatSize(entry.size)}</p>
                    )}
                  </div>

                  {/* Index button */}
                  {canIndex && (
                    <Button
                      variant="ghost"
                      size="icon"
                      className={cn(
                        'h-7 w-7 opacity-0 group-hover:opacity-100 transition-opacity',
                        isIndexing && 'opacity-100'
                      )}
                      onClick={(e) => {
                        e.stopPropagation();
                        handleIndexFile(entry);
                      }}
                      disabled={isIndexing}
                      title="Indexer ce fichier"
                    >
                      {isIndexing ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <Database className="w-3.5 h-3.5" />
                      )}
                    </Button>
                  )}

                  {/* Arrow for folders */}
                  {entry.isDirectory && (
                    <ChevronRight className="w-4 h-4 text-text-muted opacity-0 group-hover:opacity-100 transition-opacity" />
                  )}
                </motion.div>
              );
            })}
          </motion.div>
        )}
      </div>

      {/* Footer stats */}
      <div className="px-3 py-2 border-t border-border/50 text-xs text-text-muted">
        {filteredEntries.length} elements
        {searchQuery && ' (filtre: "' + searchQuery + '")'}
      </div>
    </div>
  );
}
