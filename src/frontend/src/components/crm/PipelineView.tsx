/**
 * THÉRÈSE v2 - Pipeline View (CRM Phase 5)
 *
 * Vue Kanban du pipeline commercial avec 7 stages.
 */

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { User, Building2, Mail, Phone, TrendingUp } from 'lucide-react';
import type { ContactResponse } from '../../services/api';

// Les 7 stages du pipeline
const PIPELINE_STAGES = [
  { id: 'contact', label: 'Contact', color: 'bg-gray-500' },
  { id: 'discovery', label: 'Découverte', color: 'bg-blue-500' },
  { id: 'proposition', label: 'Proposition', color: 'bg-purple-500' },
  { id: 'signature', label: 'Signature', color: 'bg-yellow-500' },
  { id: 'delivery', label: 'Livraison', color: 'bg-orange-500' },
  { id: 'active', label: 'Actif', color: 'bg-green-500' },
  { id: 'archive', label: 'Archivé', color: 'bg-gray-400' },
];

interface PipelineViewProps {
  contacts: ContactResponse[];
  onContactClick: (contact: ContactResponse) => void;
  onStageChange: (contactId: string, newStage: string) => void;
}

export function PipelineView({ contacts, onContactClick, onStageChange }: PipelineViewProps) {
  const [contactsByStage, setContactsByStage] = useState<Record<string, ContactResponse[]>>({});

  useEffect(() => {
    // Grouper les contacts par stage
    const grouped = PIPELINE_STAGES.reduce((acc, stage) => {
      acc[stage.id] = contacts.filter(c => c.stage === stage.id);
      return acc;
    }, {} as Record<string, ContactResponse[]>);

    setContactsByStage(grouped);
  }, [contacts]);

  return (
    <div className="flex gap-4 overflow-x-auto pb-4">
      {PIPELINE_STAGES.map((stage) => (
        <div key={stage.id} className="flex-shrink-0 w-72">
          {/* Header colonne */}
          <div className={`${stage.color} text-white rounded-t-lg px-4 py-3`}>
            <div className="flex items-center justify-between">
              <h3 className="font-semibold">{stage.label}</h3>
              <span className="text-sm opacity-80">
                {contactsByStage[stage.id]?.length || 0}
              </span>
            </div>
          </div>

          {/* Cards contacts */}
          <div className="bg-surface border border-surface rounded-b-lg p-2 min-h-[200px] space-y-2">
            <AnimatePresence>
              {contactsByStage[stage.id]?.map((contact) => (
                <motion.div
                  key={contact.id}
                  layout
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -10 }}
                  onClick={() => onContactClick(contact)}
                  className="bg-background border border-surface hover:border-accent-cyan rounded-lg p-3 cursor-pointer transition-colors"
                >
                  {/* Nom */}
                  <div className="flex items-center gap-2 mb-2">
                    <User className="w-4 h-4 text-text-muted" />
                    <span className="font-medium text-sm text-text-primary">
                      {contact.first_name} {contact.last_name}
                    </span>
                  </div>

                  {/* Entreprise */}
                  {contact.company && (
                    <div className="flex items-center gap-2 text-xs text-text-muted mb-1">
                      <Building2 className="w-3 h-3" />
                      <span className="truncate">{contact.company}</span>
                    </div>
                  )}

                  {/* Email */}
                  {contact.email && (
                    <div className="flex items-center gap-2 text-xs text-text-muted mb-1">
                      <Mail className="w-3 h-3" />
                      <span className="truncate">{contact.email}</span>
                    </div>
                  )}

                  {/* Score */}
                  <div className="flex items-center justify-between mt-2 pt-2 border-t border-surface">
                    <div className="flex items-center gap-1 text-xs">
                      <TrendingUp className="w-3 h-3 text-accent-cyan" />
                      <span className="text-text-muted">Score:</span>
                      <span className="font-semibold text-accent-cyan">{contact.score}</span>
                    </div>

                    {contact.source && (
                      <span className="text-xs bg-surface px-2 py-0.5 rounded text-text-muted">
                        {contact.source}
                      </span>
                    )}
                  </div>
                </motion.div>
              ))}
            </AnimatePresence>
          </div>
        </div>
      ))}
    </div>
  );
}
