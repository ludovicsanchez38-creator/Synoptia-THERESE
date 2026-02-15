/**
 * THÉRÈSE v2 - Projet Panel Standalone
 *
 * Panel projets en plein écran pour ouverture dans une fenêtre Tauri séparée.
 * Affiche uniquement les projets (Kanban + recherche + suppression).
 */

import { useState, useEffect } from 'react';
import { Plus, Search, Trash2, AlertCircle } from 'lucide-react';
import { AnimatePresence, motion } from 'framer-motion';
import { Button } from '../ui/Button';
import { ProjectsKanban } from './ProjectsKanban';
import { ProjectModal } from './ProjectModal';
import * as api from '../../services/api';
import type { MemoryScope } from '../../services/api';
import { useDemoMask } from '../../hooks';

export function MemoryPanelStandalone() {
  const [projects, setProjects] = useState<api.Project[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [scopeFilter, setScopeFilter] = useState<MemoryScope | 'all'>('all');
  const [deleteConfirm, setDeleteConfirm] = useState<{ id: string; name: string } | null>(null);
  const [deleting, setDeleting] = useState(false);
  const { enabled: demoEnabled, maskProject, populateMap } = useDemoMask();

  // Modal
  const [showProjectModal, setShowProjectModal] = useState(false);
  const [editingProject, setEditingProject] = useState<api.Project | null>(null);

  useEffect(() => {
    loadData();
  }, [scopeFilter]);

  async function loadData() {
    setLoading(true);
    try {
      const scopeParams: api.ScopeFilter | undefined = scopeFilter !== 'all'
        ? { scope: scopeFilter as MemoryScope }
        : undefined;

      const projectsData = await api.listProjectsWithScope(0, 50, scopeParams);
      setProjects(projectsData);
      populateMap([], projectsData);
    } catch (error) {
      console.error('Failed to load projects:', error);
    } finally {
      setLoading(false);
    }
  }

  async function handleDelete() {
    if (!deleteConfirm) return;
    setDeleting(true);
    try {
      await api.deleteProjectWithCascade(deleteConfirm.id, true);
      setProjects(prev => prev.filter(p => p.id !== deleteConfirm.id));
      setDeleteConfirm(null);
    } catch (error) {
      console.error('Failed to delete project:', error);
    } finally {
      setDeleting(false);
    }
  }

  async function handleProjectStatusChange(projectId: string, newStatus: string) {
    try {
      const updated = await api.updateProject(projectId, { status: newStatus });
      setProjects(prev => prev.map(p => p.id === projectId ? updated : p));
    } catch (error) {
      console.error('Failed to update project status:', error);
    }
  }

  const filteredProjects = projects.filter(p => {
    const q = searchQuery.toLowerCase();
    return p.name.toLowerCase().includes(q) || p.description?.toLowerCase().includes(q);
  });

  const displayProjects = demoEnabled ? filteredProjects.map(p => maskProject(p)) : filteredProjects;

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="h-14 flex items-center justify-between px-6 border-b border-border/50 bg-surface/60">
        <h1 className="text-lg font-bold gradient-text">Projets</h1>
        <Button
          variant="primary"
          size="sm"
          onClick={() => { setEditingProject(null); setShowProjectModal(true); }}
        >
          <Plus className="w-4 h-4 mr-1" />
          Nouveau projet
        </Button>
      </div>

      {/* Search + Scope */}
      <div className="px-6 py-3 border-b border-border/30 space-y-2">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <input
            type="text"
            placeholder="Rechercher un projet..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted focus:outline-none focus:border-accent-cyan/50 transition-colors"
          />
        </div>
        <div className="flex gap-1.5">
          {(['all', 'global', 'project', 'conversation'] as const).map((scope) => (
            <button
              key={scope}
              onClick={() => setScopeFilter(scope)}
              className={`px-2.5 py-1 text-xs font-medium rounded-full transition-colors ${
                scopeFilter === scope
                  ? 'bg-accent-cyan/20 text-accent-cyan border border-accent-cyan/50'
                  : 'bg-background/40 text-text-muted hover:bg-background/60 border border-transparent'
              }`}
            >
              {scope === 'all' ? 'Tout' : scope === 'global' ? 'Global' : scope === 'project' ? 'Projet' : 'Conv.'}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto relative">
        {loading ? (
          <div className="flex items-center justify-center h-32">
            <div className="w-6 h-6 border-2 border-accent-cyan border-t-transparent rounded-full animate-spin" />
          </div>
        ) : (
          <ProjectsKanban
            projects={displayProjects}
            onSelect={(p) => { setEditingProject(p); setShowProjectModal(true); }}
            onDelete={(p) => setDeleteConfirm({ id: p.id, name: p.name })}
            onStatusChange={handleProjectStatusChange}
          />
        )}

        {/* Delete confirmation */}
        <AnimatePresence>
          {deleteConfirm && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="absolute inset-0 bg-black/60 flex items-center justify-center p-4 z-10"
              onClick={() => setDeleteConfirm(null)}
            >
              <motion.div
                initial={{ scale: 0.95, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                exit={{ scale: 0.95, opacity: 0 }}
                className="bg-surface border border-border rounded-xl p-5 w-full max-w-sm shadow-xl"
                onClick={(e) => e.stopPropagation()}
              >
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-10 h-10 rounded-full bg-red-500/20 flex items-center justify-center">
                    <AlertCircle className="w-5 h-5 text-red-400" />
                  </div>
                  <div>
                    <h3 className="text-base font-semibold text-text">Supprimer le projet ?</h3>
                    <p className="text-sm text-text-muted">{deleteConfirm.name}</p>
                  </div>
                </div>
                <p className="text-sm text-text-muted mb-4">
                  Les fichiers associés seront aussi supprimés.
                </p>
                <div className="flex gap-2">
                  <Button variant="ghost" className="flex-1" onClick={() => setDeleteConfirm(null)} disabled={deleting}>
                    Annuler
                  </Button>
                  <Button variant="primary" className="flex-1 bg-red-500 hover:bg-red-600" onClick={handleDelete} disabled={deleting}>
                    {deleting ? (
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    ) : (
                      <><Trash2 className="w-4 h-4 mr-2" />Supprimer</>
                    )}
                  </Button>
                </div>
              </motion.div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Project Modal */}
      <ProjectModal
        isOpen={showProjectModal}
        onClose={() => { setShowProjectModal(false); setEditingProject(null); }}
        onSaved={() => loadData()}
        project={editingProject}
      />
    </div>
  );
}
