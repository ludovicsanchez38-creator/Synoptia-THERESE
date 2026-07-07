/**
 * Tests PistesPanel (Atelier documentaire, D4).
 *
 * Composant purement présentationnel (props uniquement) : le câblage réel
 * avec le store (updatePiste, sélection de la section d'origine,
 * préremplissage de l'instruction) est testé côté `DocumentWorkspace.test.tsx`.
 * Ici : badge compteur (et sa décrémentation quand une piste change de
 * statut), boutons Explorer/Ignorer, sous-liste des pistes traitées
 * (conservées, jamais supprimées), volet repliable.
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { PistesPanel } from './PistesPanel';
import type { DocumentPiste } from '../../services/api/documents';

function makePiste(overrides: Partial<DocumentPiste> = {}): DocumentPiste {
  return {
    id: 'p1',
    document_id: 'd1',
    section_origine_id: 's1',
    texte: 'Ajouter un exemple chiffré sur le ROI',
    status: 'nouvelle',
    created_at: '2026-07-01T00:00:00Z',
    ...overrides,
  };
}

describe('PistesPanel', () => {
  it('état vide : aucune piste nouvelle -> pas de badge, message guidé', () => {
    render(<PistesPanel pistes={[]} onExplore={vi.fn()} onIgnore={vi.fn()} />);
    expect(screen.getByText(/Aucune piste pour l'instant/i)).toBeInTheDocument();
    expect(screen.queryByText('1')).not.toBeInTheDocument();
  });

  it('badge compteur = nombre de pistes au statut nouvelle', () => {
    render(
      <PistesPanel
        pistes={[makePiste({ id: 'p1' }), makePiste({ id: 'p2' }), makePiste({ id: 'p3', status: 'ignoree' })]}
        onExplore={vi.fn()}
        onIgnore={vi.fn()}
      />
    );
    expect(screen.getByLabelText('2 nouvelles pistes')).toHaveTextContent('2');
  });

  it('piste explorée disparaît du badge (compteur décrémente) - re-rendu avec le statut mis à jour', () => {
    const { rerender } = render(
      <PistesPanel
        pistes={[makePiste({ id: 'p1' }), makePiste({ id: 'p2' })]}
        onExplore={vi.fn()}
        onIgnore={vi.fn()}
      />
    );
    expect(screen.getByLabelText('2 nouvelles pistes')).toBeInTheDocument();

    rerender(
      <PistesPanel
        pistes={[makePiste({ id: 'p1', status: 'exploree' }), makePiste({ id: 'p2' })]}
        onExplore={vi.fn()}
        onIgnore={vi.fn()}
      />
    );
    expect(screen.getByLabelText('1 nouvelle piste')).toBeInTheDocument();
  });

  it('« Explorer » appelle onExplore avec la piste complète', () => {
    const onExplore = vi.fn();
    const piste = makePiste();
    render(<PistesPanel pistes={[piste]} onExplore={onExplore} onIgnore={vi.fn()} />);

    fireEvent.click(screen.getByRole('button', { name: /^Explorer$/i }));
    expect(onExplore).toHaveBeenCalledWith(piste);
  });

  it('« Ignorer » appelle onIgnore avec la piste complète', () => {
    const onIgnore = vi.fn();
    const piste = makePiste();
    render(<PistesPanel pistes={[piste]} onExplore={vi.fn()} onIgnore={onIgnore} />);

    fireEvent.click(screen.getByRole('button', { name: /^Ignorer$/i }));
    expect(onIgnore).toHaveBeenCalledWith(piste);
  });

  it('les pistes explorées/ignorées restent visibles (pas supprimées) dans une sous-liste repliée par défaut', () => {
    render(
      <PistesPanel
        pistes={[makePiste({ id: 'p1', status: 'exploree', texte: 'Piste explorée' })]}
        onExplore={vi.fn()}
        onIgnore={vi.fn()}
      />
    );

    // Repliée par défaut : le texte de la piste traitée n'est pas encore affiché.
    expect(screen.queryByText('Piste explorée')).not.toBeInTheDocument();
    expect(screen.getByText(/Pistes traitées \(1\)/i)).toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Pistes traitées/i }));
    expect(screen.getByText('Piste explorée')).toBeInTheDocument();
    expect(screen.getByText('Explorée')).toBeInTheDocument();
  });

  it('volet repliable : replier masque la liste, garde le badge visible ; déplier restaure', () => {
    render(<PistesPanel pistes={[makePiste()]} onExplore={vi.fn()} onIgnore={vi.fn()} />);

    fireEvent.click(screen.getByRole('button', { name: /Replier le volet Pistes/i }));
    expect(screen.getByTestId('pistes-panel-collapsed')).toBeInTheDocument();
    expect(screen.getByLabelText('1 nouvelle piste')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /^Explorer$/i })).not.toBeInTheDocument();

    fireEvent.click(screen.getByRole('button', { name: /Déplier le volet Pistes/i }));
    expect(screen.getByTestId('pistes-panel')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /^Explorer$/i })).toBeInTheDocument();
  });
});
