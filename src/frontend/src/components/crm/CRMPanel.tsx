/**
 * THÉRÈSE v2 - CRM Panel (Phase 6)
 *
 * Panel principal CRM avec Pipeline et Activités.
 * Filtre par source pour éviter les doublons.
 * Utilise crmStore avec persistance pour affichage instantané.
 */

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, LayoutDashboard, Users, Activity, UserPlus, Mail, Phone, FileText, Plus, Clock } from 'lucide-react';
import { PipelineView } from './PipelineView';
import { ActivityTimeline } from './ActivityTimeline';
import { useCRMStore } from '../../stores/crmStore';
import { listContacts, listProjects, listActivities, updateContactStage, type ContactResponse, type ActivityResponse } from '../../services/api';
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
  const [showAddActivity, setShowAddActivity] = useState(false);
  const [activityRefreshKey, setActivityRefreshKey] = useState(0);
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
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="text-lg font-semibold text-text-primary">
                    {displaySelectedContact.first_name} {displaySelectedContact.last_name}
                  </h3>
                  {displaySelectedContact.company && (
                    <p className="text-sm text-text-muted">{displaySelectedContact.company}</p>
                  )}
                </div>
                <button
                  onClick={() => setShowAddActivity(true)}
                  className="flex items-center gap-2 px-3 py-2 bg-accent-cyan/10 hover:bg-accent-cyan/20 text-accent-cyan rounded-lg transition-colors text-sm font-medium"
                >
                  <Plus className="w-4 h-4" />
                  Ajouter une activité
                </button>
              </div>

              <ActivityTimeline contactId={selectedContact!.id} key={activityRefreshKey} />

              {showAddActivity && selectedContact && (
                <AddActivityModal
                  contactId={selectedContact.id}
                  onClose={() => setShowAddActivity(false)}
                  onCreated={() => {
                    setShowAddActivity(false);
                    setActivityRefreshKey(prev => prev + 1);
                  }}
                />
              )}
            </motion.div>
          )}

          {activeTab === 'activities' && !selectedContact && (
            <GlobalActivityView contacts={contacts} />
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

// =============================================================================
// GLOBAL ACTIVITY VIEW (no contact selected)
// =============================================================================

const ACTIVITY_FILTER_CHIPS = [
  { id: 'all', label: 'Tous' },
  { id: 'email', label: 'Email', icon: Mail },
  { id: 'call', label: 'Appel', icon: Phone },
  { id: 'meeting', label: 'Réunion', icon: Users },
  { id: 'note', label: 'Note', icon: FileText },
];

const GLOBAL_ACTIVITY_ICONS: Record<string, typeof Mail> = {
  email: Mail,
  call: Phone,
  meeting: Users,
  note: FileText,
};

const GLOBAL_ACTIVITY_COLORS: Record<string, string> = {
  email: 'text-blue-400',
  call: 'text-green-400',
  meeting: 'text-purple-400',
  note: 'text-yellow-400',
};

function GlobalActivityView({ contacts }: { contacts: ContactResponse[] }) {
  const [activities, setActivities] = useState<ActivityResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    loadAllActivities();
  }, []);

  const loadAllActivities = async () => {
    try {
      setLoading(true);
      const data = await listActivities({ limit: 100 });
      setActivities(data);
    } catch (error) {
      console.error('Failed to load global activities:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredActivities = filter === 'all'
    ? activities
    : activities.filter(a => a.type === filter);

  const getContactName = (contactId: string) => {
    const contact = contacts.find(c => c.id === contactId);
    if (!contact) return 'Contact inconnu';
    return `${contact.first_name} ${contact.last_name || ''}`.trim();
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return "À l'instant";
    if (diffMins < 60) return `Il y a ${diffMins}min`;
    if (diffHours < 24) return `Il y a ${diffHours}h`;
    if (diffDays < 7) return `Il y a ${diffDays}j`;

    return date.toLocaleDateString('fr-FR', {
      day: 'numeric',
      month: 'short',
      year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined,
    });
  };

  return (
    <motion.div
      key="activities-global"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      {/* Filter chips */}
      <div className="flex flex-wrap gap-2 mb-6">
        {ACTIVITY_FILTER_CHIPS.map(chip => {
          const isActive = filter === chip.id;
          const ChipIcon = chip.icon;
          return (
            <button
              key={chip.id}
              onClick={() => setFilter(chip.id)}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-accent-cyan/20 text-accent-cyan'
                  : 'bg-surface text-text-muted hover:bg-surface-elevated'
              }`}
            >
              {ChipIcon && <ChipIcon className="w-3.5 h-3.5" />}
              {chip.label}
            </button>
          );
        })}
      </div>

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent-cyan"></div>
        </div>
      )}

      {/* Empty state */}
      {!loading && filteredActivities.length === 0 && (
        <div className="flex items-center justify-center py-12 text-text-muted">
          <div className="text-center">
            <Clock className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>{filter === 'all' ? 'Aucune activité enregistrée' : `Aucune activité de type "${ACTIVITY_FILTER_CHIPS.find(c => c.id === filter)?.label}"`}</p>
            <p className="text-xs mt-1">Cliquez sur un contact dans le Pipeline pour ajouter une activité</p>
          </div>
        </div>
      )}

      {/* Timeline */}
      {!loading && filteredActivities.length > 0 && (
        <div className="space-y-3">
          {filteredActivities.map((activity, index) => {
            const Icon = GLOBAL_ACTIVITY_ICONS[activity.type] || FileText;
            const color = GLOBAL_ACTIVITY_COLORS[activity.type] || 'text-text-muted';
            const contactName = getContactName(activity.contact_id);

            return (
              <motion.div
                key={activity.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.03 }}
                className="flex gap-3 items-start"
              >
                <div className={`${color} bg-surface rounded-full p-2 mt-0.5 shrink-0`}>
                  <Icon className="w-4 h-4" />
                </div>

                <div className="flex-1 bg-surface rounded-lg p-3">
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 mb-0.5">
                        <span className="text-xs font-medium text-accent-cyan">{contactName}</span>
                        <span className="text-xs text-text-muted">·</span>
                        <span className="text-xs text-text-muted capitalize">{
                          activity.type === 'email' ? 'Email' :
                          activity.type === 'call' ? 'Appel' :
                          activity.type === 'meeting' ? 'Réunion' :
                          activity.type === 'note' ? 'Note' :
                          activity.type === 'stage_change' ? 'Changement de stage' :
                          activity.type
                        }</span>
                      </div>
                      <h4 className="text-sm font-medium text-text-primary">{activity.title}</h4>
                      {activity.description && (
                        <p className="text-xs text-text-muted mt-1 line-clamp-2">{activity.description}</p>
                      )}
                    </div>
                    <span className="text-xs text-text-muted whitespace-nowrap shrink-0">
                      {formatDate(activity.created_at)}
                    </span>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      )}
    </motion.div>
  );
}

// =============================================================================
// ADD ACTIVITY MODAL
// =============================================================================

const ACTIVITY_TYPES = [
  { id: 'email', label: 'Email', icon: Mail },
  { id: 'call', label: 'Appel', icon: Phone },
  { id: 'meeting', label: 'Réunion', icon: Users },
  { id: 'note', label: 'Note', icon: FileText },
];

interface AddActivityModalProps {
  contactId: string;
  onClose: () => void;
  onCreated: () => void;
}

function AddActivityModal({ contactId, onClose, onCreated }: AddActivityModalProps) {
  const [type, setType] = useState('note');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    setSubmitting(true);
    try {
      const { createActivity } = await import('../../services/api');
      await createActivity({
        contact_id: contactId,
        type,
        title: title.trim(),
        description: description.trim() || undefined,
      });
      onCreated();
    } catch (error) {
      console.error('Failed to create activity:', error);
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
          <h3 className="text-lg font-semibold text-text-primary">Nouvelle activité</h3>
          <button onClick={onClose} className="p-1 hover:bg-background rounded-lg transition-colors">
            <X className="w-5 h-5 text-text-muted" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs text-text-muted mb-2">Type</label>
            <div className="flex gap-2">
              {ACTIVITY_TYPES.map(at => {
                const AtIcon = at.icon;
                const isActive = type === at.id;
                return (
                  <button
                    key={at.id}
                    type="button"
                    onClick={() => setType(at.id)}
                    className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-accent-cyan/20 text-accent-cyan'
                        : 'bg-background text-text-muted hover:bg-background/80'
                    }`}
                  >
                    <AtIcon className="w-4 h-4" />
                    {at.label}
                  </button>
                );
              })}
            </div>
          </div>

          <div>
            <label className="block text-xs text-text-muted mb-1">Titre *</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Ex: Appel de suivi, Envoi devis..."
              className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:ring-2 focus:ring-accent-cyan outline-none"
              required
            />
          </div>

          <div>
            <label className="block text-xs text-text-muted mb-1">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Détails de l'activité..."
              rows={3}
              className="w-full px-3 py-2 bg-background border border-border rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:ring-2 focus:ring-accent-cyan outline-none resize-none"
            />
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
              disabled={!title.trim() || submitting}
              className="px-4 py-2 text-sm font-medium bg-accent-cyan text-background rounded-lg hover:bg-accent-cyan/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {submitting ? 'Ajout...' : 'Ajouter'}
            </button>
          </div>
        </form>
      </motion.div>
    </div>
  );
}
