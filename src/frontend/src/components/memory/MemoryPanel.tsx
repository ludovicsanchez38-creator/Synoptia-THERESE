import { useState, useEffect } from 'react';
import { X, Plus, Search, ChevronRight, Trash2, AlertCircle, Shield, Download, Upload, UserX, RefreshCw, AlertTriangle } from 'lucide-react';
import { Spinner } from '../ui/Spinner';
import { motion, AnimatePresence } from 'framer-motion';
import { Alerte } from '../ui/Alerte';
import { Button } from '../ui/Button';
import { EtatVide } from '../ui/EtatVide';
import { Etiquette } from '../ui/Etiquette';
import { Input } from '../ui/Input';
import { Ligne } from '../ui/Ligne';
import { Squelette } from '../ui/Squelette';
import { CLASSES_SEGMENTS, classeSegment } from '../ui/segments.classes';
import { sidebarVariants, overlayVariants } from '../../lib/animations';
import * as api from '../../services/api';
import type { MemoryScope, RGPDStatsResponse } from '../../services/api';
import { useDemoMask } from '../../hooks';
import { useStatusStore } from '../../stores/statusStore';
import { useContactsStore } from '../../stores/contactsStore';
import { useNavigationStore } from '../../stores/navigationStore';
import { pushEscapeHandler } from '../../lib/escapeStack';
import { Z_LAYER } from '../../styles/z-layers';

const LIBELLES_PERIMETRE: Record<MemoryScope, string> = {
  global: 'Global',
  project: 'Projet',
  conversation: 'Conv.',
};

interface EtatVideContacts {
  message: string;
  /** Absent quand il n'y a aucun filtre à lever : le carnet est vraiment vide. */
  actionLabel?: string;
}

/**
 * B-240 : trois situations rendaient la même phrase, « Aucun contact ». Avec
 * deux cents fiches et une faute de frappe, l'écran affirmait que le carnet
 * était vide. La recherche et le périmètre sont maintenant nommés, et le
 * moyen de les lever est proposé là où l'utilisateur constate le vide.
 */
function decrireEtatVideContacts(
  recherche: string,
  perimetre: MemoryScope | 'all',
): EtatVideContacts {
  const terme = recherche.trim();
  const nomPerimetre = perimetre === 'all' ? null : LIBELLES_PERIMETRE[perimetre];

  if (terme && nomPerimetre) {
    return {
      message: `Aucun contact ne correspond à « ${terme} » dans le périmètre « ${nomPerimetre} ».`,
      actionLabel: 'Effacer les filtres',
    };
  }
  if (terme) {
    return {
      message: `Aucun contact ne correspond à « ${terme} ».`,
      actionLabel: 'Effacer la recherche',
    };
  }
  if (nomPerimetre) {
    return {
      message: `Aucun contact dans le périmètre « ${nomPerimetre} ».`,
      actionLabel: 'Voir tous les périmètres',
    };
  }
  return { message: 'Aucun contact' };
}

interface MemoryPanelProps {
  isOpen?: boolean;
  onClose?: () => void;
  onNewContact?: () => void;
  onEditContact?: (contact: api.Contact) => void;
  /** Mode vue plein écran (content-swap L6) : pas de backdrop ni de tiroir fixe. */
  standalone?: boolean;
}

export function MemoryPanel({ isOpen, onClose, onNewContact, onEditContact, standalone = false }: MemoryPanelProps) {
  // En standalone (vue), le panneau est toujours « ouvert » et charge ses données.
  const effectiveOpen = standalone || !!isOpen;
  const addNotification = useStatusStore((state) => state.addNotification);
  // Contacts via le store UNIQUE (P4) ; plus de state local dupliqué.
  const {
    contacts,
    searchResults,
    fetchContacts,
    search: searchContacts,
    removeLocal,
    truncated: contactsTronques,
    error: contactsError,
  } = useContactsStore();
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  // P-052 : le raccourci « Rechercher dans les Contacts » demande le focus du
  // champ ; la demande est consommée ici, que le panneau soit monté avant ou
  // après elle.
  const rechercheDemandee = useNavigationStore((state) => state.memorySearchFocusRequested);
  useEffect(() => {
    if (!rechercheDemandee) return;
    const champ = document.querySelector<HTMLInputElement>('[data-testid="memory-search-input"]');
    if (!champ) return;
    champ.focus();
    useNavigationStore.getState().consumeMemorySearchFocus();
  }, [rechercheDemandee]);
  // E3-05: Scope filter state
  const [scopeFilter, setScopeFilter] = useState<MemoryScope | 'all'>('all');
  // E3-06: Delete state
  const [deleteConfirm, setDeleteConfirm] = useState<{ type: 'contact'; id: string; name: string } | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  // RGPD state (Phase 6)
  const [rgpdStats, setRgpdStats] = useState<RGPDStatsResponse | null>(null);
  const [rgpdAction, setRgpdAction] = useState<{
    type: 'export' | 'anonymize' | 'renew';
    contact: api.Contact;
  } | null>(null);
  const [rgpdActionLoading, setRgpdActionLoading] = useState(false);
  const [anonymizeReason, setAnonymizeReason] = useState('');
  const { enabled: demoEnabled, maskContact, populateMap } = useDemoMask();
  const vcfInputRef = { current: null as HTMLInputElement | null };

  async function handleImportVCF(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (!file) return;
    try {
      const result = await api.importVCFFile(file);
      console.log('VCF import:', result.message);
      await loadData();
      addNotification({ type: 'success', title: 'Import VCF', message: result.message });
    } catch (err: any) {
      console.error('VCF import failed:', err);
      addNotification({ type: 'error', title: 'Import VCF', message: 'L’import a échoué. Vérifie le fichier et réessaie.' });
    }
    e.target.value = '';
  }

  async function handleExportVCF() {
    try {
      const result = await api.downloadVCFFile();
      addNotification({
        type: 'success',
        title: 'Export VCF',
        message:
          result === 'desktop_saved'
            ? 'Contacts exportés dans Téléchargements'
            : 'Téléchargement du fichier VCF démarré',
      });
    } catch (err: any) {
      // #150 : une seule notification, sans le message brut de l'exception.
      console.error('VCF export failed:', err);
      addNotification({ type: 'error', title: 'Export VCF', message: 'L’export a échoué. Réessaie dans un instant.' });
    }
  }

  // Load data when panel opens or scope changes
  useEffect(() => {
    if (effectiveOpen) {
      loadData();
    }
  }, [effectiveOpen]);

  // P5 : recherche sémantique débouncée quand la requête change.
  useEffect(() => {
    const t = setTimeout(() => {
      searchContacts(searchQuery).catch(() => undefined);
    }, 250);
    return () => clearTimeout(t);
  }, [searchQuery, searchContacts]);

  // Correctif KO Syn 1.1/1.2 : quand un modal destructif (suppression / RGPD) est
  // ouvert, Échap doit le fermer LUI, pas éjecter la vue Mémoire. On l'inscrit sur
  // la pile d'Échap (interceptée avant le retour de vue par cascade Échap de la coque).
  useEffect(() => {
    if (!deleteConfirm && !rgpdAction) return;
    return pushEscapeHandler(() => {
      if (rgpdAction) {
        setRgpdAction(null);
        setAnonymizeReason('');
      } else {
        setDeleteConfirm(null);
        setDeleteError(null);
      }
    });
  }, [deleteConfirm, rgpdAction]);

  async function loadData() {
    setLoading(true);
    try {
      // Contacts via le store unique (sur-ensemble) ; le scope est filtré côté client.
      const [, rgpdStatsData] = await Promise.all([
        fetchContacts(),
        api.getRGPDStats().catch(() => null), // RGPD stats (fail silently)
      ]);
      setRgpdStats(rgpdStatsData);
      // Peupler la map de remplacement pour le mode démo
      populateMap(useContactsStore.getState().contacts, []);
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
      addNotification({ type: 'error', title: 'Export RGPD', message: 'L’export a échoué. Réessaie dans un instant.' });
    } finally {
      setRgpdActionLoading(false);
    }
  }

  async function handleRGPDAnonymize(contact: api.Contact, reason: string) {
    if (!reason.trim()) {
      addNotification({ type: 'warning', title: 'Anonymisation', message: 'Indique la raison de l’anonymisation.' });
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
      addNotification({ type: 'error', title: 'Anonymisation', message: 'L’anonymisation a échoué. Réessaie dans un instant.' });
    } finally {
      setRgpdActionLoading(false);
    }
  }

  async function handleRGPDRenewConsent(contact: api.Contact) {
    setRgpdActionLoading(true);
    try {
      const result = await api.renewContactConsent(contact.id);
      addNotification({ type: 'success', title: 'Consentement', message: `Consentement renouvelé jusqu’au ${new Date(result.new_expiration).toLocaleDateString('fr-FR')}.` });
      setRgpdAction(null);
      await loadData(); // Reload to show updated expiration
    } catch (error) {
      console.error('RGPD renew consent failed:', error);
      addNotification({ type: 'error', title: 'Consentement', message: 'Le renouvellement du consentement a échoué.' });
    } finally {
      setRgpdActionLoading(false);
    }
  }

  // E3-06: Delete handlers
  async function handleDelete() {
    if (!deleteConfirm) return;

    setDeleting(true);
    setDeleteError(null);
    try {
      await api.deleteContactWithCascade(deleteConfirm.id, true);
      removeLocal(deleteConfirm.id);
      setDeleteConfirm(null);
    } catch (error) {
      console.error('Failed to delete:', error);
      setDeleteError(error instanceof Error ? error.message : 'Erreur lors de la suppression');
    } finally {
      setDeleting(false);
    }
  }

  // P5 : pendant une recherche on affiche les résultats sémantiques (searchResults),
  // sinon la liste complète du store. Le scope est filtré côté client.
  const isSearching = searchQuery.trim().length > 0;
  const baseContacts = isSearching ? (searchResults ?? []) : contacts;
  const scopedContacts = scopeFilter === 'all'
    ? baseContacts
    : baseContacts.filter((c) => c.scope === scopeFilter);

  // Mode démo : masquer les contacts affichés
  const displayContacts = demoEnabled ? scopedContacts.map(c => maskContact(c)) : scopedContacts;

  // B-240 : la liste ne savait pas POURQUOI elle était vide. Les deux causes
  // possibles vivent ici ; on les descend au lieu de laisser l'écran affirmer
  // que le carnet est vide.
  const etatVideContacts = decrireEtatVideContacts(searchQuery, scopeFilter);
  function leverLesFiltresContacts() {
    setSearchQuery('');
    setScopeFilter('all');
  }

  const panelBody = (
    <>
            <input
              ref={(el) => { vcfInputRef.current = el; }}
              type="file"
              accept=".vcf"
              className="hidden"
              onChange={handleImportVCF}
            />
            {/* Header - en standalone, les actions vivent ici (harmonisation
                17/07 : la barre « Nouveau contact » pleine largeur en pied de
                page était un vestige du tiroir, absurde sur une vue) */}
            <div className="flex flex-wrap items-end gap-3 px-4 pt-4 pb-2">
              <div>
                {/* B-241 : la coque `PrototypeUnifiedViewCanvas` pose déjà le titre de
                    la vue, et en fait le nom accessible de la région. Ce libellé reste
                    visible mais n'est plus un titre : deux titres de même texte, c'est
                    un plan de page qui ment. */}
                <p className="text-lg font-semibold text-text">Contacts</p>
                {contactsTronques && (
                  <p role="alert" data-testid="memory-troncature" className="text-sm text-warning bg-[var(--color-warning-tint)]">
                    Liste incomplète : {contacts.length} contacts affichés, d'autres
                    existent. Cherche par le nom pour les retrouver.
                  </p>
                )}
              </div>
              {standalone ? (
                <div className="ml-auto flex flex-wrap gap-2 max-[840px]:basis-full max-[840px]:ml-0">
                  <Button
                    variant="secondary"
                    size="md"
                    onClick={() => vcfInputRef.current?.click()}
                    title="Importer des contacts (.vcf)"
                  >
                    <Upload size={18} />
                    Importer (.vcf)
                  </Button>
                  <Button
                    variant="ghost"
                    size="md"
                    onClick={handleExportVCF}
                    title="Exporter les contacts (.vcf)"
                  >
                    <Download size={18} />
                    Exporter
                  </Button>
                  <Button
                    variant="primary"
                    size="md"
                    onClick={onNewContact}
                    data-testid="memory-add-contact-btn"
                    title="Nouveau contact"
                  >
                    <Plus size={18} />
                    Nouveau contact
                  </Button>
                </div>
              ) : (
                <Button variant="ghost" size="icon" onClick={onClose}>
                  <X className="w-5 h-5" />
                </Button>
              )}
            </div>

            {/* Arbitrage A/B : Fichiers sortis en vue Indexation dédiée.
                La Mémoire ne contient plus que les Contacts (un seul sujet, pas d'onglets). */}

            {/* Search + Scope Filter */}
            {(
              <div className="p-3 border-b border-border/30 space-y-2">
                <Input
                  type="search"
                  icon={<Search size={18} />}
                  aria-label="Retrouver un contact"
                  placeholder="Rechercher..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  data-testid="memory-search-input"
                />
                <div role="group" className={CLASSES_SEGMENTS}>
                  {(['all', 'global', 'project', 'conversation'] as const).map((scope) => (
                    <button
                      key={scope}
                      type="button"
                      onClick={() => setScopeFilter(scope)}
                      className={classeSegment(scopeFilter === scope)}
                    >
                      {scope === 'all' ? 'Tout' : scope === 'global' ? 'Global' : scope === 'project' ? 'Projet' : 'Conv.'}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* RGPD Alert Banner */}
            {rgpdStats && rgpdStats.expires_ou_bientot > 0 && (
              <div className="mx-3 mt-3 p-2.5 rounded-md text-sm text-warning bg-[var(--color-warning-tint)]">
                <div className="flex items-center gap-2">
                  <Shield className="w-4 h-4 flex-shrink-0" />
                  <span>
                    <strong>{rgpdStats.expires_ou_bientot}</strong> contact{rgpdStats.expires_ou_bientot > 1 ? 's' : ''} RGPD expire{rgpdStats.expires_ou_bientot > 1 ? 'nt' : ''} bientot
                  </span>
                </div>
              </div>
            )}

            {/* Content */}
            <div className="flex-1 overflow-y-auto">
              {/* #149 : le store dit quand la lecture a échoué ; le panneau le montre,
                  sinon un carnet en panne passe pour un carnet vide. */}
              {contactsError && !loading && (
                <Alerte
                  action={
                    <Button variant="secondary" size="md" type="button" onClick={() => void loadData()}>
                      Réessayer
                    </Button>
                  }
                >
                  {contactsError}
                </Alerte>
              )}
              {loading ? (
                <Squelette lignes={4} className="px-4 py-4" />
              ) : (
                <ContactsList
                  contacts={displayContacts}
                  etatVide={etatVideContacts}
                  onLeverLesFiltres={leverLesFiltresContacts}
                  onSelect={(c) => onEditContact?.(c)}
                  onDelete={(c) => {
                    setDeleteError(null);
                    setDeleteConfirm({
                      type: 'contact',
                      id: c.id,
                      name: [c.first_name, c.last_name].filter(Boolean).join(' ') || c.company || 'Contact'
                    });
                  }}
                  onRGPDAction={(type, contact) => setRgpdAction({ type, contact })}
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
                  className={`absolute inset-0 bg-black/60 flex items-center justify-center p-4 ${Z_LAYER.MODAL_NESTED}`}
                  onClick={() => { setDeleteConfirm(null); setDeleteError(null); }}
                >
                  <motion.div
                    initial={{ scale: 0.95, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    exit={{ scale: 0.95, opacity: 0 }}
                    className="bg-surface border border-border rounded-md p-5 w-full max-w-sm shadow-xl"
                    onClick={(e) => e.stopPropagation()}
                  >
                    <div className="flex items-center gap-3 mb-4">
                      <div className="w-10 h-10 rounded-full bg-error/20 flex items-center justify-center">
                        <AlertCircle className="w-5 h-5 text-error" />
                      </div>
                      <div>
                        <h3 className="text-base font-semibold text-text">Supprimer le contact ?</h3>
                        <p className="text-sm text-text-muted">{deleteConfirm.name}</p>
                      </div>
                    </div>
                    <p className="text-sm text-text-muted mb-4">
                      Les projets et fichiers associés seront aussi supprimés.
                    </p>
                    {deleteError && (
                      <div role="alert" className="flex items-center gap-2 px-3 py-2 mb-4 bg-error/10 border border-error/20 rounded-md">
                        <AlertCircle className="w-4 h-4 text-error shrink-0" />
                        <span className="text-sm text-error">{deleteError}</span>
                      </div>
                    )}
                    <div className="flex gap-2">
                      <Button
                        variant="ghost"
                        className="flex-1"
                        onClick={() => { setDeleteConfirm(null); setDeleteError(null); }}
                        disabled={deleting}
                      >
                        Annuler
                      </Button>
                      <Button
                        variant="danger"
                        className="flex-1"
                        onClick={handleDelete}
                        disabled={deleting}
                      >
                        {deleting ? (
                          <Spinner className="text-error" />
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
                  className={`absolute inset-0 bg-black/60 flex items-center justify-center p-4 ${Z_LAYER.MODAL_NESTED}`}
                  onClick={() => { setRgpdAction(null); setAnonymizeReason(''); }}
                >
                  <motion.div
                    initial={{ scale: 0.95, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    exit={{ scale: 0.95, opacity: 0 }}
                    className="bg-surface border border-border rounded-md p-5 w-full max-w-sm shadow-xl"
                    onClick={(e) => e.stopPropagation()}
                  >
                    {rgpdAction.type === 'export' && (
                      <>
                        <div className="flex items-center gap-3 mb-4">
                          <div className="w-10 h-10 rounded-full bg-accent-cyan/20 flex items-center justify-center">
                            <Download className="w-5 h-5 text-accent-cyan-ink" />
                          </div>
                          <div>
                            <h3 className="text-base font-semibold text-text">Export RGPD</h3>
                            <p className="text-sm text-text-muted">Droit de portabilité (Art. 20)</p>
                          </div>
                        </div>
                        <p className="text-sm text-text-muted mb-4">
                          Exporter toutes les données de <strong>{rgpdAction.contact.first_name} {rgpdAction.contact.last_name}</strong> au format JSON.
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
                              <Spinner />
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
                          <div className="w-10 h-10 rounded-full bg-error/20 flex items-center justify-center">
                            <UserX className="w-5 h-5 text-error" />
                          </div>
                          <div>
                            <h3 className="text-base font-semibold text-text">Anonymisation RGPD</h3>
                            <p className="text-sm text-text-muted">Droit à l'oubli (Art. 17)</p>
                          </div>
                        </div>
                        <p className="text-sm text-text-muted mb-3">
                          Cette action est <strong>irréversible</strong>. Toutes les données personnelles seront remplacées par [ANONYMISE].
                        </p>
                        <div className="mb-4">
                          <label htmlFor="memorypanel-raison-de-l-anonymisation" className="block text-sm font-medium text-text mb-1">Raison de l'anonymisation *</label>
                          <input id="memorypanel-raison-de-l-anonymisation"
                            type="text"
                            value={anonymizeReason}
                            onChange={(e) => setAnonymizeReason(e.target.value)}
                            placeholder="Ex: Demande du contact, fin de relation..."
                            className="w-full px-3 py-2 bg-background/60 border border-border/50 rounded-md text-sm text-text placeholder:text-text-muted focus:outline-none focus:border-error/50"
                          />
                        </div>
                        <div className="flex gap-2">
                          <Button variant="ghost" className="flex-1" onClick={() => { setRgpdAction(null); setAnonymizeReason(''); }}>
                            Annuler
                          </Button>
                          <Button
                            variant="primary"
                            className="flex-1 bg-error hover:bg-error"
                            onClick={() => handleRGPDAnonymize(rgpdAction.contact, anonymizeReason)}
                            disabled={rgpdActionLoading || !anonymizeReason.trim()}
                          >
                            {rgpdActionLoading ? (
                              <Spinner />
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
                          <div className="w-10 h-10 rounded-full bg-agent-green/20 flex items-center justify-center">
                            <RefreshCw className="w-5 h-5 text-agent-green" />
                          </div>
                          <div>
                            <h3 className="text-base font-semibold text-text">Renouveler le consentement</h3>
                            <p className="text-sm text-text-muted">Prolonger de 3 ans</p>
                          </div>
                        </div>
                        <p className="text-sm text-text-muted mb-4">
                          Le consentement de <strong>{rgpdAction.contact.first_name} {rgpdAction.contact.last_name}</strong> sera prolongé de 3 ans à partir d'aujourd'hui.
                        </p>
                        <div className="flex gap-2">
                          <Button variant="ghost" className="flex-1" onClick={() => setRgpdAction(null)}>
                            Annuler
                          </Button>
                          <Button
                            variant="primary"
                            className="flex-1 bg-agent-green hover:bg-agent-green"
                            onClick={() => handleRGPDRenewConsent(rgpdAction.contact)}
                            disabled={rgpdActionLoading}
                          >
                            {rgpdActionLoading ? (
                              <Spinner />
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

            {/* Footer - Add button (mode tiroir uniquement : en vue, les
                actions sont dans l'entête) */}
            {!standalone && (
              <div className="p-3 border-t border-border/50 space-y-2">
                <Button
                  variant="primary"
                  className="w-full"
                  onClick={onNewContact}
                  data-testid="memory-add-contact-btn-drawer"
                >
                  <Plus className="w-4 h-4 mr-2" />
                  Nouveau contact
                </Button>
                <div className="flex gap-2">
                  <Button
                    variant="ghost"
                    className="flex-1"
                    onClick={() => vcfInputRef.current?.click()}
                    title="Importer des contacts (.vcf)"
                  >
                    <Upload className="w-4 h-4 mr-2" />
                    Importer VCF
                  </Button>
                  <Button
                    variant="ghost"
                    className="flex-1"
                    onClick={handleExportVCF}
                    title="Exporter les contacts (.vcf)"
                  >
                    <Download className="w-4 h-4 mr-2" />
                    Exporter VCF
                  </Button>
                </div>
              </div>
            )}
    </>
  );

  // Mode vue plein écran (L6) : pas de backdrop, pas de tiroir fixe.
  // `relative` pour que les modaux internes (suppression, RGPD) en `absolute inset-0`
  // restent cadrés sur la vue.
  if (standalone) {
    // flex-1 min-h-0, pas h-full : la back-bar « Chat » du conteneur de vue
    // ferait déborder le panneau de sa hauteur (cf. bug EmailPanel 11/06).
    return (
      <div className="relative flex-1 min-h-0 flex flex-col bg-bg" data-testid="memory-panel">
        {panelBody}
      </div>
    );
  }

  // Mode tiroir (legacy / overlay)
  return (
    <AnimatePresence>
      {effectiveOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            variants={overlayVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            transition={{ duration: 0.2 }}
            className={`fixed inset-0 bg-black/40 backdrop-blur-sm ${Z_LAYER.BACKDROP}`}
            onClick={onClose}
          />

          {/* Panel */}
          <motion.div
            variants={sidebarVariants}
            initial="initial"
            animate="animate"
            exit="exit"
            data-testid="memory-panel"
            className={`fixed right-0 top-0 bottom-0 w-[420px] bg-surface border-l border-border ${Z_LAYER.MODAL} flex flex-col shadow-2xl`}
          >
            {panelBody}
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}

// Contacts list component
function ContactsList({
  contacts,
  etatVide,
  onLeverLesFiltres,
  onSelect,
  onDelete,
  onRGPDAction,
}: {
  contacts: api.Contact[];
  etatVide: EtatVideContacts;
  onLeverLesFiltres: () => void;
  onSelect: (contact: api.Contact) => void;
  onDelete: (contact: api.Contact) => void;
  onRGPDAction: (type: 'export' | 'anonymize' | 'renew', contact: api.Contact) => void;
}) {
  const [openMenuId, setOpenMenuId] = useState<string | null>(null);

  if (contacts.length === 0) {
    return (
      <EtatVide
        data-testid="contacts-etat-vide"
        titre={etatVide.message}
        action={
          etatVide.actionLabel ? (
            <Button variant="ghost" size="md" onClick={onLeverLesFiltres}>
              {etatVide.actionLabel}
            </Button>
          ) : undefined
        }
      />
    );
  }

  return (
    <div>
      {contacts.map((contact) => {
        const titre = [contact.first_name, contact.last_name].filter(Boolean).join(' ') || 'Sans nom';
        const detail = [contact.company, contact.email].filter(Boolean).join(' · ') || undefined;
        return (
          <Ligne
            key={contact.id}
            puce={getInitials(contact.first_name, contact.last_name)}
            titre={titre}
            detail={detail}
            onClick={() => onSelect(contact)}
            className={openMenuId === contact.id ? Z_LAYER.DROPDOWN : undefined}
            droite={
              <>
                <RGPDBadge contact={contact} />
                <div className="relative">
                  <button
                    type="button"
                    onClick={(e) => { e.stopPropagation(); setOpenMenuId(openMenuId === contact.id ? null : contact.id); }}
                    className="p-1.5 rounded-md hover:bg-accent-tint text-text-muted hover:text-accent-cyan-ink transition-colors"
                    aria-label="Actions RGPD"
                    title="Actions RGPD"
                  >
                    <Shield className="w-4 h-4" />
                  </button>
                  <AnimatePresence>
                    {openMenuId === contact.id && (
                      <motion.div
                        initial={{ opacity: 0, scale: 0.95, y: -5 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.95, y: -5 }}
                        className={`absolute right-0 top-full mt-1 w-48 bg-surface border border-border rounded-md shadow-xl ${Z_LAYER.DROPDOWN} py-1 pointer-events-auto`}
                        onClick={(e) => e.stopPropagation()}
                      >
                        <button
                          type="button"
                          onClick={() => { onRGPDAction('export', contact); setOpenMenuId(null); }}
                          className="w-full flex items-center gap-2 px-3 py-2 text-sm text-text hover:bg-background/40 transition-colors"
                        >
                          <Download className="w-4 h-4 text-accent-cyan-ink" />
                          Exporter (Art. 20)
                        </button>
                        <button
                          type="button"
                          onClick={() => { onRGPDAction('renew', contact); setOpenMenuId(null); }}
                          className="w-full flex items-center gap-2 px-3 py-2 text-sm text-text hover:bg-background/40 transition-colors"
                        >
                          <RefreshCw className="w-4 h-4 text-agent-green" />
                          Renouveler consentement
                        </button>
                        <div className="border-t border-border/50 my-1" />
                        <button
                          type="button"
                          onClick={() => { onRGPDAction('anonymize', contact); setOpenMenuId(null); }}
                          className="w-full flex items-center gap-2 px-3 py-2 text-sm text-error hover:bg-error/10 transition-colors"
                        >
                          <UserX className="w-4 h-4" />
                          Anonymiser (Art. 17)
                        </button>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
                <button
                  type="button"
                  onClick={(e) => { e.stopPropagation(); onDelete(contact); }}
                  className="p-1.5 rounded-md hover:bg-error/20 text-text-muted hover:text-error transition-colors"
                  aria-label={`Supprimer ${titre === 'Sans nom' ? 'le contact' : titre}`}
                  title="Supprimer"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
                <ChevronRight className="w-4 h-4 text-text-muted" />
              </>
            }
          />
        );
      })}
    </div>
  );
}

// RGPD Badge component
function RGPDBadge({ contact }: { contact: api.Contact }) {
  const baseLegale = contact.rgpd_base_legale;
  const dateExpiration = contact.rgpd_date_expiration;

  if (!baseLegale) {
    return (
      <span title="Base légale RGPD non définie pour ce contact">
        <Etiquette ton="attention">RGPD ?</Etiquette>
      </span>
    );
  }

  const isExpiringSoon = dateExpiration && new Date(dateExpiration) <= new Date(Date.now() + 30 * 24 * 60 * 60 * 1000);
  const isExpired = dateExpiration && new Date(dateExpiration) < new Date();

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

  const tonsBase: Record<string, 'succes' | 'info' | 'neutre'> = {
    consentement: 'succes',
    contrat: 'info',
    interet_legitime: 'neutre',
    obligation_legale: 'neutre',
  };

  const ton = isExpired ? 'erreur' : isExpiringSoon ? 'attention' : (tonsBase[baseLegale] ?? 'neutre');
  const title = `${fullLabels[baseLegale] || baseLegale}${dateExpiration ? ` - Expire le ${new Date(dateExpiration).toLocaleDateString('fr-FR')}` : ''}`;

  return (
    <span title={title}>
      <Etiquette ton={ton}>
        {badgeLabels[baseLegale] || baseLegale?.charAt(0).toUpperCase()}
        {isExpired && '!'}
        {isExpiringSoon && !isExpired && <AlertTriangle className="ml-0.5 inline h-3 w-3" aria-hidden="true" />}
      </Etiquette>
    </span>
  );
}

// Helper functions
function getInitials(firstName?: string | null, lastName?: string | null): string {
  const first = firstName?.charAt(0)?.toUpperCase() || '';
  const last = lastName?.charAt(0)?.toUpperCase() || '';
  return first + last || '?';
}

