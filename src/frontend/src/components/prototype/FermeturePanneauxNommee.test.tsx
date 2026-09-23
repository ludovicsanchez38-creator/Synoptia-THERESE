/**
 * BUG-183 (Discord, Dr_logic-3D, 23/09/2026) : le panneau « Suivi local
 * unifié » se fermait par une icône seule (PanelRightClose), lue comme
 * « réduire ». La règle existe pourtant : BoutonFermerLePanneau affiche le mot
 * « Fermer » à côté de l'icône (persona 08 : « des petits dessins sans nom »).
 * Cinq panneaux de travail l'enfreignaient : Livrables, Relances, Voix,
 * Images, Calculatrice.
 */
import { render, screen } from '@testing-library/react';
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
