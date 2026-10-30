import { render, screen } from '@testing-library/react';
import { expect, it, vi } from 'vitest';
import { WelcomeStep } from './WelcomeStep';

it('décrit le stockage local et le choix du service sans promesse de souveraineté', () => {
  render(<WelcomeStep onNext={vi.fn()} />);
  expect(screen.queryByText(/assistante IA souveraine/)).not.toBeInTheDocument();
  expect(screen.getByText(/Tes données sont stockées sur ton ordinateur/)).toBeInTheDocument();
});
