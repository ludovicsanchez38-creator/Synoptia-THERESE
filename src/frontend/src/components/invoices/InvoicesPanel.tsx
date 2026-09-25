/**
 * THÉRÈSE v2 - Invoices Panel
 *
 * Panel principal pour la gestion de facturation.
 * Phase 4 - Invoicing
 */

import { montantAvecDevise } from '../../lib/devise';
import { useEffect, useRef, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { AlertCircle, FileText, Plus, X } from 'lucide-react';
import { filtresAvecType, statutsProposesPour, useInvoiceStore } from '../../stores/invoiceStore';
import { useStatusStore } from '../../stores/statusStore';
import { listInvoices, deleteInvoice, generateInvoicePDF, type Invoice } from '../../services/api';
import { InvoiceForm } from './InvoiceForm';
import { libellesDeLaPiece } from './libellesPiece';
import { cn } from '../../lib/utils';
import { Z_LAYER } from '../../styles/z-layers';
import { pushEscapeHandler } from '../../lib/escapeStack';
import { useDialogFocusTrap } from '../../hooks/useDialogFocusTrap';
import { Alerte } from '../ui/Alerte';
import { Button } from '../ui/Button';
import { Carte } from '../ui/Carte';
import { EtatVide } from '../ui/EtatVide';
import { Etiquette } from '../ui/Etiquette';
import { Segments } from '../ui/Segments';
import { Squelette } from '../ui/Squelette';
import { STATUS_CONFIG } from './statutsFacture';
import { cellulesStatut, compteurPieces, sousLignePiece } from './presentationFacture';

/** Lot F : le GET factures plafonne à 100. Atteint = liste incomplète. */
const PLAFOND_FACTURES = 100;

const OPTIONS_TYPE = [
  { id: 'all', label: 'Tout' },
  { id: 'devis', label: 'Devis' },
  { id: 'facture', label: 'Factures' },
  { id: 'avoir', label: 'Avoirs' },
] as const;

const SQUELETTES = ['w-24', 'w-[60%]', 'w-20', 'w-20', 'w-16', 'w-16', 'w-12'] as const;

/**
 * B-1387 (Nathalie, Zoé, cycle 13) : à 125 % ou à 800 px, le tableau débordait
 * de son cadre et le montant, « PDF » et « Supprimer » sortaient de la vue. La
 * dernière colonne (montant et actions) reste collée au bord droit du cadre
 * quand le reste défile ; son fond suit celui de la rangée survolée.
 */
const COLONNE_COLLEE = 'sticky right-0 z-[1] bg-surface border-l border-border';

interface InvoicesPanelProps {
  standalone?: boolean;
}

export function InvoicesPanel({ standalone = false }: InvoicesPanelProps) {
  const {
    isInvoicePanelOpen,
    setIsInvoicePanelOpen,
    setInvoices,
    getFilteredInvoices,
    filters,
    setFilters,
    removeInvoice,
    updateInvoiceInStore,
    listeTronquee,
  } = useInvoiceStore();

  const addNotification = useStatusStore((s) => s.addNotification);

  const [isLoading, setIsLoading] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [editingInvoice, setEditingInvoice] = useState<Invoice | null>(null);
  const [deletingInvoice, setDeletingInvoice] = useState<Invoice | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const deleteDialogRef = useRef<HTMLDivElement>(null);
  const creationRef = useRef<HTMLButtonElement>(null);
  const retourSuppressionRef = useRef<HTMLDivElement | null>(null);
  const effectiveOpen = standalone || isInvoicePanelOpen;
  useDialogFocusTrap(deleteDialogRef, {
    active: Boolean(deletingInvoice) && effectiveOpen,
    isolateBackground: true,
  });
  // Pendant l'appel, les deux boutons sont désactivés : le conteneur garde
  // le focus et retient Tab jusqu'au retour de l'API.
  useEffect(() => {
    if (isDeleting) deleteDialogRef.current?.focus();
  }, [isDeleting]);
  useEffect(() => {
    const origine = retourSuppressionRef.current;
    if (deletingInvoice || !origine) return;
    retourSuppressionRef.current = null;
    // Le bouton de la ligne supprimée n'existe plus. Reprendre sur l'action
    // persistante, après le retrait d'inert, sauf si le focus a changé de vue.
    if (effectiveOpen && (document.activeElement === document.body || origine.contains(document.activeElement))) {
      creationRef.current?.focus();
    }
  }, [deletingInvoice, effectiveOpen]);

  // #287 : « Supprimer la facture ? » prend Échap sur la pile ; sinon la touche
  // remonte à la coque, qui replie toute la vue Facturer.
  useEffect(() => {
    if (!deletingInvoice) return;
    return pushEscapeHandler(() => {
      if (!isDeleting) setDeletingInvoice(null);
    });
  }, [deletingInvoice, isDeleting]);

  // Lot F : recharger quand le filtre change. Avant, le filtre tournait
  // dans les 50 plus récentes : « Payée » vide alors que mille payées
  // étaient plus anciennes.
  useEffect(() => {
    if (effectiveOpen) {
      loadInvoices();
    }
  }, [effectiveOpen, filters.status, filters.document_type, filters.contact_id]);

  async function loadInvoices() {
    setIsLoading(true);
    setLoadError(null);
    try {
      const courants = useInvoiceStore.getState().filters;
      const data = await listInvoices({
        limit: PLAFOND_FACTURES,
        status:
          courants.status && courants.status !== 'all' ? courants.status : undefined,
        document_type: courants.document_type,
        contact_id: courants.contact_id,
      });
      setInvoices(data, data.length >= PLAFOND_FACTURES);
    } catch (error) {
      console.error('Failed to load invoices:', error);
      // B-009 : sans cette ligne, l'échec s'ajoutait aux affirmations du
      // chargement précédent au lieu de les remplacer - « 0+ document », le
      // bandeau de troncature et le message d'échec ensemble à l'écran. La
      // liste et son drapeau tombent d'un seul geste : rien ne peut plus
      // décrire des données qui ne sont plus là.
      setInvoices([], false);
      setLoadError('Impossible de charger les factures pour le moment.');
    } finally {
      setIsLoading(false);
    }
  }

  async function handleGeneratePDF(invoice: Invoice) {
    try {
      const result = await generateInvoicePDF(invoice.id);
      try {
        const { open } = await import('@tauri-apps/plugin-shell');
        await open(result.pdf_path);
        addNotification({ type: 'success', title: 'PDF généré et ouvert', message: result.invoice_number });
      } catch (openError) {
        // En prévisualisation web, le système ne peut pas ouvrir un chemin local.
        // Le PDF est tout de même généré et son emplacement reste accessible.
        console.info('PDF generated but local opening is unavailable:', openError);
        addNotification({
          type: 'info',
          title: 'PDF généré',
          message: `Fichier disponible : ${result.pdf_path}`,
          duration: 10000,
        });
      }
    } catch (error) {
      console.error('Failed to generate PDF:', error);
      // B-218 : le serveur dit POURQUOI (« profil émetteur incomplet :
      // renseigne SIRET, adresse dans Réglages > Profil ») et `invoices.ts`
      // porte cette phrase dans l'Error. La remplacer par un générique laissait
      // l'utilisatrice devant un refus sans issue. Le générique ne sert plus
      // que de repli quand l'échec n'a pas de message.
      const cause = error instanceof Error ? error.message.trim() : '';
      addNotification({
        type: 'error',
        title: 'Erreur',
        message: cause || 'Impossible de générer le PDF',
      });
    }
  }

  function handleDeleteInvoice(invoice: Invoice) {
    setDeletingInvoice(invoice);
  }

  async function confirmDeleteInvoice() {
    if (!deletingInvoice) return;

    const origine = deleteDialogRef.current;
    setIsDeleting(true);
    try {
      await deleteInvoice(deletingInvoice.id);
      // Une réponse tardive ne déplace pas le focus d'une autre vue/modale.
      retourSuppressionRef.current = origine?.isConnected && origine === deleteDialogRef.current
        && origine.contains(document.activeElement) ? origine : null;
      removeInvoice(deletingInvoice.id);
      setDeletingInvoice(null);
    } catch (error) {
      console.error('Failed to delete invoice:', error);
      // B-207 : second site du motif fermé en B-218 sur le PDF. Le serveur dit
      // POURQUOI il refuse - la frontière d'erreurs 0.48 lui impose une phrase
      // française - et `invoices.ts` porte cette phrase dans l'Error. La
      // remplacer par un générique laissait l'utilisatrice devant un refus sans
      // issue. Le générique ne sert plus que de repli quand l'échec est muet.
      const cause = error instanceof Error ? error.message.trim() : '';
      addNotification({
        type: 'error',
        title: 'Erreur',
        message: cause || `Impossible de supprimer ${libellesDeLaPiece(deletingInvoice.document_type).nomDefini}`,
      });
    } finally {
      setIsDeleting(false);
    }
  }

  function handleCreateNew() {
    setEditingInvoice(null);
    setShowForm(true);
  }

  function handleEdit(invoice: Invoice) {
    setEditingInvoice(invoice);
    setShowForm(true);
  }

  function handleCloseForm() {
    setShowForm(false);
    setEditingInvoice(null);
  }

  function handleInvoiceCreatedOrUpdated(invoice: Invoice) {
    // B-1067 : « Convertir en facture » renvoie une NOUVELLE pièce, d'un autre
    // identifiant ; la mise à jour par identifiant ne l'ajoutait pas et le devis
    // gardait son ancien statut. Seule la pièce modifiée elle-même est
    // remplacée en place ; tout le reste recharge la liste.
    if (editingInvoice && invoice.id === editingInvoice.id) {
      updateInvoiceInStore(invoice);
    } else {
      // B-569 : un document créé sous un filtre de statut qui l'exclut
      // disparaissait aussitôt de la liste. On lève le filtre pour le montrer.
      if (filters.status && filters.status !== 'all' && filters.status !== invoice.status) {
        setFilters({ ...filters, status: 'all' });
      }
      loadInvoices(); // Recharger pour avoir toutes les données
    }
    handleCloseForm();
    // B-1069 : la première pièce créée depuis l'état vide démonte le bouton qui
    // avait ouvert la modale ; le focus tombait sur la page. Il revient à
    // « Nouveau devis ou facture », sauf s'il est déjà ailleurs.
    requestAnimationFrame(() => {
      const actif = document.activeElement;
      if (!actif || actif === document.body || !actif.isConnected) creationRef.current?.focus();
    });
  }

  const filteredInvoices = getFilteredInvoices();
  // B-646 (Nadia, c4) : Statut = Toutes (la valeur par défaut) comptait comme
  // un filtre, et l'écran vide accusait « ce filtre » avec pour seule action
  // de le réinitialiser. Seul un filtre qui restreint compte.
  const filtreEffectif = Boolean(
    (filters.status && filters.status !== 'all') || filters.document_type || filters.contact_id,
  );
  const echues = filteredInvoices.filter((invoice) => invoice.status === 'overdue').length;

  if (!effectiveOpen) return null;

  const invoicesHeader = (
    <div className="flex flex-wrap items-end gap-3 px-4 py-4 border-b border-border">
      <div>
        {/* B-241 : la coque `PrototypeUnifiedViewCanvas` pose déjà le titre de
            la vue, et en fait le nom accessible de la région. Ce libellé reste
            visible mais n'est plus un titre : deux titres de même texte, c'est
            un plan de page qui ment. */}
        <p className="font-editorial text-lg font-semibold text-text">Devis et factures</p>
        <p data-testid="invoices-compteur" className="text-sm text-text-muted">
          {compteurPieces(filteredInvoices.length, listeTronquee, echues)}
        </p>
        {listeTronquee && (
          <p role="alert" className="text-sm text-warning">
            Liste incomplète : seules les {PLAFOND_FACTURES} pièces les plus
            récentes de ce filtre sont affichées.
          </p>
        )}
      </div>

      <div className="ml-auto flex flex-wrap gap-2 max-[840px]:basis-full max-[840px]:ml-0">
        <Button ref={creationRef} variant="primary" size="lg" type="button" onClick={handleCreateNew}>
          <Plus className="h-[18px] w-[18px]" />
          {/* P-015 : la surface s'appelle « Devis et factures », ses actions nomment les deux objets. */}
          {/* Audit 0.74 : sous le filtre Avoirs, le formulaire s'ouvre sur une facture (un avoir en découle) : le bouton le dit. */}
          {filters.document_type === 'devis' ? 'Nouveau devis' : filters.document_type ? 'Nouvelle facture' : 'Nouveau devis ou facture'}
        </Button>

        {!standalone && (
          <Button
            variant="ghost"
            size="icon"
            type="button"
            aria-label="Fermer"
            onClick={() => setIsInvoicePanelOpen(false)}
          >
            <X className="h-[18px] w-[18px]" />
          </Button>
        )}
      </div>
    </div>
  );

  const invoicesFilters = (
    <div className="px-4 py-3 border-b border-border space-y-2">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-sm text-text-muted">Type</span>
        <Segments
          label="Type"
          className="flex-wrap"
          valeur={filters.document_type ?? 'all'}
          options={[...OPTIONS_TYPE]}
          onChange={(id) =>
            setFilters(
              filtresAvecType(
                filters,
                id === 'all' ? undefined : (id as 'devis' | 'facture' | 'avoir'),
              ),
            )
          }
        />
      </div>
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-sm text-text-muted">Statut</span>
        <Segments
          label="Statut"
          className="flex-wrap"
          valeur={filters.status ?? 'all'}
          options={statutsProposesPour(filters.document_type).map((status) => ({
            id: status,
            label: status === 'all' ? 'Toutes' : STATUS_CONFIG[status].label,
          }))}
          onChange={(id) => setFilters({ ...filters, status: id as typeof filters.status })}
        />
      </div>
    </div>
  );

  const corpsListe = (() => {
    if (isLoading) {
      return (
        <>
          {[0, 1, 2].map((rang) => (
            <div
              key={rang}
              aria-hidden
              className="grid grid-cols-7 gap-3 px-4 py-3 border-t border-border"
            >
              {SQUELETTES.map((largeur, piste) => (
                <Squelette key={piste} largeur={largeur} />
              ))}
            </div>
          ))}
          <p role="status" className="px-4 py-3 text-sm text-text-muted">
            Chargement...
          </p>
        </>
      );
    }

    if (loadError) {
      return (
        <Alerte
          data-testid="invoices-load-error"
          icone={<AlertCircle className="h-[18px] w-[18px]" />}
          titre="Chargement impossible"
          action={
            <Button variant="secondary" size="md" type="button" onClick={() => { void loadInvoices(); }}>
              Réessayer
            </Button>
          }
        >
          {loadError}
        </Alerte>
      );
    }

    if (filteredInvoices.length === 0 && filtreEffectif && filters.status === 'overdue') {
      return (
        <EtatVide
          data-testid="invoices-empty-overdue"
          titre="Aucune pièce en retard"
          action={
            <Button variant="secondary" size="md" type="button" onClick={() => setFilters({})}>
              Réinitialiser les filtres
            </Button>
          }
        >
          Les factures échues et impayées apparaîtront ici.
        </EtatVide>
      );
    }

    if (filteredInvoices.length === 0 && filtreEffectif) {
      return (
        <EtatVide
          data-testid="invoices-empty-filtre"
          titre="Aucun document ne correspond à ce filtre."
          action={
            <Button variant="secondary" size="md" type="button" onClick={() => setFilters({})}>
              Réinitialiser les filtres
            </Button>
          }
        />
      );
    }

    if (filteredInvoices.length === 0) {
      return (
        <EtatVide
          data-testid="invoices-empty"
          titre="Aucun devis ni facture"
          action={
            <Button variant="primary" size="md" type="button" onClick={handleCreateNew}>
              Créer un devis ou une facture
            </Button>
          }
        />
      );
    }

    return (
      <table className="w-full border-collapse">
        <thead>
          <tr>
            <th className="text-left text-xs font-semibold text-text-muted px-4 py-2 border-b border-border tracking-wide">
              Pièce
            </th>
            <th className="text-left text-xs font-semibold text-text-muted px-4 py-2 border-b border-border tracking-wide">
              Client
            </th>
            <th className="text-left text-xs font-semibold text-text-muted px-4 py-2 border-b border-border tracking-wide">
              Envoi
            </th>
            <th className="text-left text-xs font-semibold text-text-muted px-4 py-2 border-b border-border tracking-wide">
              Paiement
            </th>
            <th className="text-left text-xs font-semibold text-text-muted px-4 py-2 border-b border-border tracking-wide">
              Échéance
            </th>
            {/* B-1387 : montant et actions, collés à droite du cadre. */}
            <th className={cn(COLONNE_COLLEE, 'text-right text-xs font-semibold text-text-muted px-4 py-2 border-b border-border tracking-wide')}>
              Montant TTC
            </th>
          </tr>
        </thead>
        <tbody>
          {filteredInvoices.map((invoice) => {
            const { envoi, paiement, echeance } = cellulesStatut(invoice);
            return (
              <tr
                key={invoice.id}
                data-testid="invoice-item"
                className="cursor-pointer hover:[&>td]:bg-surface-2"
                onClick={() => handleEdit(invoice)}
              >
                <td className="px-4 py-2.5 border-b border-border align-middle">
                  <span className="font-mono text-sm whitespace-nowrap">{invoice.invoice_number}</span>
                  <p className="text-xs font-medium text-text-muted">{sousLignePiece(invoice)}</p>
                </td>
                <td className="px-4 py-2.5 border-b border-border align-middle">
                  <button
                    type="button"
                    onClick={(e) => {
                      e.preventDefault();
                      e.stopPropagation();
                      handleEdit(invoice);
                    }}
                    className="inline-flex min-h-9 items-center font-semibold text-sm text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-bg"
                    aria-label={invoice.contact_name ? undefined : invoice.invoice_number}
                  >
                    {invoice.contact_name || (
                      <span className="text-text-muted">{invoice.invoice_number}</span>
                    )}
                  </button>
                </td>
                <td className="px-4 py-2.5 border-b border-border align-middle">
                  <Etiquette ton={envoi.ton}>
                    {envoi.icone ? <FileText className="h-[18px] w-[18px]" /> : null}
                    {envoi.texte}
                  </Etiquette>
                  {envoi.sous ? <p className="text-xs text-text-muted">{envoi.sous}</p> : null}
                </td>
                <td className="px-4 py-2.5 border-b border-border align-middle">
                  {'ton' in paiement ? (
                    <Etiquette ton={paiement.ton}>{paiement.texte}</Etiquette>
                  ) : (
                    <span className="text-sm text-text-muted">{paiement.texte}</span>
                  )}
                </td>
                <td
                  className={cn(
                    'px-4 py-2.5 border-b border-border align-middle tabular-nums',
                    echeance.echue && 'font-semibold text-error',
                    echeance.muted && !echeance.echue && 'text-text-muted',
                  )}
                >
                  {/* B-1387 : seule la date est insécable, la sous-ligne passe à la ligne. */}
                  <span className="whitespace-nowrap">{echeance.texte}</span>
                  {echeance.sous ? (
                    <p className="text-xs text-text-muted font-normal">{echeance.sous}</p>
                  ) : null}
                </td>
                <td className={cn(COLONNE_COLLEE, 'px-4 py-2.5 border-b border-border align-middle')}>
                  <div className="flex items-center justify-end gap-2">
                    <span className="font-semibold tabular-nums whitespace-nowrap text-text">
                      {montantAvecDevise(invoice.total_ttc, invoice.currency)}
                    </span>
                    <Button
                      variant="ghost"
                      size="md"
                      type="button"
                      title="Générer et ouvrir le PDF"
                      aria-label="Générer et ouvrir le PDF"
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        void handleGeneratePDF(invoice);
                      }}
                    >
                      PDF
                    </Button>
                    <Button
                      variant="ghost"
                      size="md"
                      type="button"
                      className="text-error"
                      title="Supprimer"
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        handleDeleteInvoice(invoice);
                      }}
                    >
                      Supprimer
                    </Button>
                  </div>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    );
  })();

  const invoicesList = (
    <div className="flex-1 min-h-0 overflow-y-auto p-6">
      <Carte as="section" className="overflow-x-auto">
        {corpsListe}
      </Carte>
    </div>
  );

  const deleteConfirmModal = deletingInvoice ? (
    <div
      className={`fixed inset-0 ${Z_LAYER.MODAL_NESTED} flex items-center justify-center`}
      onClick={() => !isDeleting && setDeletingInvoice(null)}
    >
      <div className="absolute inset-0 bg-black/60" />
      <div
        ref={deleteDialogRef}
        role="dialog"
        aria-modal="true"
        aria-label="Confirmer la suppression"
        aria-busy={isDeleting}
        tabIndex={-1}
        className="relative w-full max-w-md mx-4 p-6 bg-surface border border-border rounded-md shadow-sm space-y-4"
        onClick={(e) => e.stopPropagation()}
        onKeyDown={(e) => {
          if (isDeleting && e.key === 'Tab') e.preventDefault();
        }}
      >
        {/* B-1038 : un devis ou un avoir ne s'appelle pas « facture ». */}
        <h3 className="text-lg font-semibold text-text">Supprimer {libellesDeLaPiece(deletingInvoice.document_type).nomDefini} ?</h3>
        <p className="text-sm text-text-muted">
          {deletingInvoice.document_type === 'devis'
            ? <>Le devis <strong>{deletingInvoice.invoice_number}</strong> sera définitivement supprimé.</>
            : deletingInvoice.document_type === 'avoir'
              ? <>L’avoir <strong>{deletingInvoice.invoice_number}</strong> sera définitivement supprimé.</>
              : <>La facture <strong>{deletingInvoice.invoice_number}</strong> sera définitivement supprimée.</>}{' '}
          Cette action est irréversible.
        </p>
        <div className="flex items-center justify-end gap-3">
          <Button
            variant="secondary"
            size="md"
            type="button"
            onClick={(e) => {
              e.preventDefault();
              setDeletingInvoice(null);
            }}
            disabled={isDeleting}
          >
            Annuler
          </Button>
          <Button
            variant="danger"
            size="md"
            type="button"
            onClick={(e) => {
              e.preventDefault();
              void confirmDeleteInvoice();
            }}
            disabled={isDeleting}
          >
            {isDeleting ? 'Suppression...' : 'Supprimer'}
          </Button>
        </div>
      </div>
    </div>
  ) : null;

  const formModal = showForm ? (
    <InvoiceForm
      invoice={editingInvoice}
      defaultDocumentType={filters.document_type === 'devis' ? 'devis' : 'facture'}
      onClose={handleCloseForm}
      onSave={handleInvoiceCreatedOrUpdated}
    />
  ) : null;

  // Mode standalone : pleine page
  if (standalone) {
    // flex-1 min-h-0, pas h-full : la back-bar « Chat » du conteneur de vue
    // ferait déborder le panneau de sa hauteur (cf. bug EmailPanel 11/06).
    return (
      <div className="flex-1 min-h-0 flex flex-col bg-bg" data-testid="invoices-panel">
        {invoicesHeader}
        {invoicesFilters}
        {invoicesList}
        {formModal}
        {deleteConfirmModal}
      </div>
    );
  }

  // Mode modal
  return (
    <AnimatePresence>
      <div
        className={`fixed inset-0 ${Z_LAYER.MODAL} flex items-center justify-center`}
        onClick={() => setIsInvoicePanelOpen(false)}
      >
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="absolute inset-0 bg-black/60"
        />

        <motion.div
          role="dialog"
          aria-modal="true"
          aria-label="Factures"
          data-testid="invoices-panel"
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          transition={{ duration: 0.2 }}
          className={cn(
            'relative w-full max-w-6xl h-[85vh] mx-4',
            'bg-surface border border-border rounded-md',
            'shadow-sm overflow-hidden flex flex-col',
          )}
          onClick={(e) => e.stopPropagation()}
        >
          {invoicesHeader}
          {invoicesFilters}
          {invoicesList}
        </motion.div>
      </div>

      {formModal}
      {deleteConfirmModal}
    </AnimatePresence>
  );
}
