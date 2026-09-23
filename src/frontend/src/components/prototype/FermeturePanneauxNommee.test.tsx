/**
 * BUG-183 (Discord, Dr_logic-3D, 23/09/2026) : le panneau « Suivi local
 * unifié » se fermait par une icône seule (PanelRightClose), lue comme
 * « réduire ». La règle existe pourtant : BoutonFermerLePanneau affiche le mot
 * « Fermer » à côté de l'icône (persona 08 : « des petits dessins sans nom »).
 * Cinq panneaux de travail l'enfreignaient : Livrables, Relances, Voix,
 * Images, Calculatrice.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it, vi } from 'vitest';
import type { DeliverableResponse } from '../../services/api/crm-extended';

const etat = vi.hoisted(() => ({ livrables: [] as DeliverableResponse[] }));

vi.mock('./usePrototypeDeliverablesData', () => ({
  usePrototypeDeliverablesProjects: () => ({
    resource: {
      status: 'ready',
      data: [{ id: 'p1', name: 'Site vitrine', contact_id: null, status: 'active' }],
      error: null,
    },
    refresh: vi.fn(),
    limitReached: false,
  }),
  usePrototypeDeliverableProjectData: () => ({
    data: {
      projectId: 'p1',
      contact: { status: 'ready', data: null, error: null },
      deliverables: { status: 'ready', data: etat.livrables, error: null },
      invoices: { status: 'ready', data: [], error: null },
      tasks: { status: 'ready', data: [], error: null },
    },
    refresh: vi.fn(),
    appliquerLivrable: vi.fn(),
  }),
}));
vi.mock('./BoutonOuvrirLaVue', () => ({
  BoutonOuvrirLaVue: ({ onClick, children }: { onClick: () => void; children?: React.ReactNode }) => (
    <button type="button" onClick={onClick}>{children ?? 'Ouvrir'}</button>
  ),
}));

import { BoutonFermerLePanneau } from './BoutonFermerLePanneau';
import { DeliverablesWorkspaceCanvas } from './DeliverablesWorkspaceCanvas';

function renderCanevas() {
  return render(
    <DeliverablesWorkspaceCanvas onClose={vi.fn()} onOpenProjects={vi.fn()} onOpenInvoices={vi.fn()} />
  );
}

describe('BUG-183 : la sortie des panneaux de travail est nommée à l’écran', () => {
  it('le suivi local unifié se ferme par un bouton qui affiche « Fermer »', () => {
    etat.livrables = [];
    renderCanevas();
    const bouton = screen.getByRole('button', { name: 'Fermer le suivi client' });
    expect(bouton).toHaveTextContent('Fermer');
  });

  it.each([
    'DeliverablesWorkspaceCanvas',
    'FollowUpsWorkspaceCanvas',
    'VoiceWorkspaceCanvas',
    'ImagesWorkspaceCanvas',
    'CalculatorWorkspaceCanvas',
  ])('%s passe par BoutonFermerLePanneau, sans fermeture à icône seule', (nom) => {
    const source = readFileSync(resolve(process.cwd(), 'src/components/prototype', `${nom}.tsx`), 'utf-8');
    expect(source).toContain('<BoutonFermerLePanneau');
    expect(source).not.toMatch(/size="icon"[^>]*aria-label="Fermer/);
  });
});

// Revue Codex 12 (R-5) : la garde sur les sources ne prouve pas le rendu.
// Le composant partagé, lui, est rendu : mot visible, nom propre au panneau,
// fermeture au clic.
describe('BUG-183 : le bouton partagé ferme et se nomme', () => {
  it('affiche « Fermer », porte le nom donné et appelle onClose', () => {
    const onClose = vi.fn();
    render(<BoutonFermerLePanneau onClose={onClose} nom="Fermer les relances" position="right-4 top-4" />);
    const bouton = screen.getByRole('button', { name: 'Fermer les relances' });
    expect(bouton).toHaveTextContent('Fermer');
    expect(bouton.className).toContain('right-4 top-4');
    fireEvent.click(bouton);
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('sans nom, garde « Fermer ce panneau »', () => {
    render(<BoutonFermerLePanneau onClose={vi.fn()} />);
    expect(screen.getByRole('button', { name: 'Fermer ce panneau' })).toHaveTextContent('Fermer');
  });
});
