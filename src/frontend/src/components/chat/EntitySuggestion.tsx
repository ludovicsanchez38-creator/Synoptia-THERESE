/**
 * THERESE v2 - Entity Suggestion Component
 *
 * Displays detected entities and offers to save them to memory.
 */

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { UserPlus, FolderPlus, Check, X, Loader2 } from 'lucide-react';
import type { ExtractedContact, ExtractedProject } from '../../services/api';
import * as api from '../../services/api';

interface EntitySuggestionProps {
  contacts: ExtractedContact[];
  projects: ExtractedProject[];
  messageId: string;
  onDismiss: () => void;
  onSaved: () => void;
}

interface EntityItemProps {
  type: 'contact' | 'project';
  name: string;
  subtitle?: string;
  confidence: number;
  onSave: () => Promise<void>;
  onIgnore: () => void;
}

function EntityItem({ type, name, subtitle, confidence, onSave, onIgnore }: EntityItemProps) {
  const [status, setStatus] = useState<'idle' | 'saving' | 'saved' | 'ignored'>('idle');

  const handleSave = async () => {
    setStatus('saving');
    try {
      await onSave();
      setStatus('saved');
    } catch (error) {
      console.error('Failed to save entity:', error);
      setStatus('idle');
    }
  };

  const handleIgnore = () => {
    setStatus('ignored');
    onIgnore();
  };

  if (status === 'saved' || status === 'ignored') {
    return null;
  }

  const Icon = type === 'contact' ? UserPlus : FolderPlus;
  const confidencePercent = Math.round(confidence * 100);

  return (
    <motion.div
      initial={{ opacity: 0, x: -10 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 10 }}
      className="flex items-center gap-3 px-3 py-2 rounded-lg bg-[#1a2444] border border-[#2a3654]"
    >
      <div className="flex-shrink-0">
        <div className={`p-1.5 rounded-md ${type === 'contact' ? 'bg-cyan-500/20' : 'bg-magenta-500/20'}`}>
          <Icon className={`w-4 h-4 ${type === 'contact' ? 'text-cyan-400' : 'text-[#E11D8D]'}`} />
        </div>
      </div>

      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-[#E6EDF7] truncate">{name}</p>
        {subtitle && (
          <p className="text-xs text-[#B6C7DA] truncate">{subtitle}</p>
        )}
      </div>

      <div className="flex items-center gap-1.5">
        <span className="text-xs text-[#B6C7DA]/60">{confidencePercent}%</span>

        {status === 'saving' ? (
          <Loader2 className="w-4 h-4 text-cyan-400 animate-spin" />
        ) : (
          <>
            <button
              onClick={handleSave}
              className="p-1 rounded hover:bg-cyan-500/20 text-cyan-400 transition-colors"
              title="Sauvegarder"
            >
              <Check className="w-4 h-4" />
            </button>
            <button
              onClick={handleIgnore}
              className="p-1 rounded hover:bg-red-500/20 text-[#B6C7DA] hover:text-red-400 transition-colors"
              title="Ignorer"
            >
              <X className="w-4 h-4" />
            </button>
          </>
        )}
      </div>
    </motion.div>
  );
}

export function EntitySuggestion({
  contacts,
  projects,
  messageId: _messageId,
  onDismiss,
  onSaved,
}: EntitySuggestionProps) {
  // Note: messageId is passed for future use (e.g., tracking which message triggered suggestions)
  void _messageId;
  const [remainingContacts, setRemainingContacts] = useState(contacts);
  const [remainingProjects, setRemainingProjects] = useState(projects);

  const handleSaveContact = async (contact: ExtractedContact) => {
    // Parse name into first/last
    const nameParts = contact.name.trim().split(' ');
    const firstName = nameParts[0] || '';
    const lastName = nameParts.slice(1).join(' ') || null;

    await api.createContact({
      first_name: firstName,
      last_name: lastName,
      company: contact.company,
      email: contact.email,
      phone: contact.phone,
      notes: contact.role ? `Role: ${contact.role}` : null,
    });

    setRemainingContacts((prev) => prev.filter((c) => c.name !== contact.name));
    onSaved();
  };

  const handleSaveProject = async (project: ExtractedProject) => {
    await api.createProject({
      name: project.name,
      description: project.description,
      budget: project.budget,
      status: (project.status as 'active' | 'completed' | 'on_hold') || 'active',
    });

    setRemainingProjects((prev) => prev.filter((p) => p.name !== project.name));
    onSaved();
  };

  const handleIgnoreContact = (name: string) => {
    setRemainingContacts((prev) => prev.filter((c) => c.name !== name));
  };

  const handleIgnoreProject = (name: string) => {
    setRemainingProjects((prev) => prev.filter((p) => p.name !== name));
  };

  // Check if all items have been handled
  const allHandled = remainingContacts.length === 0 && remainingProjects.length === 0;

  if (allHandled) {
    return null;
  }

  const totalCount = remainingContacts.length + remainingProjects.length;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10, height: 0 }}
      animate={{ opacity: 1, y: 0, height: 'auto' }}
      exit={{ opacity: 0, y: -10, height: 0 }}
      transition={{ duration: 0.2, ease: 'easeOut' }}
      className="mt-2 ml-10 overflow-hidden"
    >
      <div className="p-3 rounded-xl bg-[#131B35] border border-[#2a3654]/50">
        {/* Header */}
        <div className="flex items-center justify-between mb-2">
          <p className="text-xs font-medium text-[#B6C7DA]">
            {totalCount === 1 ? "J'ai detecte une entite" : `J'ai detecte ${totalCount} entites`}
          </p>
          <button
            onClick={onDismiss}
            className="text-xs text-[#B6C7DA]/60 hover:text-[#B6C7DA] transition-colors"
          >
            Tout ignorer
          </button>
        </div>

        {/* Entity List */}
        <div className="space-y-2">
          <AnimatePresence mode="popLayout">
            {remainingContacts.map((contact) => (
              <EntityItem
                key={`contact-${contact.name}`}
                type="contact"
                name={contact.name}
                subtitle={contact.company || contact.role || undefined}
                confidence={contact.confidence}
                onSave={() => handleSaveContact(contact)}
                onIgnore={() => handleIgnoreContact(contact.name)}
              />
            ))}
            {remainingProjects.map((project) => (
              <EntityItem
                key={`project-${project.name}`}
                type="project"
                name={project.name}
                subtitle={project.description || (project.budget ? `${project.budget} EUR` : undefined)}
                confidence={project.confidence}
                onSave={() => handleSaveProject(project)}
                onIgnore={() => handleIgnoreProject(project.name)}
              />
            ))}
          </AnimatePresence>
        </div>
      </div>
    </motion.div>
  );
}
