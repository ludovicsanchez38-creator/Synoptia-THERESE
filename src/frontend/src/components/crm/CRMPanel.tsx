/**
 * THÉRÈSE v2 - CRM Panel (Phase 5)
 *
 * Panel principal CRM avec Pipeline, Activities et Dashboard.
 */

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, LayoutDashboard, Users, Activity } from 'lucide-react';
import { PipelineView } from './PipelineView';
import { ActivityTimeline } from './ActivityTimeline';
import { listContacts, updateContactStage, type ContactResponse } from '../../services/api';

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

  const effectiveOpen = standalone || isOpen;

  useEffect(() => {
    if (effectiveOpen) {
      loadContacts();
    }
  }, [effectiveOpen]);

  const loadContacts = async () => {
    try {
      setLoading(true);
      const data = await listContacts(0, 200);
      setContacts(data as ContactResponse[]);
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

  const tabs = [
    { id: 'pipeline' as Tab, label: 'Pipeline', icon: LayoutDashboard },
    { id: 'activities' as Tab, label: 'Activités', icon: Activity },
    { id: 'dashboard' as Tab, label: 'Dashboard', icon: Users },
  ];

  const crmHeader = (
    <div className="flex items-center justify-between p-6 border-b border-surface">
      <div>
        <h2 className="text-2xl font-bold text-text-primary">CRM Pipeline</h2>
        <p className="text-sm text-text-muted">Gestion du pipeline commercial</p>
      </div>

      {!standalone && (
        <button
          onClick={onClose}
          className="p-2 hover:bg-surface rounded-lg transition-colors"
        >
          <X className="w-5 h-5 text-text-muted" />
        </button>
      )}
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
                contacts={contacts}
                onContactClick={handleContactClick}
                onStageChange={handleStageChange}
              />
            </motion.div>
          )}

          {activeTab === 'activities' && selectedContact && (
            <motion.div
              key="activities"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
            >
              <div className="mb-6">
                <h3 className="text-lg font-semibold text-text-primary">
                  {selectedContact.first_name} {selectedContact.last_name}
                </h3>
                {selectedContact.company && (
                  <p className="text-sm text-text-muted">{selectedContact.company}</p>
                )}
              </div>

              <ActivityTimeline contactId={selectedContact.id} />
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
              key="dashboard"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
              className="flex items-center justify-center h-full text-text-muted"
            >
              <div className="text-center">
                <Users className="w-16 h-16 mx-auto mb-4 opacity-50" />
                <p>Dashboard en cours de développement</p>
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
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
