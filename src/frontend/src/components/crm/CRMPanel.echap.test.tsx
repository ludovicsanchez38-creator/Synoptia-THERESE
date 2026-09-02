/**
 * B-262 : Échap dans « Nouveau contact CRM » éjectait tout le panneau CRM.
 *
 * `CreateContactModal` (CRMPanel.tsx) se déclare `role="dialog"
 * aria-modal="true"` mais n'appelait jamais `pushEscapeHandler`. La cascade
 * d'Échap de la coque (`consommeEchapUnifie`, ConversationCanvasPrototype.tsx)
 * interroge d'abord la pile, puis les modales du panelStore : le formulaire
 * n'était dans ni l'une ni l'autre, la cascade rendait donc false et retombait
 * sur `collapseEmbeddedView()`, qui démonte la vue CRM AVEC le formulaire et
 * la saisie en cours. C'est exactement le « KO 1.1/1.2 » que lib/escapeStack.ts
 * dit empêcher : « Échap tombait sur le retour de vue (goBack) et ÉJECTAIT la
 * vue entière sous le modal ».
 *
 * Même défaut, même correctif que B-228 (InvoiceForm.echap.test.tsx), et le
 * commentaire d'autorité de la coque le dit déjà : « Une surface nouvelle doit
 * s'inscrire dans l'une des deux — il n'y a pas de troisième endroit. »
 *
 * Ce test mesure la pile ET le rendu : un handler inscrit qui ne fermerait pas
 * le formulaire passerait la première assertion et pas la seconde. La
 * conséquence à l'écran (le panneau CRM survit à Échap) est mesurée de bout en
 * bout par tests/e2e/stories/parcours-04-crm.spec.ts.
 */
import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { useCRMStore } from '../../stores/crmStore';
import { useContactsStore } from '../../stores/contactsStore';
import { _clearEscapeHandlers, runTopEscapeHandler } from '../../lib/escapeStack';

vi.mock('../../services/api', async () => {
  const reel = await vi.importActual<typeof import('../../services/api')>('../../services/api');
  return {
    ...reel,
    listProjects: vi.fn().mockResolvedValue([]),
    listActivities: vi.fn().mockResolvedValue([]),
  };
});

import { CRMPanel } from './CRMPanel';

async function ouvrirLeFormulaire() {
  render(<CRMPanel standalone />);
  fireEvent.click(await screen.findByRole('button', { name: /Ajouter un contact/i }));
  return screen.findByRole('dialog', { name: 'Nouveau contact CRM' });
}

describe('B-262 : Échap ne ferme que le formulaire de contact', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    _clearEscapeHandlers();
    useCRMStore.setState({ projects: [], activeTab: 'pipeline' });
    useContactsStore.setState({ contacts: [], selectedContactId: null, truncated: false });
  });

  afterEach(() => {
    _clearEscapeHandlers();
  });

  it("le formulaire s'inscrit dans la pile Échap, et une pression le ferme seul", async () => {
    const formulaire = await ouvrirLeFormulaire();
    expect(formulaire).toBeInTheDocument();

    // La pile a un preneur : la cascade de la coque s'arrête là et ne descend
    // donc jamais jusqu'à `collapseEmbeddedView()`, qui démonterait la vue CRM.
    let consomme = false;
    act(() => {
      consomme = runTopEscapeHandler();
    });
    expect(consomme).toBe(true);

    await waitFor(() =>
      expect(screen.queryByRole('dialog', { name: 'Nouveau contact CRM' })).toBeNull(),
    );
    // Et le panneau qui le portait est toujours là.
    expect(screen.getByTestId('crm-panel')).toBeInTheDocument();
  });

  it('le handler se retire à la fermeture : Échap suivant ne trouve plus personne', async () => {
    await ouvrirLeFormulaire();

    fireEvent.click(screen.getByRole('button', { name: 'Annuler' }));
    await waitFor(() =>
      expect(screen.queryByRole('dialog', { name: 'Nouveau contact CRM' })).toBeNull(),
    );

    // Leçon B-237 (PipelineView) : un handler laissé dans la pile avalerait
    // TOUS les Échap suivants, et la coque ne fermerait plus rien.
    expect(runTopEscapeHandler()).toBe(false);
  });
});
