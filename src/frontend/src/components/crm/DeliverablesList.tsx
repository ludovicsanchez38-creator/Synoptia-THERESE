/**
 * THÉRÈSE v2 - Deliverables List (CRM Phase 5)
 *
 * Liste des livrables d'un projet avec gestion du statut.
 */

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Package, Calendar, CheckCircle2, Circle, Clock, AlertCircle } from 'lucide-react';
import { listDeliverables, type DeliverableResponse } from '../../services/api';

interface DeliverablesListProps {
  projectId: string;
}

const DELIVERABLE_STATUS = {
  a_faire: { label: 'À faire', icon: Circle, color: 'text-gray-400' },
  en_cours: { label: 'En cours', icon: Clock, color: 'text-blue-400' },
  en_revision: { label: 'En révision', icon: AlertCircle, color: 'text-yellow-400' },
  valide: { label: 'Validé', icon: CheckCircle2, color: 'text-green-400' },
};

export function DeliverablesList({ projectId }: DeliverablesListProps) {
  const [deliverables, setDeliverables] = useState<DeliverableResponse[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDeliverables();
  }, [projectId]);

  const loadDeliverables = async () => {
    try {
      setLoading(true);
      const data = await listDeliverables({ project_id: projectId });
      setDeliverables(data);
    } catch (error) {
      console.error('Failed to load deliverables:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return null;
    const date = new Date(dateStr);
    return date.toLocaleDateString('fr-FR', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    });
  };

  const getProgress = () => {
    if (deliverables.length === 0) return 0;
    const completed = deliverables.filter(d => d.status === 'valide').length;
    return Math.round((completed / deliverables.length) * 100);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent-cyan"></div>
      </div>
    );
  }

  if (deliverables.length === 0) {
    return (
      <div className="text-center py-8 text-text-muted">
        <Package className="w-12 h-12 mx-auto mb-3 opacity-50" />
        <p>Aucun livrable pour ce projet</p>
      </div>
    );
  }

  const progress = getProgress();

  return (
    <div className="space-y-4">
      {/* Progress bar */}
      <div className="bg-surface rounded-lg p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-text-primary">Progression</span>
          <span className="text-sm font-semibold text-accent-cyan">{progress}%</span>
        </div>
        <div className="w-full bg-background rounded-full h-2">
          <div
            className="bg-gradient-to-r from-accent-cyan to-accent-magenta h-2 rounded-full transition-all duration-300"
            style={{ width: `${progress}%` }}
          ></div>
        </div>
      </div>

      {/* Deliverables list */}
      {deliverables.map((deliverable, index) => {
        const statusInfo = DELIVERABLE_STATUS[deliverable.status as keyof typeof DELIVERABLE_STATUS];
        const Icon = statusInfo.icon;

        return (
          <motion.div
            key={deliverable.id}
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
            className="bg-surface rounded-lg p-4 hover:bg-background transition-colors"
          >
            <div className="flex items-start gap-3">
              <Icon className={`w-5 h-5 mt-0.5 ${statusInfo.color}`} />

              <div className="flex-1">
                <div className="flex items-start justify-between mb-1">
                  <h4 className="font-medium text-text-primary">{deliverable.title}</h4>
                  <span className={`text-xs px-2 py-1 rounded ${statusInfo.color} bg-surface`}>
                    {statusInfo.label}
                  </span>
                </div>

                {deliverable.description && (
                  <p className="text-sm text-text-muted mb-2">{deliverable.description}</p>
                )}

                <div className="flex items-center gap-4 text-xs text-text-muted">
                  {deliverable.due_date && (
                    <div className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      <span>Échéance: {formatDate(deliverable.due_date)}</span>
                    </div>
                  )}

                  {deliverable.completed_at && (
                    <div className="flex items-center gap-1 text-green-400">
                      <CheckCircle2 className="w-3 h-3" />
                      <span>Complété: {formatDate(deliverable.completed_at)}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </motion.div>
        );
      })}
    </div>
  );
}
