/**
 * THÉRÈSE v2 - CRM Panel (Phase 6)
 *
 * Panel principal CRM avec Pipeline et Activités.
 * Utilise crmStore avec persistance pour affichage instantané.
 */

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, UserPlus, Upload, Mail, Phone, FileText, Users, AlertCircle } from 'lucide-react';
import { PipelineView } from './PipelineView';
import { ActivityTimeline } from './ActivityTimeline';
import { ListeDesPrestations } from './ListeDesPrestations';
import { useCRMStore } from '../../stores/crmStore';
import { useContactsStore } from '../../stores/contactsStore';
import { listProjects, listActivities, updateContactStage, type ContactResponse, type ActivityResponse } from '../../services/api';
import { createCRMContact, importVCFContacts, type CreateCRMContactRequest } from '../../services/api/crm';
import { useDemoMask } from '../../hooks';
import { useStatusStore } from '../../stores/statusStore';
import { Z_LAYER } from '../../styles/z-layers';
import { handleRovingFocus } from '../../lib/rovingFocus';
import { pushEscapeHandler } from '../../lib/escapeStack';
import { cn } from '../../lib/utils';
import { Alerte } from '../ui/Alerte';
import { Button } from '../ui/Button';
import { Carte, CarteTete } from '../ui/Carte';
import { EtatVide } from '../ui/EtatVide';
import { FormField } from '../ui/FormField';
import { Input } from '../ui/Input';
import { Select } from '../ui/Select';
import { Squelette } from '../ui/Squelette';
import { Textarea } from '../ui/Textarea';
import { CLASSES_SEGMENTS, classeSegment } from '../ui/segments.classes';
import { PIPELINE_ETAPES } from './pipelineEtapes';

interface CRMPanelProps {
  isOpen?: boolean;
  onClose?: () => void;
  standalone?: boolean;
}

export function CRMPanel({ isOpen, onClose, standalone = false }: CRMPanelProps) {
  const { projects, activeTab, setProjects, setActiveTab } = useCRMStore();
  const {
    contacts: allContacts,
    selectedContactId,
    setSelectedContact,
    fetchContacts,
    upsertLocal,
    truncated: contactsTronques,
  } = useContactsStore();

  // B-314 : `stage` est l'appartenance au pipeline ; `source` n'est qu'une
  // information facultative sur l'origine du contact. Filtrer sur cette
  // dernière cachait des fiches pourtant placées en Découverte, Livraison ou
  // Actif et produisait un compteur faux. Le store unique est la source de
  // vérité de la vue, sans duplication.
  const contacts = allContacts;

  const hasCachedContacts = contacts.length > 0;

  const [loading, setLoading] = useState(!hasCachedContacts);
  const [error, setError] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [showAddActivity, setShowAddActivity] = useState(false);
  const [activityRefreshKey, setActivityRefreshKey] = useState(0);
  const vcfInputRef = useRef<HTMLInputElement>(null);
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
      // Contacts via le store unique (sur-ensemble) + projets en parallèle
      const [, projectsData] = await Promise.all([
        fetchContacts(),
        listProjects(0, 200),
      ]);
      setProjects(projectsData);
      // Peupler la map de remplacement pour le mode démo
      populateMap(useContactsStore.getState().contacts, projectsData);
    } catch (err: any) {
      console.error('Failed to load CRM data:', err);
      // D69 : même avec des contacts en cache, un rechargement en panne se dit,
      // sinon une liste périmée passe pour à jour. Le store des contacts porte
      // le message quand c'est lui qui a échoué.
      setError(useContactsStore.getState().error || err?.message || 'Impossible de charger les données CRM');
    } finally {
      setLoading(false);
    }
  };

  const handleStageChange = async (contactId: string, newStage: string) => {
    try {
      setError(null);
      const updated = await updateContactStage(contactId, newStage);
      upsertLocal(updated);
    } catch (err: any) {
      console.error('Failed to update stage:', err);
      setError(err?.message || 'Impossible de mettre à jour le stage');
    }
  };

  const handleContactClick = (contact: ContactResponse) => {
    setSelectedContact(contact.id);
    setActiveTab('activities');
  };

  const handleImportVCF = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const addNotification = useStatusStore.getState().addNotification;
    try {
      const result = await importVCFContacts(file);
      addNotification({ type: 'success', title: 'Import VCF', message: result.message });
      await loadContacts();
    } catch (err: any) {
      addNotification({ type: 'error', title: 'Erreur import', message: err.message });
    }
    e.target.value = '';
  };

  const handleCreateContact = async (data: CreateCRMContactRequest) => {
    try {
      setError(null);
      const newContact = await createCRMContact(data);
      upsertLocal(newContact);
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
    { id: 'pipeline' as const, label: 'Pipeline' },
    { id: 'activities' as const, label: 'Activités' },
  ];

  if (!effectiveOpen) return null;

  const crmHeader = (
    <div className="flex flex-wrap items-end gap-3 px-4 pt-4 pb-2">
      <div>
        {/* B-241 : la coque `PrototypeUnifiedViewCanvas` pose déjà le titre de
            la vue, et en fait le nom accessible de la région. Ce libellé reste
            visible mais n'est plus un titre : deux titres de même texte, c'est
            un plan de page qui ment. */}
        <p className="text-lg font-semibold text-text">Pipeline</p>
        <p className="text-sm text-text-muted tabular-nums">
          {contacts.length} contact{contacts.length > 1 ? 's' : ''}
          {contactsTronques ? '+' : ''} · {projects.length} projet{projects.length > 1 ? 's' : ''}
        </p>
        {contactsTronques && (
          <p role="alert" data-testid="crm-troncature" className="text-sm text-warning bg-[var(--color-warning-tint)]">
            Liste incomplète : le pipeline ne montre que les 200 contacts les plus récents.
          </p>
        )}
      </div>

      <div className="ml-auto flex flex-wrap gap-2 max-[840px]:basis-full max-[840px]:ml-0">
        <input
          ref={vcfInputRef}
          type="file"
          accept=".vcf"
          className="hidden"
          onChange={handleImportVCF}
        />
        <Button variant="secondary" size="md" className="gap-2" onClick={() => vcfInputRef.current?.click()}>
          <Upload size={18} />
          Importer (.vcf)
        </Button>
        <Button variant="primary" size="md" className="gap-2" onClick={() => setShowCreateForm(true)}>
          <UserPlus size={18} />
          Nouveau contact
        </Button>
        {!standalone && (
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="w-5 h-5 text-text-muted" />
          </Button>
        )}
      </div>
    </div>
  );

  const crmTabs = (
    // B-219 : tablist / tab / aria-selected, plus les flèches pour changer
    // d'onglet - sans elles, le `tabIndex={-1}` de l'onglet inactif l'enfermerait.
    <div
      role="tablist"
      aria-label="Vues du CRM"
      className={cn(CLASSES_SEGMENTS, 'px-4 pt-3')}
    >
      {tabs.map(tab => {
        const isActive = activeTab === tab.id;

        return (
          <button
            key={tab.id}
            id={`crm-tab-${tab.id}`}
            role="tab"
            aria-selected={isActive}
            aria-controls={`crm-panel-${tab.id}`}
            tabIndex={isActive ? 0 : -1}
            onKeyDown={(event) => handleRovingFocus(event, '[role="tab"]', 'horizontal')}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              classeSegment(isActive),
              'focus-visible:outline focus-visible:outline-[3px] focus-visible:outline-offset-2 focus-visible:outline-ring',
            )}
          >
            {tab.label}
          </button>
        );
      })}
    </div>
  );

  const crmErreur = error ? (
    <Alerte data-testid="crm-erreur" icone={<AlertCircle size={18} />}>
      {error}
    </Alerte>
  ) : null;

  const crmContent = (
    <div
      id={`crm-panel-${activeTab}`}
      role="tabpanel"
      aria-labelledby={`crm-tab-${activeTab}`}
      tabIndex={0}
      className="flex-1 overflow-auto p-6 outline-none"
    >
      {loading ? (
        <div>
          <p role="status">Chargement du pipeline…</p>
          <div
            aria-hidden="true"
            className="grid grid-flow-col auto-cols-[minmax(15rem,1fr)] gap-3"
          >
            {[0, 1, 2].map((colonne) => (
              <div key={colonne} className="grid gap-2">
                <Squelette classeBarre="h-8 rounded-sm" largeur="w-8" />
                <Squelette largeur="w-[60%]" />
                <Squelette largeur="w-[40%]" />
              </div>
            ))}
          </div>
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
              <Carte>
                <CarteTete
                  titre={`${displaySelectedContact.first_name} ${displaySelectedContact.last_name}`}
                  meta={displaySelectedContact.company || undefined}
                  actions={
                    <Button variant="primary" size="md" onClick={() => setShowAddActivity(true)}>
                      Ajouter une activité
                    </Button>
                  }
                />
              </Carte>

              {/* Les prestations d'abord : c'est l'ETAT (ce que Ludo a
                  enregistre), la timeline en dessous n'est que la trace de ce
                  qui a ete ecrit. */}
              <section className="mb-6 mt-4">
                <h3 className="mb-2 text-sm font-semibold text-text">Prestations</h3>
                <ListeDesPrestations contactId={selectedContact!.id} />
              </section>

              <h3 className="mb-2 text-sm font-semibold text-text">Historique</h3>
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
            // B-205 : le fil charge les activités de TOUS les contacts
            // (`listActivities` sans filtre) ; il doit donc les nommer depuis le
            // magasin COMPLET, jamais depuis la vue filtrée du pipeline (filtre
            // délibéré, plus haut) — sinon la vue affiche une ligne qu'elle
            // s'interdit ensuite de nommer (« Contact inconnu »).
            <GlobalActivityView annuaire={demoEnabled ? allContacts.map((c) => maskContact(c)) : allContacts} />
          )}
        </AnimatePresence>
      )}
    </div>
  );

  // Mode standalone : pleine page
  if (standalone) {
    // flex-1 min-h-0, pas h-full : la back-bar « Chat » du conteneur de vue
    // ferait déborder le panneau de sa hauteur (cf. bug EmailPanel 11/06).
    return (
      <div className="flex-1 min-h-0 flex flex-col bg-bg" data-testid="crm-panel">
        {crmHeader}
        {crmTabs}
        {crmErreur}
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
            className={`fixed inset-0 bg-black/50 backdrop-blur-sm ${Z_LAYER.BACKDROP}`}
          />

          <motion.div
            role="dialog"
            aria-modal="true"
            aria-label="CRM Pipeline"
            data-testid="crm-panel"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className={`fixed inset-8 bg-background border border-surface rounded-md shadow-2xl ${Z_LAYER.MODAL} flex flex-col`}
          >
            {crmHeader}
            {crmTabs}
            {crmErreur}
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

const STAGES = PIPELINE_ETAPES.filter((s) => s.id !== 'archive');

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
  const [formError, setFormError] = useState<string | null>(null);

  // B-262 : le formulaire se déclare `aria-modal` mais n'était inscrit NI dans
  // la pile Échap NI dans le panelStore. `consommeEchapUnifie` rendait donc
  // false, la cascade de la coque tombait sur `collapseEmbeddedView()` et
  // éjectait la vue CRM entière — saisie en cours comprise — en une seule
  // pression. Même défaut et même correctif que B-228 (InvoiceForm).
  // Le ref suit le pattern de SignatureEditorModal : sans lui, l'identité de
  // `onClose`, recréée à chaque rendu du parent, réinscrirait un handler par
  // rendu.
  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose;
  useEffect(() => pushEscapeHandler(() => onCloseRef.current()), []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.first_name.trim()) {
      setFormError('Le prénom est obligatoire.');
      return;
    }

    setFormError(null);
    setSubmitting(true);
    try {
      await onCreate(form);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className={`fixed inset-0 flex items-center justify-center ${Z_LAYER.MODAL_NESTED}`}>
      <div className="absolute inset-0 bg-black/30" onClick={onClose} />
      <motion.div
        role="dialog"
        aria-modal="true"
        aria-label="Nouveau contact CRM"
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="relative bg-surface border border-border rounded-md shadow-2xl p-6 w-full max-w-lg mx-4"
      >
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-text-primary">Nouveau contact</h3>
          <Button variant="ghost" size="icon" onClick={onClose} type="button">
            <X className="w-5 h-5 text-text-muted" />
          </Button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {formError && <Alerte>{formError}</Alerte>}
          <div className="grid grid-cols-2 gap-4">
            <FormField htmlFor="crmpanel-prenom" label="Prénom *">
              <Input
                id="crmpanel-prenom"
                type="text"
                value={form.first_name}
                onChange={(e) => setForm(prev => ({ ...prev, first_name: e.target.value }))}
                required
              />
            </FormField>
            <FormField htmlFor="crmpanel-nom" label="Nom">
              <Input
                id="crmpanel-nom"
                type="text"
                value={form.last_name || ''}
                onChange={(e) => setForm(prev => ({ ...prev, last_name: e.target.value }))}
              />
            </FormField>
          </div>

          <FormField htmlFor="crmpanel-entreprise" label="Entreprise">
            <Input
              id="crmpanel-entreprise"
              type="text"
              value={form.company || ''}
              onChange={(e) => setForm(prev => ({ ...prev, company: e.target.value }))}
            />
          </FormField>

          <div className="grid grid-cols-2 gap-4">
            <FormField htmlFor="crmpanel-email" label="Email">
              <Input
                id="crmpanel-email"
                type="email"
                value={form.email || ''}
                onChange={(e) => setForm(prev => ({ ...prev, email: e.target.value }))}
              />
            </FormField>
            <FormField htmlFor="crmpanel-telephone" label="Téléphone">
              <Input
                id="crmpanel-telephone"
                type="tel"
                value={form.phone || ''}
                onChange={(e) => setForm(prev => ({ ...prev, phone: e.target.value }))}
              />
            </FormField>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <FormField htmlFor="crmpanel-source" label="Source">
              <Input
                id="crmpanel-source"
                type="text"
                value={form.source || ''}
                onChange={(e) => setForm(prev => ({ ...prev, source: e.target.value }))}
                placeholder="LinkedIn, Site web..."
              />
            </FormField>
            <FormField htmlFor="crmpanel-stage" label="Stage">
              <Select
                id="crmpanel-stage"
                value={form.stage}
                onChange={(e) => setForm(prev => ({ ...prev, stage: e.target.value }))}
                options={STAGES.map((s) => ({ value: s.id, label: s.label }))}
              />
            </FormField>
          </div>

          <div className="flex justify-end gap-3 pt-2">
            <Button type="button" variant="ghost" size="md" onClick={onClose}>
              Annuler
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="md"
              disabled={!form.first_name.trim() || submitting}
            >
              {submitting ? 'Création...' : 'Créer le contact'}
            </Button>
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
  email: 'text-agent-blue',
  call: 'text-agent-green',
  meeting: 'text-agent-purple',
  note: 'text-warning',
};

function GlobalActivityView({ annuaire }: { annuaire: ContactResponse[] }) {
  const [activities, setActivities] = useState<ActivityResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  // B-442 : en démonstration, titres et descriptions citent des vrais noms.
  const { maskText } = useDemoMask();
  // B-527 : une panne n'est pas un fil vide.
  const [erreurActivites, setErreurActivites] = useState<string | null>(null);

  useEffect(() => {
    loadAllActivities();
  }, []);

  const loadAllActivities = async () => {
    try {
      setLoading(true);
      const data = await listActivities({ limit: 100 });
      setActivities(data);
      setErreurActivites(null);
    } catch (error) {
      console.error('Failed to load global activities:', error);
      setErreurActivites('Les activités n’ont pas pu être lues. Réessaie dans un instant.');
    } finally {
      setLoading(false);
    }
  };

  const filteredActivities = filter === 'all'
    ? activities
    : activities.filter(a => a.type === filter);

  const getContactName = (contactId: string) => {
    const contact = annuaire.find(c => c.id === contactId);
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
      <div role="group" className={cn(CLASSES_SEGMENTS, 'mb-6 flex-wrap')}>
        {ACTIVITY_FILTER_CHIPS.map(chip => {
          const isActive = filter === chip.id;
          const ChipIcon = chip.icon;
          return (
            <button
              key={chip.id}
              type="button"
              onClick={() => setFilter(chip.id)}
              className={classeSegment(isActive)}
            >
              {ChipIcon && <ChipIcon size={18} />}
              {chip.label}
            </button>
          );
        })}
      </div>

      {loading && (
        <div>
          <p role="status">Chargement des activités…</p>
          <Squelette lignes={3} />
        </div>
      )}

      {!loading && erreurActivites && (
        <Alerte
          data-testid="crm-activites-erreur"
          action={
            <Button variant="secondary" size="md" type="button" onClick={() => void loadAllActivities()}>
              Réessayer
            </Button>
          }
        >
          {erreurActivites}
        </Alerte>
      )}

      {!loading && !erreurActivites && filteredActivities.length === 0 && (
        <EtatVide
          data-testid="crm-activites-vide"
          titre={
            filter === 'all'
              ? 'Aucune activité enregistrée'
              : `Aucune activité de type "${ACTIVITY_FILTER_CHIPS.find(c => c.id === filter)?.label}"`
          }
        >
          Clique sur un contact dans le Pipeline pour ajouter une activité
        </EtatVide>
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

                <div className="flex-1 bg-surface rounded-md p-3">
                  <div className="flex items-start justify-between gap-2">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2 mb-0.5">
                        <span className="text-sm font-medium text-accent-cyan-ink">{contactName}</span>
                        <span className="text-sm text-text-muted">·</span>
                        <span className="text-sm text-text-muted capitalize">{
                          activity.type === 'email' ? 'Email' :
                          activity.type === 'call' ? 'Appel' :
                          activity.type === 'meeting' ? 'Réunion' :
                          activity.type === 'note' ? 'Note' :
                          activity.type === 'stage_change' ? 'Changement de stage' :
                          activity.type
                        }</span>
                      </div>
                      <h4 className="text-sm font-medium text-text-primary">{maskText(activity.title)}</h4>
                      {activity.description && (
                        <p className="text-sm text-text-muted mt-1 line-clamp-2">{maskText(activity.description)}</p>
                      )}
                    </div>
                    <span className="tabular-nums text-sm text-text-muted whitespace-nowrap shrink-0">
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
  const [activityError, setActivityError] = useState<string | null>(null);

  // B-336 : même inscription dans la pile Échap que CreateContactModal (B-262) ;
  // sans elle, Échap retombait sur la cascade de la coque et éjectait la vue CRM.
  const onCloseRef = useRef(onClose);
  onCloseRef.current = onClose;
  useEffect(() => pushEscapeHandler(() => onCloseRef.current()), []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) {
      setActivityError('Le titre est obligatoire.');
      return;
    }

    setActivityError(null);
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
      // B-528 : l'échec serveur passe par le même bandeau que la validation locale.
      setActivityError('L’activité n’a pas été enregistrée. Réessaie dans un instant.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className={`fixed inset-0 flex items-center justify-center ${Z_LAYER.MODAL_NESTED}`}>
      <div className="absolute inset-0 bg-black/30" onClick={onClose} />
      <motion.div
        role="dialog"
        aria-modal="true"
        aria-label="Nouvelle activité CRM"
        initial={{ opacity: 0, scale: 0.95, y: 20 }}
        animate={{ opacity: 1, scale: 1, y: 0 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="relative bg-surface border border-border rounded-md shadow-2xl p-6 w-full max-w-lg mx-4"
      >
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-text-primary">Nouvelle activité</h3>
          <Button variant="ghost" size="icon" onClick={onClose} type="button">
            <X className="w-5 h-5 text-text-muted" />
          </Button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {activityError && <Alerte>{activityError}</Alerte>}
          <div>
            <p className="block text-sm font-semibold text-text mb-2">Type</p>
            <div role="group" className={CLASSES_SEGMENTS}>
              {ACTIVITY_TYPES.map(at => {
                const AtIcon = at.icon;
                const isActive = type === at.id;
                return (
                  <button
                    key={at.id}
                    type="button"
                    onClick={() => setType(at.id)}
                    className={classeSegment(isActive)}
                  >
                    <AtIcon size={18} />
                    {at.label}
                  </button>
                );
              })}
            </div>
          </div>

          <FormField htmlFor="crmpanel-titre" label="Titre *">
            <Input
              id="crmpanel-titre"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Ex: Appel de suivi, Envoi devis..."
              required
            />
          </FormField>

          <FormField htmlFor="crmpanel-description" label="Description">
            <Textarea
              id="crmpanel-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Détails de l'activité..."
              rows={3}
            />
          </FormField>

          <div className="flex justify-end gap-3 pt-2">
            <Button type="button" variant="ghost" size="md" onClick={onClose}>
              Annuler
            </Button>
            <Button
              type="submit"
              variant="primary"
              size="md"
              disabled={!title.trim() || submitting}
            >
              {submitting ? 'Ajout...' : 'Ajouter'}
            </Button>
          </div>
        </form>
      </motion.div>
    </div>
  );
}
