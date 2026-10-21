import { render, screen } from '@testing-library/react';
import { expect, it, vi } from 'vitest';
import { ProfileStep } from './ProfileStep';

vi.mock('../../services/api', () => ({ getConfigStats: vi.fn().mockResolvedValue({}) }));

it('R6 : propose un contexte concret de TPE, sans offre commerciale propre à Synoptïa', () => {
  render(<ProfileStep onNext={vi.fn()} onBack={vi.fn()} />);
  const exemple = screen.getByLabelText('Contexte additionnel').getAttribute('placeholder');
  expect(exemple).toContain('entreprise de plomberie');
  expect(exemple).toContain('devis');
  expect(exemple).not.toMatch(/FORGER|Synopt|490/);
});
