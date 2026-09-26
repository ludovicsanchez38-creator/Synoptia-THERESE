/**
 * P-132, seconde moitié, lot 4 : les prestations parlent la langue du pipeline
 * (`docs/plans/2026-09-26-rfc-p132-vocabulaire-unique-perdu.md`, §3 et §7).
 *
 * Sous la fiche d'Élodie, le Pipeline disait Découverte, Proposition,
 * Signature… et la prestation Piste, Proposition envoyée, Signée…
 * Une prestation prend désormais six des huit étapes (ni Contact ni Actif,
 * qui décrivent une personne), avec les mots de la même liste.
 */
import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

const prestations: unknown[] = [];
const creees: unknown[] = [];
const phasesChangees: unknown[] = [];

vi.mock('../../services/api/prestations', async (importOriginal) => {
  const vrai = await importOriginal<typeof import('../../services/api/prestations')>();
  return {
    ...vrai,
    listerLesPrestations: () => Promise.resolve(prestations),
    creerUnePrestation: (c: unknown) => {
      creees.push(c);
      return Promise.resolve({ ...(c as object), id: 'p-neuve' });
    },
    changerLaPhase: (id: string, phase: string) => {
      phasesChangees.push({ id, phase });
      return Promise.resolve({ id, phase });
    },
  };
});

const { ListeDesPrestations } = await import('./ListeDesPrestations');
const { ETAPES_DE_PRESTATION, PIPELINE_ETAPES } = await import('./pipelineEtapes');
const api = await import('../../services/api/prestations');

function servir(...p: unknown[]) {
  prestations.length = 0;
  prestations.push(...p);
}

const FORGER = {
  id: 'p1', contact_id: 'c1', intitule: 'FORGER', montant_ht: 490,
  phase: 'signature', created_at: '2026-08-01T10:00:00Z', updated_at: '2026-08-01T10:00:00Z',
};

// Le même tuple que le moteur (tests/test_p132_prestations_pipeline.py) : l'écran
// n'envoie jamais une valeur que le moteur refuse.
const ETAPES_ACCEPTEES_PAR_LE_MOTEUR = ['discovery', 'proposition', 'signature', 'delivery', 'lost', 'archive'];

describe('P-132 : une prestation parle la langue du pipeline', () => {
  it('le sélecteur propose les six étapes, avec les mots des colonnes du Pipeline', async () => {
    servir(FORGER);
    render(<ListeDesPrestations contactId="c1" />);

    const etape = (await screen.findByLabelText('Étape de FORGER')) as HTMLSelectElement;
    const options = Array.from(etape.options).map((o) => [o.value, o.text]);
    expect(options).toEqual(
      ETAPES_ACCEPTEES_PAR_LE_MOTEUR.map((id) => [id, PIPELINE_ETAPES.find((e) => e.id === id)?.label]),
    );
    expect(etape.value).toBe('signature');
    expect(etape.options[etape.selectedIndex].text).toBe('Signature');
  });

  it('une seule source : les étapes d’une prestation viennent de PIPELINE_ETAPES', () => {
    expect(ETAPES_DE_PRESTATION.map((e) => e.id)).toEqual(ETAPES_ACCEPTEES_PAR_LE_MOTEUR);
    for (const etape of ETAPES_DE_PRESTATION) {
      expect(PIPELINE_ETAPES).toContain(etape);
    }
    // L'ancien vocabulaire recopié n'existe plus.
    expect('LIBELLE_DE_PHASE' in api).toBe(false);
    expect('PHASES_DE_PRESTATION' in api).toBe(false);
  });

  it('changer d’étape envoie l’identifiant du pipeline', async () => {
    servir(FORGER);
    phasesChangees.length = 0;
    render(<ListeDesPrestations contactId="c1" />);

    fireEvent.change(await screen.findByLabelText('Étape de FORGER'), { target: { value: 'lost' } });

    await waitFor(() => expect(phasesChangees).toEqual([{ id: 'p1', phase: 'lost' }]));
  });

  it('le champ de création s’appelle « Étape » et présélectionne Découverte', async () => {
    servir();
    creees.length = 0;
    render(<ListeDesPrestations contactId="c1" />);

    // Le mot visible est « Étape » ; le nom accessible le distingue de
    // l'étape du contact (revue du diff, constat 5).
    const etape = (await screen.findByLabelText('Étape de la nouvelle prestation')) as HTMLSelectElement;
    expect(document.querySelector(`label[for="${etape.id}"]`)?.firstChild?.textContent).toBe('Étape');
    expect(screen.getByRole('group', { name: 'Nouvelle prestation' })).toContainElement(etape);
    expect(etape.value).toBe('discovery');
    expect(etape.options[etape.selectedIndex].text).toBe('Découverte');
    expect(screen.queryByText(/où ça en est/i)).toBeNull();

    fireEvent.change(screen.getByLabelText(/intitulé/i), { target: { value: 'Audit' } });
    fireEvent.click(screen.getByRole('button', { name: /ajouter/i }));

    await waitFor(() => expect(creees).toHaveLength(1));
    expect((creees[0] as { phase: string }).phase).toBe('discovery');
  });

  it('une valeur inconnue se dit telle quelle, sans être remplacée par la première option', async () => {
    servir({ ...FORGER, phase: 'xyz' });
    render(<ListeDesPrestations contactId="c1" />);

    const etape = (await screen.findByLabelText('Étape de FORGER')) as HTMLSelectElement;
    expect(etape.value).toBe('xyz');
    expect(etape.options[etape.selectedIndex].text).toBe('Étape inconnue : xyz');
  });
});
