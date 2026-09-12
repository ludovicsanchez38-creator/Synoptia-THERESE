/**
 * THÉRÈSE v2 - Code Review Panel
 *
 * Interface de review simplifiée pour non-développeurs.
 * Vocabulaire : "Appliquer les changements" / "Refuser" (pas merge/branch).
 */

import { useState, useEffect } from 'react';
import { Check, X, ChevronDown, ChevronRight, FileText, Plus, Minus } from 'lucide-react';
import { useAtelierStore } from '../../stores/atelierStore';
import { approveTask, rejectTask, getAgentTask, getTaskDiff } from '../../services/api/agents';
import type { DiffFile } from '../../services/api/agents';
import { cn } from '../../lib/utils';
import { Button } from '../ui/Button';
import { Etiquette } from '../ui/Etiquette';
import { EtatVide } from '../ui/EtatVide';

export function CodeReviewPanel() {
  const { currentMission } = useAtelierStore();
  const [diffFiles, setDiffFiles] = useState<DiffFile[]>([]);
  const [expandedFile, setExpandedFile] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [actionPending, setActionPending] = useState<'approve' | 'reject' | null>(null);
  const [actionDone, setActionDone] = useState<string | null>(null);
  const [confirmation, setConfirmation] = useState<'approve' | 'reject' | null>(null);
  const [totalAdd, setTotalAdd] = useState(0);
  const [totalDel, setTotalDel] = useState(0);

  useEffect(() => {
    if (currentMission?.taskId) {
      setIsLoading(true);
      getTaskDiff(currentMission.taskId)
        .then((diff) => {
          setDiffFiles(diff.files);
          setTotalAdd(diff.total_additions);
          setTotalDel(diff.total_deletions);
        })
        .catch(() => {
          // Le diff n'est peut-être pas encore prêt
        })
        .finally(() => setIsLoading(false));
    }
  }, [currentMission?.taskId]);

  const handleApprove = async () => {
    if (!currentMission?.taskId) return;
    setActionPending('approve');
    try {
      await approveTask(currentMission.taskId);
      const task = await getAgentTask(currentMission.taskId);
      if (task.status !== 'merged') throw new Error(`Statut backend inattendu : ${task.status}`);
      setActionDone('Changements appliqués avec succès !');
    } catch (e: any) {
      setActionDone(`Erreur : ${e.message}`);
    } finally {
      setActionPending(null);
    }
  };

  const handleReject = async () => {
    if (!currentMission?.taskId) return;
    setActionPending('reject');
    try {
      await rejectTask(currentMission.taskId);
      const task = await getAgentTask(currentMission.taskId);
      if (task.status !== 'rejected') throw new Error(`Statut backend inattendu : ${task.status}`);
      setActionDone('Changements refusés.');
    } catch (e: any) {
      setActionDone(`Erreur : ${e.message}`);
    } finally {
      setActionPending(null);
    }
  };

  if (!currentMission) {
    return (
      <EtatVide titre="Aucune mission en cours" className="flex h-full flex-col items-center justify-center" />
    );
  }

  return (
    <div className="flex h-full flex-col">
      {/* Explication par Katia */}
      {currentMission.explanation && (
        <div className="border-b border-border px-4 py-3">
          <div className="mb-1 text-xs font-medium text-agent-purple">
            Explication de Katia
          </div>
          <div className="text-sm leading-relaxed text-text">
            {currentMission.explanation}
          </div>
        </div>
      )}

      {/* Résumé des changements */}
      <div className="border-b border-border px-4 py-2">
        <div className="flex items-center gap-3 text-xs text-text-muted">
          <span className="flex items-center gap-1 text-agent-green">
            <Plus size={12} /> {totalAdd} ajouts
          </span>
          <span className="flex items-center gap-1 text-error">
            <Minus size={12} /> {totalDel} suppressions
          </span>
          <span>{diffFiles.length} fichier{diffFiles.length > 1 ? 's' : ''} touché{diffFiles.length > 1 ? 's' : ''}</span>
        </div>
      </div>

      {/* Liste des fichiers */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="flex items-center justify-center py-8 text-sm text-text-muted">
            Chargement des modifications...
          </div>
        ) : (
          diffFiles.map((file) => (
            <div key={file.file_path} className="border-b border-border">
              <Button
                type="button"
                variant="ghost"
                onClick={() => setExpandedFile(
                  expandedFile === file.file_path ? null : file.file_path
                )}
                className="h-auto w-full justify-start gap-2 rounded-sm px-4 py-2 text-left"
              >
                {expandedFile === file.file_path ? (
                  <ChevronDown size={14} className="text-text-muted" />
                ) : (
                  <ChevronRight size={14} className="text-text-muted" />
                )}
                <FileText size={14} className="text-text-muted" />
                <span className="flex-1 truncate text-text">
                  {file.file_path}
                </span>
                <Etiquette ton={file.change_type === 'added' ? 'succes' : file.change_type === 'deleted' ? 'erreur' : 'attention'}>
                  {file.change_type === 'added' ? 'nouveau' :
                   file.change_type === 'deleted' ? 'supprimé' :
                   'modifié'}
                </Etiquette>
              </Button>

              {expandedFile === file.file_path && file.diff_hunk && (
                <div className="overflow-x-auto bg-surface-2 px-4 py-2">
                  <pre className="text-xs leading-5">
                    {file.diff_hunk.split('\n').map((line, i) => (
                      <div
                        key={i}
                        className={cn(
                          line.startsWith('+') && !line.startsWith('+++') && 'bg-[var(--color-success-tint)] text-success',
                          line.startsWith('-') && !line.startsWith('---') && 'bg-[var(--color-error-tint)] text-error',
                          !(line.startsWith('+') && !line.startsWith('+++')) &&
                            !(line.startsWith('-') && !line.startsWith('---')) && 'text-text-muted',
                        )}
                      >
                        {line}
                      </div>
                    ))}
                  </pre>
                </div>
              )}
            </div>
          ))
        )}
      </div>

      {/* Actions */}
      {actionDone ? (
        <div className="border-t border-border px-4 py-3 text-center text-sm text-text-muted">
          {actionDone}
        </div>
      ) : confirmation ? (
        <div className="border-t border-border px-4 py-3">
          <div className="rounded-md border border-warning/30 bg-[var(--color-warning-tint)] p-3 text-sm text-text">
            <div className="font-semibold">
              {confirmation === 'approve'
                ? 'Appliquer ces changements sur main ?'
                : 'Refuser et supprimer la branche Atelier ?'}
            </div>
            <p className="mt-1 text-text-muted">
              Le succès ne sera affiché qu&apos;après confirmation du backend.
            </p>
            <div className="mt-3 flex flex-wrap justify-end gap-2">
              <Button type="button" variant="secondary" onClick={() => setConfirmation(null)}>Retour</Button>
              <Button
                type="button"
                variant={confirmation === 'approve' ? 'primary' : 'danger'}
                disabled={actionPending !== null}
                onClick={() => {
                  const action = confirmation;
                  setConfirmation(null);
                  if (action === 'approve') void handleApprove();
                  else void handleReject();
                }}
              >
                Confirmer l&apos;action
              </Button>
            </div>
          </div>
        </div>
      ) : (
        <div className="flex flex-wrap gap-3 border-t border-border px-4 py-3">
          <Button
            type="button"
            variant="primary"
            onClick={() => setConfirmation('approve')}
            disabled={actionPending !== null}
            className="min-w-48 flex-1"
          >
            <Check size={16} />
            {actionPending === 'approve' ? 'Application...' : 'Appliquer les changements'}
          </Button>
          <Button
            type="button"
            variant="danger"
            onClick={() => setConfirmation('reject')}
            disabled={actionPending !== null}
          >
            <X size={16} />
            {actionPending === 'reject' ? 'Refus...' : 'Refuser'}
          </Button>
        </div>
      )}
    </div>
  );
}
