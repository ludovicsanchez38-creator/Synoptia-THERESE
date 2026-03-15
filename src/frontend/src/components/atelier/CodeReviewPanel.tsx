/**
 * THÉRÈSE v2 - Code Review Panel
 *
 * Interface de review simplifiée pour non-développeurs.
 * Vocabulaire : "Appliquer les changements" / "Refuser" (pas merge/branch).
 */

import { useState, useEffect } from 'react';
import { Check, X, ChevronDown, ChevronRight, FileText, Plus, Minus } from 'lucide-react';
import { useAtelierStore } from '../../stores/atelierStore';
import { approveTask, rejectTask, getTaskDiff } from '../../services/api/agents';
import type { DiffFile } from '../../services/api/agents';

export function CodeReviewPanel() {
  const { currentMission } = useAtelierStore();
  const [diffFiles, setDiffFiles] = useState<DiffFile[]>([]);
  const [expandedFile, setExpandedFile] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [actionPending, setActionPending] = useState<'approve' | 'reject' | null>(null);
  const [actionDone, setActionDone] = useState<string | null>(null);
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
      setActionDone('Changements refusés.');
    } catch (e: any) {
      setActionDone(`Erreur : ${e.message}`);
    } finally {
      setActionPending(null);
    }
  };

  if (!currentMission) {
    return (
      <div className="flex h-full items-center justify-center text-sm text-[#6B7280]">
        Aucune mission en cours
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      {/* Explication par Katia */}
      {currentMission.explanation && (
        <div className="border-b border-white/5 px-4 py-3">
          <div className="mb-1 text-xs font-medium text-purple-400">
            Explication de Katia
          </div>
          <div className="text-sm leading-relaxed text-[#E6EDF7]">
            {currentMission.explanation}
          </div>
        </div>
      )}

      {/* Résumé des changements */}
      <div className="border-b border-white/5 px-4 py-2">
        <div className="flex items-center gap-3 text-xs text-[#B6C7DA]">
          <span className="flex items-center gap-1 text-green-400">
            <Plus size={12} /> {totalAdd} ajouts
          </span>
          <span className="flex items-center gap-1 text-red-400">
            <Minus size={12} /> {totalDel} suppressions
          </span>
          <span>{diffFiles.length} fichier{diffFiles.length > 1 ? 's' : ''} touché{diffFiles.length > 1 ? 's' : ''}</span>
        </div>
      </div>

      {/* Liste des fichiers */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="flex items-center justify-center py-8 text-sm text-[#6B7280]">
            Chargement des modifications...
          </div>
        ) : (
          diffFiles.map((file) => (
            <div key={file.file_path} className="border-b border-white/5">
              <button
                onClick={() => setExpandedFile(
                  expandedFile === file.file_path ? null : file.file_path
                )}
                className="flex w-full items-center gap-2 px-4 py-2 text-left text-sm transition hover:bg-white/5"
              >
                {expandedFile === file.file_path ? (
                  <ChevronDown size={14} className="text-[#6B7280]" />
                ) : (
                  <ChevronRight size={14} className="text-[#6B7280]" />
                )}
                <FileText size={14} className="text-[#B6C7DA]" />
                <span className="flex-1 truncate text-[#E6EDF7]">
                  {file.file_path}
                </span>
                <span className={`text-xs ${
                  file.change_type === 'added' ? 'text-green-400' :
                  file.change_type === 'deleted' ? 'text-red-400' :
                  'text-amber-400'
                }`}>
                  {file.change_type === 'added' ? 'nouveau' :
                   file.change_type === 'deleted' ? 'supprimé' :
                   'modifié'}
                </span>
              </button>

              {expandedFile === file.file_path && file.diff_hunk && (
                <div className="overflow-x-auto bg-[#0a0f1e] px-4 py-2">
                  <pre className="text-xs leading-5">
                    {file.diff_hunk.split('\n').map((line, i) => (
                      <div
                        key={i}
                        style={{
                          backgroundColor:
                            line.startsWith('+') && !line.startsWith('+++')
                              ? 'rgba(34, 197, 94, 0.1)'
                              : line.startsWith('-') && !line.startsWith('---')
                                ? 'rgba(239, 68, 68, 0.1)'
                                : 'transparent',
                          color:
                            line.startsWith('+') && !line.startsWith('+++')
                              ? '#4ade80'
                              : line.startsWith('-') && !line.startsWith('---')
                                ? '#f87171'
                                : '#B6C7DA',
                        }}
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
        <div className="border-t border-white/5 px-4 py-3 text-center text-sm text-[#B6C7DA]">
          {actionDone}
        </div>
      ) : (
        <div className="flex gap-3 border-t border-white/5 px-4 py-3">
          <button
            onClick={handleApprove}
            disabled={actionPending !== null}
            className="flex flex-1 items-center justify-center gap-2 rounded-lg bg-green-500/20 px-4 py-2.5 text-sm font-medium text-green-400 transition hover:bg-green-500/30 disabled:opacity-50"
          >
            <Check size={16} />
            {actionPending === 'approve' ? 'Application...' : 'Appliquer les changements'}
          </button>
          <button
            onClick={handleReject}
            disabled={actionPending !== null}
            className="flex items-center justify-center gap-2 rounded-lg bg-red-500/10 px-4 py-2.5 text-sm font-medium text-red-400 transition hover:bg-red-500/20 disabled:opacity-50"
          >
            <X size={16} />
            {actionPending === 'reject' ? 'Refus...' : 'Refuser'}
          </button>
        </div>
      )}
    </div>
  );
}
