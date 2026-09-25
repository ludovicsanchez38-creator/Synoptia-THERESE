/**
 * B-1346 et B-1363 (cycle 13) : les liens de la mise en route n'ouvraient pas
 * la bonne rubrique.
 *
 * « Compléter le profil de facturation » ouvrait Paramètres en haut du profil
 * (Claire devait défiler jusqu'à la facturation), et « Configurer une clé IA »
 * ouvrait aussi le Profil, au lieu de « Service d'IA ».
 */
import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';

import { SetupChecklist } from './SetupChecklist';
import { usePanelStore } from '../../stores/panelStore';

const rienDeFait = {
  has_calendar: true, has_email: true, billing_complete: false, has_invoices: false,
  has_llm_key: false, indisponibles: [],
};

beforeEach(() => {
  usePanelStore.getState().closeSettings();
});

describe('mise en route : chaque lien ouvre sa rubrique', () => {
  it('« Compléter le profil de facturation » demande la section facturation du profil', () => {
    render(<SetupChecklist status={rienDeFait} />);
    fireEvent.click(screen.getByRole('button', { name: /Compléter le profil de facturation/ }));
    const etat = usePanelStore.getState();
    expect(etat.showSettings).toBe(true);
    expect(etat.requestedSettingsTab).toBe('profile');
    expect(etat.requestedSettingsSection).toBe('facturation');
  });

  it('« Configurer une clé IA » ouvre la rubrique Service d’IA', () => {
    render(<SetupChecklist status={rienDeFait} />);
    fireEvent.click(screen.getByRole('button', { name: /Configurer une clé IA/ }));
    expect(usePanelStore.getState().requestedSettingsTab).toBe('ai');
  });

  it('fermer les Paramètres oublie la section demandée', () => {
    usePanelStore.getState().openSettings('profile', 'facturation');
    usePanelStore.getState().closeSettings();
    expect(usePanelStore.getState().requestedSettingsSection).toBeNull();
  });
});
