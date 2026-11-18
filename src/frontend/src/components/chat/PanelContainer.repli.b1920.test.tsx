/**
 * B-1920 : le repli du Suspense qui groupe les panneaux est « Chargement... »
 * sans role=status. Le repli de la bibliothèque, lui, annonce le chargement.
 */
import { render, screen } from '@testing-library/react';
import { expect, it, vi } from 'vitest';

vi.mock('../memory/ContactModal', () => ({ ContactModal: () => null }));
vi.mock('../memory/ProjectModal', () => ({ ProjectModal: () => null }));
vi.mock('../board/BoardPanel', () => ({ BoardPanel: () => null }));
vi.mock('../atelier/AtelierPanel', () => ({ AtelierPanel: () => null }));
vi.mock('../prompts/PromptLibrary', () => ({ PromptLibrary: () => null }));
vi.mock('../settings/SettingsModal', () => ({
  SettingsModal: () => {
    throw new Promise(() => {});
  },
}));

import { PanelContainer } from './PanelContainer';

it('B-1920 : le repli des panneaux annonce le chargement', async () => {
  render(<PanelContainer onUserCommandsRefresh={vi.fn()} />);
  const repli = await screen.findByText('Chargement...');
  expect(repli).toHaveAttribute('role', 'status');
});
