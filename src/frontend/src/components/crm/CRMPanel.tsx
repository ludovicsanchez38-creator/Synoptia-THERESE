/**
 * THÉRÈSE v2 - CRM Panel (Phase 5)
 *
 * Panel principal CRM avec Pipeline, Activities et Dashboard.
 * Filtre par source pour eviter les doublons.
 * Utilise crmStore avec persistance pour affichage instantané.
 */

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, LayoutDashboard, Users, Activity, UserPlus, FolderKanban, Calendar, DollarSign } from 'lucide-react';
import { PipelineView } from './PipelineView';
import { ActivityTimeline } from './ActivityTimeline';
import { useCRMStore } from '../../stores/crmStore';
import { listContacts, listProjects, updateContactStage, type ContactResponse } from '../../services/api';
import { createCRMContact, type CreateCRMContactRequest } from '../../services/api/crm';
import { useDemoMask } from '../../hooks';

interface CRMPanelProps {
  isOpen?: boolean;
  onClose?: () => void;
  standalone?: boolean;
}

export function CRMPanel({ isOpen, onClose, standalone = false }: CRMPanelProps) {
  const {
    contacts,
    projects,
    selectedContactId,
    activeTab,
    setContacts,
    setProjects,
    setSelectedContact,
    updateContact,
    addContact,
    setActiveTab,
  } = useCRMStore();

  const hasCachedContacts = contacts.length > 0;

  const [loading, setLoading] = useState(!hasCachedContacts);
  const [error, setError] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const { enabled: demoEnabled, maskContact, populateMap } = useDemoMask();

  const effectiveOpen = standalone || isOpen;

  const selectedContact = contacts.find((c) => c.id === selectedContactId) || null;

  useEffect(() => {
    if (effectiveOpen) {
      loadContacts();
    }
  }, [effectiveOpen]);

  const loadContacts = async () => {
    try {
      if (!hasCachedContacts) setLoading(true);
      setError(null);
      // Charger contacts et projets en parallèle
      const [contactsData, projectsData] = await Promise.all([
        listContacts(0, 200, { hasSource: true }),
        listProjects(0, 200),
      ]);
      setContacts(contactsData as ContactResponse[]);
      setProjects(projectsData);
      // Peupler la map de remplacement pour le mode démo
      populateMap(contactsData, projectsData);
    } catch (err: any) {
      console.error('Failed to load CRM data:', err);
      if (!hasCachedContacts) {
        setError(err?.message || 'Impossible de charger les données CRM');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleStageChange = async (contactId: string, newStage: string) => {
    try {
      setError(null);
      const updated = await updateContactStage(contactId, newStage);
      updateContact(contactId, updated);
    } catch (err: any) {
      console.error('Failed to update stage:', err);
      setError(err?.message || 'Impossible de mettre à jour le stage');
    }
  };

  const handleContactClick = (contact: ContactResponse) => {
    setSelectedContact(contact.id);
    setActiveTab('activities');
  };

  const handleCreateContact = async (data: CreateCRMContactRequest) => {
    try {
      setError(null);
      const newContact = await createCRMContact(data);
      addContact(newContact);
      setShowCreateForm(false);
    } catch (err: any) {
      console.error('Failed to create contact:', err);
      setError(err?.message || 'Impossible de créer le contact');
    }
  };

  // Contacts masqués pour le mode démo
  const displayContacts = demoEnabled ? contacts.map(c => maskContact(c)) : contacts;
  const displaySelectedContact = selectedContact
    ? (demoEnabled ? maskContact(selectedContact) : selectedContact)
    : null;

  const tabs = [
    { id: 'pipeline' as const, label: 'Pipeline', icon: LayoutDashboard },
    { id: 'activities' as const, label: 'Activités', icon: Activity },
    { id: 'dashboard' as const, label: 'Projets', icon: FolderKanban },
  ];

  if (!effectiveOpen) return null;

  const crmHeader = (
    <div className="flex items-center justify-between p-6 border-b border-surface">
      <div>
        <h2 className="text-2xl font-bold text-text-primary">CRM Pipeline</h2>
        <p className="text-sm text-text-muted">
          {contacts.length} contact{contacts.length > 1 ? 's' : ''} · {projects.length} projet{projects.length > 1 ? 's' : ''}
        </p>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={() => setShowCreateForm(true)}
          className="flex items-center gap-2 px-3 py-2 bg-accent-cyan/10 hover:bg-accent-cyan/20 text-accent-cyan rounded-lg transition-colors text-sm font-medium"
        >
          <UserPlus className="w-4 h-4" />
          Ajouter un contact
        </button>

        {!standalone && (
          <button
            onClick={onClose}
            className="p-2 hover:bg-surface rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-text-muted" />
          </button>
        )}
      </div>
    </div>
  );

  const crmTabs = (
    <div className="flex gap-2 px-6 pt-4 border-b border-surface">
      {tabs.map(tab => {
        const Icon = tab.icon;
        const isActive = activeTab === tab.id;

        return (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`
              flex items-center gap-2 px-4 py-2 rounded-t-lg transition-colors relative
              ${
                isActive
                  ? 'bg-surface text-text-primary'
                  : 'text-text-muted hover:bg-surface/50'
              }
            `}
          >
            <Icon className="w-4 h-4" />
            <span className="font-medium">{tab.label}</span>

            {isActive && (
              <motion.div
                layoutId="activeTab"
                className="absolute bottom-0 left-0 right-0 h-0.5 bg-accent-cyan"
              />
            )}
          </button>
        );
      })}
    </div>
  );

  const crmContent = (
    <div className="flex-1 overflow-auto p-6">
      {error && (
        <div className="mb-4 px-3 py-2 bg-red-500/10 border border-red-500/20 rounded-lg">
          <p className="text-sm text-red-400">{error}</p>
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center h-full">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-accent-cyan"></div>
        </div>
      ) : (
        <AnimatePresence mode="wait">
          {activeTab === 'pipeline' && (
            <motion.div
              key="pipeline"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
            >
              <PipelineView
                contacts={displayContacts}
                onContactClick={handleContactClick}
                onStageChange={handleStageChange}
              />
            </motion.div>
          )}

          {activeTab === 'activities' && displaySelectedContact && (
            <motion.div
              key="activities"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
            >
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-text-primary">
                  {displaySelectedContact.first_name} {displaySelectedContact.last_name}
                </h3>
                {displaySelectedContact.company && (
                  <p className="text-sm text-text-muted">{displaySelectedContact.company}</p>
                )}
              </div>

              <ActivityTimeline contactId={selectedContact!.id} />
            </motion.div>
          )}

          {activeTab === 'activities' && !selectedContact && (
            <motion.div
              key="activities-empty"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex items-center justify-center h-full text-text-muted"
            >
              <div className="text-center">
                <Activity className="w-16 h-16 mx-auto mb-4 opacity-50" />
                <p>Sélectionnez un contact pour voir son activité</p>
              </div>
            </motion.div>
          )}

          {activeTab === 'dashboard' && (
            <motion.div
              key="projects"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
            >
              {projects.length === 0 ? (
                <div className="flex items-center justify-center h-64 text-text-muted">
                  <div className="text-center">
                    <FolderKanban className="w-16 h-16 mx-auto mb-4 opacity-50" />
                    <p>Aucun projet</p>
                  </div>
                </div>
              ) : (
                <div className="grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
                  {projects.map((project) => {
                    const linkedContact = contacts.find((c) => c.id === project.contact_id);
                    return (
                      <div
                        key={project.id}
                        className="bg-background border border-surface hover:border-accent-cyan/50 rounded-lg p-4 transition-colors"
                      >
                        <div className="flex items-start justify-between mb-3">
                          <h4 className="font-semibold text-text-primary text-sm">{project.name}</h4>
                          <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                            project.status === 'active' ? 'bg-green-500/20 text-green-400' :
                            project.status === 'completed' ? 'bg-blue-500/20 text-blue-400' :
                            project.status === 'on_hold' ? 'bg-yellow-500/20 text-yellow-400' :
                            project.status === 'cancelled' ? 'bg-red-500/20 text-red-400' :
                            'bg-gray-500/20 text-gray-400'
                          }`}>
                            {project.status === 'active' ? 'Actif' :
                             project.status === 'completed' ? 'Terminé' :
                             project.status === 'on_hold' ? 'En pause' :
                             project.status === 'cancelled' ? 'Annulé' :
                             project.status}
                          </span>
                        </div>

                        {project.description && (
                          <p className="text-xs text-text-muted mb-3 line-clamp-2">{project.description}</p>
                        )}

                        <div className="space-y-1.5">
                          {linkedContact && (
                            <div className="flex items-center gap-2 text-xs text-text-muted">
                              <Users className="w-3 h-3" />
                              <span>{linkedContact.first_name} {linkedContact.last_name}</span>
                            </div>
                          )}

                          {project.budget != null && project.budget > 0 && (
                            <div className="flex items-center gap-2 text-xs text-text-muted">
                              <DollarSign className="w-3 h-3" />
                              <span>{project.budget.toLocaleString('fr-FR')} €</span>
                            </div>
                          )}

                          <div className="flex items-center gap-2 text-xs text-text-muted">
                            <Calendar className="w-3 h-3" />
                            <span>{new Date(project.created_at).toLocaleDateString('fr-FR')}</span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      )}
    </div>
  );

  // Mode standalone : pleine page
  if (standalone) {
    return (
      <div className="h-full flex flex-col bg-bg">
        {crmHeader}
        {crmTabs}
        {crmContent}

        {showCreateForm && (
          <CreateContactModal
            onClose={() => setShowCreateForm(false)}
            onCreate={handleCreateContact}
          />
        )}
      </div>
    );
  }

  // Mode modal
  return (
    <AnimatePresence>
      {effectiveOpen && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
          />

          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="fixed inset-8 bg-background border border-surface rounded-xl shadow-2xl z-50 flex flex-col"
          >
            {crmHeader}
            {crmTabs}
            {crmContent}

            {showCreateForm && (
              <CreateContactModal
                onClose={() => setShowCreateForm(false)}
                onCreate={handleCreateContact}
              />
            )}
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

// =============================================================================
// CREATE CONTACT MODAL
// =============================================================================

interface CreateContactModalProps {
  onClose: () => void;
  onCreate: (data: CreateCRMContactRequest) => void;
}

const STAGES = [
  { id: 'contact', label: 'Contact' },
  { id: 'discovery', label: 'Découverte' },
  { id: 'proposition', label: 'Proposition' },
  { id: 'signature', label: 'Signature' },
  { id: 'delivery', label: 'Livraison' },
  { id: 'active', label: 'Actif' },
];

function CreateContactModal({ onClose, onCreate }: CreateContactModalProps) {
  const [form, setForm] = useState<CreateCRMContactRequest>({
    first_name: '',
    last_name: '',
    company: '',
    email: '',
    phone: '',
    source: '',
    stage: 'contact',
  });
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.first_name.trim()) return;

    setSubmitting(true);
    try {
      await onCreate(form);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 flex items-center justify-center z-[60]">
      <div className="absolute inset-0 bg-black/30" onClick={onClose} />
      <motion.div
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="relative bg-surface border border-border rounded-xl shadow-2xl p-6 w-full max-w-lg mx-4"
      >
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-text-primary">Nouveau contact</h3>
          <button onClick={onClose} className="p-1 hover:bg-background rounded-lg transition-colors">
            <X className="w-5 h-5 text-text-muted" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-text-muted mb-1">Prénom *</label>
              <input
                type="text"
                value={form.first_name}
                onChange={(e) => setForm(prev => ({ ...prev, first_name: e.target.value }))}
                className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm text-text focus:ring-2 focus:ring-accent-cyan outline-none"
                required
              />
            </div>
            <div>
              <label className="block text-xs text-text-muted mb-1">Nom</label>
              <input
                type="text"
                value={form.last_name || ''}
                onChange={(e) => setForm(prev => ({ ...prev, last_name: e.target.value }))}
                className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm text-text focus:ring-2 focus:ring-accent-cyan outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs text-text-muted mb-1">Entreprise</label>
            <input
              type="text"
              value={form.company || ''}
              onChange={(e) => setForm(prev => ({ ...prev, company: e.target.value }))}
              className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm text-text focus:ring-2 focus:ring-accent-cyan outline-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-text-muted mb-1">Email</label>
              <input
                type="email"
                value={form.email || ''}
                onChange={(e) => setForm(prev => ({ ...prev, email: e.target.value }))}
                className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm text-text focus:ring-2 focus:ring-accent-cyan outline-none"
              />
            </div>
            <div>
              <label className="block text-xs text-text-muted mb-1">Téléphone</label>
              <input
                type="tel"
                value={form.phone || ''}
                onChange={(e) => setForm(prev => ({ ...prev, phone: e.target.value }))}
                className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm text-text focus:ring-2 focus:ring-accent-cyan outline-none"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-text-muted mb-1">Source</label>
              <input
                type="text"
                value={form.source || ''}
                onChange={(e) => setForm(prev => ({ ...prev, source: e.target.value }))}
                placeholder="LinkedIn, Site web..."
                className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:ring-2 focus:ring-accent-cyan outline-none"
              />
            </div>
            <div>
              <label className="block text-xs text-text-muted mb-1">Stage</label>
              <select
                value={form.stage}
                onChange={(e) => setForm(prev => ({ ...prev, stage: e.target.value }))}
                className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm text-text focus:ring-2 focus:ring-accent-cyan outline-none"
              >
                {STAGES.map(s => (
                  <option key={s.id} value={s.id}>{s.label}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm text-text-muted hover:bg-background rounded-lg transition-colors"
            >
              Annuler
            </button>
            <button
              type="submit"
              disabled={!form.first_name.trim() || submitting}
              className="px-4 py-2 text-sm font-medium bg-accent-cyan text-background rounded-lg hover:bg-accent-cyan/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? 'Création...' : 'Créer le contact'}
            </button>
          </div>
        </form>
      </motion.div>
    </div>
  );
}
