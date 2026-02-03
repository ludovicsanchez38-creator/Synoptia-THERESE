/**
 * THÉRÈSE v2 - CRM Panel (Phase 5)
 *
 * Panel principal CRM avec Pipeline, Activities et Dashboard.
 * Filtre par source pour eviter les doublons.
 */

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, LayoutDashboard, Users, Activity, UserPlus } from 'lucide-react';
import { PipelineView } from './PipelineView';
import { ActivityTimeline } from './ActivityTimeline';
import { listContacts, updateContactStage, type ContactResponse } from '../../services/api';
import { createCRMContact, type CreateCRMContactRequest } from '../../services/api/crm';
import { useDemoMask } from '../../hooks';

interface CRMPanelProps {
  isOpen?: boolean;
  onClose?: () => void;
  standalone?: boolean;
}

type Tab = 'pipeline' | 'activities' | 'dashboard';

export function CRMPanel({ isOpen, onClose, standalone = false }: CRMPanelProps) {
  const [activeTab, setActiveTab] = useState<Tab>('pipeline');
  const [contacts, setContacts] = useState<ContactResponse[]>([]);
  const [selectedContact, setSelectedContact] = useState<ContactResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const { enabled: demoEnabled, maskContact, populateMap } = useDemoMask();

  const effectiveOpen = standalone || isOpen;

  useEffect(() => {
    if (effectiveOpen) {
      loadContacts();
    }
  }, [effectiveOpen]);

  const loadContacts = async () => {
    try {
      setLoading(true);
      // Filtrer par has_source=true pour n'afficher que les contacts avec source (GSheets + THERESE)
      const data = await listContacts(0, 200, { hasSource: true });
      setContacts(data as ContactResponse[]);
      // Peupler la map de remplacement pour le mode démo
      populateMap(data, []);
    } catch (error) {
      console.error('Failed to load contacts:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStageChange = async (contactId: string, newStage: string) => {
    try {
      const updated = await updateContactStage(contactId, newStage);
      setContacts(prev => prev.map(c => (c.id === contactId ? updated : c)));
    } catch (error) {
      console.error('Failed to update stage:', error);
    }
  };

  const handleContactClick = (contact: ContactResponse) => {
    setSelectedContact(contact);
    setActiveTab('activities');
  };

  const handleCreateContact = async (data: CreateCRMContactRequest) => {
    try {
      const newContact = await createCRMContact(data);
      setContacts(prev => [newContact, ...prev]);
      setShowCreateForm(false);
    } catch (error) {
      console.error('Failed to create contact:', error);
    }
  };

  // Contacts masqués pour le mode démo
  const displayContacts = demoEnabled ? contacts.map(c => maskContact(c)) : contacts;

  const tabs = [
    { id: 'pipeline' as Tab, label: 'Pipeline', icon: LayoutDashboard },
    { id: 'activities' as Tab, label: 'Activites', icon: Activity },
    { id: 'dashboard' as Tab, label: 'Dashboard', icon: Users },
  ];

  const crmHeader = (
    <div className="flex items-center justify-between p-6 border-b border-surface">
      <div>
        <h2 className="text-2xl font-bold text-text-primary">CRM Pipeline</h2>
        <p className="text-sm text-text-muted">Gestion du pipeline commercial</p>
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

          {activeTab === 'activities' && selectedContact && (() => {
            const displayContact = demoEnabled ? maskContact(selectedContact) : selectedContact;
            return (
            <motion.div
              key="activities"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
            >
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-text-primary">
                  {displayContact.first_name} {displayContact.last_name}
                </h3>
                {displayContact.company && (
                  <p className="text-sm text-text-muted">{displayContact.company}</p>
                )}
              </div>

              <ActivityTimeline contactId={selectedContact.id} />
            </motion.div>
            );
          })()}

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
                <p>Selectionnez un contact pour voir son activite</p>
              </div>
            </motion.div>
          )}

          {activeTab === 'dashboard' && (
            <motion.div
              key="dashboard"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="flex items-center justify-center h-full text-text-muted"
            >
              <div className="text-center">
                <Users className="w-16 h-16 mx-auto mb-4 opacity-50" />
                <p>Dashboard en cours de developpement</p>
              </div>
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
  { id: 'discovery', label: 'Decouverte' },
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
              <label className="block text-xs text-text-muted mb-1">Prenom *</label>
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
              <label className="block text-xs text-text-muted mb-1">Telephone</label>
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
              {submitting ? 'Creation...' : 'Creer le contact'}
            </button>
          </div>
        </form>
      </motion.div>
    </div>
  );
}
