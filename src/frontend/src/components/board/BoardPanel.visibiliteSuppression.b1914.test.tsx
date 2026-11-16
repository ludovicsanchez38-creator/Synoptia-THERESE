import { fireEvent, render, screen } from '@testing-library/react';
import { compile } from 'tailwindcss';
import { expect, it, vi } from 'vitest';

const api = vi.hoisted(() => ({
  listBoardDecisions: vi.fn().mockResolvedValue([{ id: 'd1', question: 'Quelle décision prendre ?', confidence: 'high', created_at: '2026-09-01T10:00:00Z' }]),
  getOllamaStatus: vi.fn().mockResolvedValue({ available: false, base_url: '', models: [], error: null }),
}));
vi.mock('../../services/api', async () => ({
  ...await vi.importActual<typeof import('../../services/api')>('../../services/api'),
  ...api,
}));
vi.mock('../../lib/consent', () => ({ hasCloudConsent: () => true }));

import { BoardPanel } from './BoardPanel';

it('B-1914 : la suppression est visible sans survol et identifie la décision', async () => {
  render(<BoardPanel isOpen onClose={vi.fn()} />);
  fireEvent.click(await screen.findByRole('button', { name: /Historique/ }));
  await screen.findByText('Quelle décision prendre ?');
  const supprimer = screen.getByTitle('Supprimer');
  // Un title seul constitue déjà un nom accessible, mais il reste générique.
  expect(supprimer).toHaveAccessibleName(/Supprimer/);

  const tailwind = await compile('@tailwind utilities;');
  const style = document.createElement('style');
  style.textContent = tailwind.build([...supprimer.classList].filter((classe) => !classe.includes(':')));
  document.head.append(style);
  try {
    const opacite = getComputedStyle(supprimer).opacity;
    const valeur = !opacite ? 1 : opacite.endsWith('%') ? parseFloat(opacite) / 100 : Number(opacite);
    expect(valeur).toBe(1);
    expect(supprimer).toHaveAccessibleName('Supprimer la décision');
    expect(supprimer).toHaveAccessibleDescription('Quelle décision prendre ?');
  } finally {
    style.remove();
  }
});
