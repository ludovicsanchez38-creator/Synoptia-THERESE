import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../services/api', () => ({ checkHealth: vi.fn() }));
import { useBackendStore } from '../../hooks/useBackend';
import { AboutTab } from './AboutTab';

function verifier(version: string, tag: unknown) {
  useBackendStore.setState({ version });
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
    ok: true, json: async () => [{ tag_name: tag, assets: [] }],
  }));
  render(<AboutTab />);
  fireEvent.click(screen.getByRole('button', { name: 'Vérifier les mises à jour' }));
}

describe('R1-2 : SemVer et versions illisibles', () => {
  afterEach(() => vi.unstubAllGlobals());

  it.each([
    ['0.83.0', 'v0.83.1+build.1', true],
    ['0.83.0-alpha.10+build.1', 'v0.83.0-alpha.2+build.1', false],
    ['0.83.0-alpha.2+build.9', 'v0.83.0-alpha.10+build.1', true],
    ['0.83.0-alpha.2+build.9', 'v0.83.0-alpha.2+autre', false],
    ['0.83.0-beta+build.9', 'v0.83.0-beta+autre', false],
    ['0.83.0-alpha.2', 'v0.83.0-alpha.beta', true],
    ['0.83.0-alpha.beta', 'v0.83.0-alpha.2', false],
    ['0.83.0-alpha.9007199254740992', 'v0.83.0-alpha.9007199254740993', true],
  ])('%s / %s : mise à jour=%s', async (version, tag, disponible) => {
    verifier(version, tag);
    expect(await screen.findByText(disponible ? /Nouvelle version disponible/ : /THÉRÈSE est à jour/)).toBeInTheDocument();
    expect(screen.queryByRole('alert')).not.toBeInTheDocument();
  });

  it.each([
    ['0.83.0', 'inconnue'], ['0.83.0', 'v1.2.erreur'],
    ['illisible', 'v1.0.0'], ['0.83.0', 'v1.0.0-alpha.01'],
    ['0.83.0', 'v1.0'], ['0.83.0', 'v01.0.0'],
    ['0.83.0', 'v1.0.0+'], ['0.83.0', null],
  ])('%s / %s : un numéro illisible reste une erreur avec un lien manuel', async (version, tag) => {
    verifier(version, tag);
    expect(await screen.findByRole('alert')).toHaveTextContent(/version.*illisible/i);
    expect(screen.queryByText(/THÉRÈSE est à jour|Nouvelle version disponible/)).not.toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Télécharger THÉRÈSE manuellement' })).toHaveAttribute('href', 'https://synoptia.fr/therese/beta/');
  });
});
