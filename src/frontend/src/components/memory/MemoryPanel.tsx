import { useState, useEffect } from 'react';
import { X, Users, Plus, Search, ChevronRight, FolderOpen, Trash2, AlertCircle, Shield, Download, UserX, RefreshCw } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from '../ui/Button';
import { sidebarVariants, overlayVariants } from '../../lib/animations';
import { FileBrowser } from '../files/FileBrowser';
import * as api from '../../services/api';
import type { MemoryScope, RGPDStatsResponse } from '../../services/api';
import { useDemoMask } from '../../hooks';

interface MemoryPanelProps {
  isOpen: boolean;
  onClose: () => void;
  onNewContact?: () => void;
  onEditContact?: (contact: api.Contact) => void;
}

type Tab = 'contacts' | 'files';

export function MemoryPanel({ isOpen, onClose, onNewContact, onEditContact }: MemoryPanelProps) {
  const [activeTab, setActiveTab] = useState<Tab>('contacts');
  const [contacts, setContacts] = useState<api.Contact[]>([]);
  const [indexedFiles, setIndexedFiles] = useState<api.FileMetadata[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  // E3-05: Scope filter state
  const [scopeFilter, setScopeFilter] = useState<MemoryScope | 'all'>('all');
  // E3-06: Delete state
  const [deleteConfirm, setDeleteConfirm] = useState<{ type: 'contact'; id: string; name: string } | null>(null);
  const [deleting, setDeleting] = useState(false);

  // RGPD state (Phase 6)
  const [rgpdStats, setRgpdStats] = useState<RGPDStatsResponse | null>(null);
  const [rgpdAction, setRgpdAction] = useState<{
    type: 'export' | 'anonymize' | 'renew';
    contact: api.Contact;
  } | null>(null);
  const [rgpdActionLoading, setRgpdActionLoading] = useState(false);
  const [anonymizeReason, setAnonymizeReason] = useState('');
  const { enabled: demoEnabled, maskContact, populateMap } = useDemoMask();

  // Load data when panel opens or scope changes
  useEffect(() => {
    if (isOpen) {
      loadData();
    }
  }, [isOpen, scopeFilter]);

  async function loadData() {
    setLoading(true);
    try {
      // E3-05: Apply scope filter
      const scopeParams: api.ScopeFilter | undefined = scopeFilter !== 'all'
        ? { scope: scopeFilter as MemoryScope }
        : undefined;

      const [contactsData, filesData, rgpdStatsData] = await Promise.all([
        api.listContactsWithScope(0, 50, scopeParams),
        api.listFiles(),
        api.getRGPDStats().catch(() => null), // RGPD stats (fail silently)
      ]);
      setContacts(contactsData);
      setIndexedFiles(filesData);
      setRgpdStats(rgpdStatsData);
      // Peupler la map de remplacement pour le mode démo
      populateMap(contactsData, []);
    } catch (error) {
      console.error('Failed to load memory data:', error);
    } finally {
      setLoading(false);
    }
  }

  // RGPD action handlers
  async function handleRGPDExport(contact: api.Contact) {
    setRgpdActionLoading(true);
    try {
      const data = await api.exportContactRGPD(contact.id);
      // Download as JSON file
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `rgpd-export-${contact.first_name || 'contact'}-${contact.id.slice(0, 8)}.json`;
      a.click();
      URL.revokeObjectURL(url);
      setRgpdAction(null);
    } catch (error) {
      console.error('RGPD export failed:', error);
      alert('Erreur lors de l\'export RGPD');
    } finally {
      setRgpdActionLoading(false);
    }
  }

  async function handleRGPDAnonymize(contact: api.Contact, reason: string) {
    if (!reason.trim()) {
      alert('Veuillez indiquer la raison de l\'anonymisation');
      return;
    }
    setRgpdActionLoading(true);
    try {
      await api.anonymizeContact(contact.id, reason);
      setRgpdAction(null);
      setAnonymizeReason('');
      await loadData(); // Reload to show anonymized contact
    } catch (error) {
      console.error('RGPD anonymize failed:', error);
      alert('Erreur lors de l\'anonymisation');
    } finally {
      setRgpdActionLoading(false);
    }
  }

  async function handleRGPDRenewConsent(contact: api.Contact) {
    setRgpdActionLoading(true);
    try {
      const result = await api.renewContactConsent(contact.id);
      alert(`Consentement renouvelé jusqu'au ${new Date(result.new_expiration).toLocaleDateString('fr-FR')}`);
      setRgpdAction(null);
      await loadData(); // Reload to show updated expiration
    } catch (error) {
      console.error('RGPD renew consent failed:', error);
      alert('Erreur lors du renouvellement du consentement');
    } finally {
      setRgpdActionLoading(false);
    }
  }

  // E3-06: Delete handlers
  async function handleDelete() {
    if (!deleteConfirm) return;

    setDeleting(true);
    try {
      await api.deleteContactWithCascade(deleteConfirm.id, true);
      setContacts(prev => prev.filter(c => c.id !== deleteConfirm.id));
      setDeleteConfirm(null);
    } catch (error) {
      console.error('Failed to delete:', error);
    } finally {
      setDeleting(false);
    }
  }

  // Filter data based on search
  const filteredContacts = contacts.filter(c => {
    const searchLower = searchQuery.toLowerCase();
    return (
      c.first_name?.toLowerCase().includes(searchLower) ||
      c.last_name?.toLowerCase().includes(searchLower) ||
      c.company?.toLowerCase().includes(searchLower) ||
      c.email?.toLowerCase().includes(searchLower)
    );
  });

  // Mode démo : masquer les contacts affichés
  const displayContacts = demoEnabled ? filteredContacts.map(c => maskContact(c)) : filteredContacts;

  // Handle file indexed from browser
  const handleFileIndexed = (metadata: api.FileMetadata) => {
    setIndexedFiles(prev => {
      // Update if exists, add if new
      const exists = prev.find(f => f.id === metadata.id);
      if (exists) {
        return prev.map(f => f.id === metadata.id ? metadata : f);
      }
      return [metadata, ...prev];
    });
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            variants={overlayVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            transition={{ duration: 0.2 }}
            className="fixed inset-0 bg-black/40 backdrop-blur-sm z-40"
            onClick={onClose}
          />

          {/* Panel */}
          <motion.div
            variants={sidebarVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            className="fixed right-0 top-0 bottom-0 w-[420px] bg-surface border-l border-border z-50 flex flex-col shadow-2xl"
          >
            {/* Header */}
            <div className="h-14 flex items-center justify-between px-4 border-b border-border/50">
              <h2 className="text-lg font-semibold text-text">Mémoire</h2>
              <Button variant="ghost" size="icon" onClick={onClose}>
                <X className="w-5 h-5" />
              </Button>
            </div>

            {/* Tabs */}
            <div className="flex border-b border-border/50">
              <button
                onClick={() => setActiveTab('contacts')}
                className={`flex-1 flex items-center justify-center gap-2 py-3 text-sm font-medium transition-colors ${
                  activeTab === 'contacts'
                    ? 'text-accent-cyan border-b-2 border-accent-cyan'
                    : 'text-text-muted hover:text-text'
                }`}
              >
                <Users className="w-4 h-4" />
                Contacts ({contacts.length})
              </button>
              <button
                onClick={() => setActiveTab('files')}
                className={`flex-1 flex items-center justify-center gap-2 py-3 text-sm font-medium transition-colors ${
                  activeTab === 'files'
                    ? 'text-accent-cyan border-b-2 border-accent-cyan'
                    : 'text-text-muted hover:text-text'
                }`}
              >
                <FolderOpen className="w-4 h-4" />
                Fichiers ({indexedFiles.length})
              </button>
            </div>

            {/* Search + Scope Filter - only for contacts */}
            {activeTab === 'contacts' && (
              <div className="p-3 border-b border-border/30 space-y-2">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
                  <input
                    type="text"
                    placeholder="Rechercher..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full pl-10 pr-4 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted focus:outline-none focus:border-accent-cyan/50 transition-colors"
                  />
                </div>
                {/* E3-05: Scope filter pills */}
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
            )}

            {/* RGPD Alert Banner */}
            {activeTab === 'contacts' && rgpdStats && rgpdStats.expires_ou_bientot > 0 && (
              <div className="mx-3 mt-3 p-2.5 rounded-lg bg-orange-500/10 border border-orange-500/30">
                <div className="flex items-center gap-2 text-sm text-orange-400">
                  <Shield className="w-4 h-4 flex-shrink-0" />
                  <span>
                    <strong>{rgpdStats.expires_ou_bientot}</strong> contact{rgpdStats.expires_ou_bientot > 1 ? 's' : ''} RGPD expire{rgpdStats.expires_ou_bientot > 1 ? 'nt' : ''} bientot
                  </span>
                </div>
              </div>
            )}

            {/* Content */}
            <div className="flex-1 overflow-y-auto">
              {loading ? (
                <div className="flex items-center justify-center h-32">
                  <div className="w-6 h-6 border-2 border-accent-cyan border-t-transparent rounded-full animate-spin" />
                </div>
              ) : activeTab === 'contacts' ? (
                <ContactsList
                  contacts={displayContacts}
                  onSelect={(c) => onEditContact?.(c)}
                  onDelete={(c) => setDeleteConfirm({
                    type: 'contact',
                    id: c.id,
                    name: [c.first_name, c.last_name].filter(Boolean).join(' ') || c.company || 'Contact'
                  })}
                  onRGPDAction={(type, contact) => setRgpdAction({ type, contact })}
                />
              ) : (
                <FileBrowser
                  onFileIndex={handleFileIndexed}
                  onFileSelect={(f) => console.log('Selected file:', f)}
                />
              )}
            </div>

            {/* E3-06: Delete confirmation modal */}
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
                        <h3 className="text-base font-semibold text-text">Supprimer le contact ?</h3>
                        <p className="text-sm text-text-muted">{deleteConfirm.name}</p>
                      </div>
                    </div>
                    <p className="text-sm text-text-muted mb-4">
                      Les projets et fichiers associés seront aussi supprimés.
                    </p>
                    <div className="flex gap-2">
                      <Button
                        variant="ghost"
                        className="flex-1"
                        onClick={() => setDeleteConfirm(null)}
                        disabled={deleting}
                      >
                        Annuler
                      </Button>
                      <Button
                        variant="primary"
                        className="flex-1 bg-red-500 hover:bg-red-600"
                        onClick={handleDelete}
                        disabled={deleting}
                      >
                        {deleting ? (
                          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        ) : (
                          <>
                            <Trash2 className="w-4 h-4 mr-2" />
                            Supprimer
                          </>
                        )}
                      </Button>
                    </div>
                  </motion.div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* RGPD Action Modal (Phase 6) */}
            <AnimatePresence>
              {rgpdAction && (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="absolute inset-0 bg-black/60 flex items-center justify-center p-4 z-10"
                  onClick={() => { setRgpdAction(null); setAnonymizeReason(''); }}
                >
                  <motion.div
                    initial={{ scale: 0.95, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    exit={{ scale: 0.95, opacity: 0 }}
                    className="bg-surface border border-border rounded-xl p-5 w-full max-w-sm shadow-xl"
                    onClick={(e) => e.stopPropagation()}
                  >
                    {rgpdAction.type === 'export' && (
                      <>
                        <div className="flex items-center gap-3 mb-4">
                          <div className="w-10 h-10 rounded-full bg-accent-cyan/20 flex items-center justify-center">
                            <Download className="w-5 h-5 text-accent-cyan" />
                          </div>
                          <div>
                            <h3 className="text-base font-semibold text-text">Export RGPD</h3>
                            <p className="text-sm text-text-muted">Droit de portabilite (Art. 20)</p>
                          </div>
                        </div>
                        <p className="text-sm text-text-muted mb-4">
                          Exporter toutes les donnees de <strong>{rgpdAction.contact.first_name} {rgpdAction.contact.last_name}</strong> au format JSON.
                        </p>
                        <div className="flex gap-2">
                          <Button variant="ghost" className="flex-1" onClick={() => setRgpdAction(null)}>
                            Annuler
                          </Button>
                          <Button
                            variant="primary"
                            className="flex-1"
                            onClick={() => handleRGPDExport(rgpdAction.contact)}
                            disabled={rgpdActionLoading}
                          >
                            {rgpdActionLoading ? (
                              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                            ) : (
                              <>
                                <Download className="w-4 h-4 mr-2" />
                                Exporter
                              </>
                            )}
                          </Button>
                        </div>
                      </>
                    )}

                    {rgpdAction.type === 'anonymize' && (
                      <>
                        <div className="flex items-center gap-3 mb-4">
                          <div className="w-10 h-10 rounded-full bg-red-500/20 flex items-center justify-center">
                            <UserX className="w-5 h-5 text-red-400" />
                          </div>
                          <div>
                            <h3 className="text-base font-semibold text-text">Anonymisation RGPD</h3>
                            <p className="text-sm text-text-muted">Droit a l'oubli (Art. 17)</p>
                          </div>
                        </div>
                        <p className="text-sm text-text-muted mb-3">
                          Cette action est <strong>irreversible</strong>. Toutes les donnees personnelles seront remplacees par [ANONYMISE].
                        </p>
                        <div className="mb-4">
                          <label className="block text-sm font-medium text-text mb-1">Raison de l'anonymisation *</label>
                          <input
                            type="text"
                            value={anonymizeReason}
                            onChange={(e) => setAnonymizeReason(e.target.value)}
                            placeholder="Ex: Demande du contact, fin de relation..."
                            className="w-full px-3 py-2 bg-background/60 border border-border/50 rounded-lg text-sm text-text placeholder:text-text-muted/50 focus:outline-none focus:border-red-400/50"
                          />
                        </div>
                        <div className="flex gap-2">
                          <Button variant="ghost" className="flex-1" onClick={() => { setRgpdAction(null); setAnonymizeReason(''); }}>
                            Annuler
                          </Button>
                          <Button
                            variant="primary"
                            className="flex-1 bg-red-500 hover:bg-red-600"
                            onClick={() => handleRGPDAnonymize(rgpdAction.contact, anonymizeReason)}
                            disabled={rgpdActionLoading || !anonymizeReason.trim()}
                          >
                            {rgpdActionLoading ? (
                              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                            ) : (
                              <>
                                <UserX className="w-4 h-4 mr-2" />
                                Anonymiser
                              </>
                            )}
                          </Button>
                        </div>
                      </>
                    )}

                    {rgpdAction.type === 'renew' && (
                      <>
                        <div className="flex items-center gap-3 mb-4">
                          <div className="w-10 h-10 rounded-full bg-green-500/20 flex items-center justify-center">
                            <RefreshCw className="w-5 h-5 text-green-400" />
                          </div>
                          <div>
                            <h3 className="text-base font-semibold text-text">Renouveler le consentement</h3>
                            <p className="text-sm text-text-muted">Prolonger de 3 ans</p>
                          </div>
                        </div>
                        <p className="text-sm text-text-muted mb-4">
                          Le consentement de <strong>{rgpdAction.contact.first_name} {rgpdAction.contact.last_name}</strong> sera prolonge de 3 ans a partir d'aujourd'hui.
                        </p>
                        <div className="flex gap-2">
                          <Button variant="ghost" className="flex-1" onClick={() => setRgpdAction(null)}>
                            Annuler
                          </Button>
                          <Button
                            variant="primary"
                            className="flex-1 bg-green-500 hover:bg-green-600"
                            onClick={() => handleRGPDRenewConsent(rgpdAction.contact)}
                            disabled={rgpdActionLoading}
                          >
                            {rgpdActionLoading ? (
                              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                            ) : (
                              <>
                                <RefreshCw className="w-4 h-4 mr-2" />
                                Renouveler
                              </>
                            )}
                          </Button>
                        </div>
                      </>
                    )}
                  </motion.div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Footer - Add button (contacts only) */}
            {activeTab === 'contacts' && (
              <div className="p-3 border-t border-border/50">
                <Button
                  variant="primary"
                  className="w-full"
                  onClick={onNewContact}
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Nouveau contact
                </Button>
              </div>
            )}
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

// Contacts list component
function ContactsList({
  contacts,
  onSelect,
  onDelete,
  onRGPDAction,
}: {
  contacts: api.Contact[];
  onSelect: (contact: api.Contact) => void;
  onDelete: (contact: api.Contact) => void;
  onRGPDAction: (type: 'export' | 'anonymize' | 'renew', contact: api.Contact) => void;
}) {
  const [openMenuId, setOpenMenuId] = useState<string | null>(null);

  if (contacts.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-32 text-text-muted">
        <Users className="w-8 h-8 mb-2 opacity-50" />
        <p className="text-sm">Aucun contact</p>
      </div>
    );
  }

  return (
    <div className="divide-y divide-border/30">
      {contacts.map((contact) => (
        <div
          key={contact.id}
          className="w-full flex items-center gap-3 p-3 hover:bg-background/40 transition-colors text-left group relative"
        >
          {/* Avatar - clickable */}
          <button
            onClick={() => onSelect(contact)}
            className="flex items-center gap-3 flex-1 min-w-0"
          >
            <div className="w-10 h-10 rounded-full bg-gradient-to-br from-accent-cyan/20 to-accent-magenta/20 flex items-center justify-center text-sm font-medium text-text flex-shrink-0">
              {getInitials(contact.first_name, contact.last_name)}
            </div>

            {/* Info */}
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <p className="text-sm font-medium text-text truncate">
                  {[contact.first_name, contact.last_name].filter(Boolean).join(' ') || 'Sans nom'}
                </p>
                {/* RGPD Badge */}
                <RGPDBadge contact={contact} />
              </div>
              {contact.company && (
                <p className="text-xs text-text-muted truncate">{contact.company}</p>
              )}
              {contact.email && (
                <p className="text-xs text-text-muted/70 truncate">{contact.email}</p>
              )}
            </div>
          </button>

          {/* RGPD Menu + Delete button */}
          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
            {/* RGPD Menu */}
            <div className="relative">
              <button
                onClick={(e) => { e.stopPropagation(); setOpenMenuId(openMenuId === contact.id ? null : contact.id); }}
                className="p-1.5 rounded-md hover:bg-accent-cyan/20 text-text-muted hover:text-accent-cyan transition-colors"
                title="Actions RGPD"
              >
                <Shield className="w-4 h-4" />
              </button>
              {/* Dropdown menu */}
              <AnimatePresence>
                {openMenuId === contact.id && (
                  <motion.div
                    initial={{ opacity: 0, scale: 0.95, y: -5 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95, y: -5 }}
                    className="absolute right-0 top-full mt-1 w-48 bg-surface border border-border rounded-lg shadow-xl z-20 py-1"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <button
                      onClick={() => { onRGPDAction('export', contact); setOpenMenuId(null); }}
                      className="w-full flex items-center gap-2 px-3 py-2 text-sm text-text hover:bg-background/40 transition-colors"
                    >
                      <Download className="w-4 h-4 text-accent-cyan" />
                      Exporter (Art. 20)
                    </button>
                    <button
                      onClick={() => { onRGPDAction('renew', contact); setOpenMenuId(null); }}
                      className="w-full flex items-center gap-2 px-3 py-2 text-sm text-text hover:bg-background/40 transition-colors"
                    >
                      <RefreshCw className="w-4 h-4 text-green-400" />
                      Renouveler consentement
                    </button>
                    <div className="border-t border-border/50 my-1" />
                    <button
                      onClick={() => { onRGPDAction('anonymize', contact); setOpenMenuId(null); }}
                      className="w-full flex items-center gap-2 px-3 py-2 text-sm text-red-400 hover:bg-red-500/10 transition-colors"
                    >
                      <UserX className="w-4 h-4" />
                      Anonymiser (Art. 17)
                    </button>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
            {/* Delete button */}
            <button
              onClick={(e) => { e.stopPropagation(); onDelete(contact); }}
              className="p-1.5 rounded-md hover:bg-red-500/20 text-text-muted hover:text-red-400 transition-colors"
              title="Supprimer"
            >
              <Trash2 className="w-4 h-4" />
            </button>
            <ChevronRight className="w-4 h-4 text-text-muted" />
          </div>
        </div>
      ))}
    </div>
  );
}

// RGPD Badge component
function RGPDBadge({ contact }: { contact: api.Contact }) {
  const baseLegale = contact.rgpd_base_legale;
  const dateExpiration = contact.rgpd_date_expiration;

  if (!baseLegale) {
    return (
      <span className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-yellow-500/20 text-yellow-400" title="RGPD non defini">
        ?
      </span>
    );
  }

  // Check if expiring soon (within 30 days)
  const isExpiringSoon = dateExpiration && new Date(dateExpiration) <= new Date(Date.now() + 30 * 24 * 60 * 60 * 1000);
  const isExpired = dateExpiration && new Date(dateExpiration) < new Date();

  const badgeColors: Record<string, string> = {
    consentement: 'bg-green-500/20 text-green-400',
    contrat: 'bg-blue-500/20 text-blue-400',
    interet_legitime: 'bg-purple-500/20 text-purple-400',
    obligation_legale: 'bg-gray-500/20 text-gray-400',
  };

  const badgeLabels: Record<string, string> = {
    consentement: 'C',
    contrat: 'CT',
    interet_legitime: 'IL',
    obligation_legale: 'OL',
  };

  const fullLabels: Record<string, string> = {
    consentement: 'Consentement',
    contrat: 'Contrat',
    interet_legitime: 'Interet legitime',
    obligation_legale: 'Obligation legale',
  };

  return (
    <span
      className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
        isExpired ? 'bg-red-500/20 text-red-400' :
        isExpiringSoon ? 'bg-orange-500/20 text-orange-400' :
        badgeColors[baseLegale] || 'bg-gray-500/20 text-gray-400'
      }`}
      title={`${fullLabels[baseLegale] || baseLegale}${dateExpiration ? ` - Expire le ${new Date(dateExpiration).toLocaleDateString('fr-FR')}` : ''}`}
    >
      {badgeLabels[baseLegale] || baseLegale?.charAt(0).toUpperCase()}
      {isExpired && '!'}
      {isExpiringSoon && !isExpired && '⚠'}
    </span>
  );
}

// Helper functions
function getInitials(firstName?: string | null, lastName?: string | null): string {
  const first = firstName?.charAt(0)?.toUpperCase() || '';
  const last = lastName?.charAt(0)?.toUpperCase() || '';
  return first + last || '?';
}

