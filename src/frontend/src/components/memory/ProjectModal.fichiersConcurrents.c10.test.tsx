import { act, fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { FileMetadata, Project } from '../../services/api';

const api = vi.hoisted(() => ({ listProjectFiles: vi.fn(), uploadProjectFile: vi.fn(), deleteFile: vi.fn() }));
vi.mock('../../services/api', async () => ({
  ...await vi.importActual<typeof import('../../services/api')>('../../services/api'),
  ...api,
  listContacts: vi.fn().mockResolvedValue([]),
}));
vi.mock('./ProjectSyncSection', () => ({ ProjectSyncSection: () => null }));
import { ProjectModal } from './ProjectModal';

function attente<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => { resolve = done; });
  return { promise, resolve };
}
const projet = (id: string) => ({ id, name: `Projet ${id}`, status: 'active' }) as Project;
const fichier = (id: string) => ({ id, name: `${id}.pdf`, extension: '.pdf', size: 123, path: `/tmp/${id}.pdf` }) as FileMetadata;
const liste = (id: string) => ({ files: [fichier(id)], total: 1, truncated: false });
const props = { isOpen: true, onClose: vi.fn() };

describe('B-940 : les fichiers restent attachés au projet affiché', () => {
  beforeEach(() => { vi.clearAllMocks(); });

  it('ignore la réponse tardive de A après la réponse de B', async () => {
    const a = attente<ReturnType<typeof liste>>();
    const b = attente<ReturnType<typeof liste>>();
    api.listProjectFiles.mockImplementation((id: string) => id === 'A' ? a.promise : b.promise);
    const { rerender } = render(<ProjectModal {...props} project={projet('A')} />);
    rerender(<ProjectModal {...props} project={projet('B')} />);
    await act(async () => b.resolve(liste('fichier-B')));
    expect(screen.getByText('fichier-B.pdf')).toBeInTheDocument();
    await act(async () => a.resolve(liste('fichier-A')));
    expect(screen.queryByText('fichier-A.pdf')).not.toBeInTheDocument();
    expect(screen.getByText('fichier-B.pdf')).toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Supprimer le fichier fichier-A.pdf' })).toBeNull();
    expect(api.deleteFile).not.toHaveBeenCalled();
  });

  it('retire les fichiers de A dès que B est ouvert, même si B ne répond pas encore', async () => {
    api.listProjectFiles.mockResolvedValueOnce(liste('fichier-A')).mockReturnValue(new Promise(() => {}));
    const { rerender } = render(<ProjectModal {...props} project={projet('A')} />);
    await screen.findByText('fichier-A.pdf');
    rerender(<ProjectModal {...props} project={projet('B')} />);
    expect(screen.queryByText('fichier-A.pdf')).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: 'Supprimer le fichier fichier-A.pdf' })).toBeNull();
  });

  it('ignore une lecture achevée après fermeture puis réouverture du même projet', async () => {
    const ancienne = attente<ReturnType<typeof liste>>();
    api.listProjectFiles.mockReturnValueOnce(ancienne.promise).mockResolvedValue(liste('version-courante'));
    const a = projet('A');
    const { rerender } = render(<ProjectModal {...props} project={a} />);
    rerender(<ProjectModal {...props} isOpen={false} project={a} />);
    rerender(<ProjectModal {...props} project={a} />);
    await screen.findByText('version-courante.pdf');
    await act(async () => ancienne.resolve(liste('version-perimee')));
    expect(screen.queryByText('version-perimee.pdf')).not.toBeInTheDocument();
    expect(screen.getByText('version-courante.pdf')).toBeInTheDocument();
  });

  it('un upload commencé dans A ne recharge pas ses fichiers dans B à sa fin', async () => {
    const upload = attente<void>();
    api.uploadProjectFile.mockReturnValue(upload.promise);
    api.listProjectFiles.mockImplementation((id: string) => Promise.resolve(liste(`fichier-${id}`)));
    const { container, rerender } = render(<ProjectModal {...props} project={projet('A')} />);
    await screen.findByText('fichier-A.pdf');
    fireEvent.change(container.querySelector('input[type=file]')!, { target: { files: [new File(['test'], 'ajout.pdf')] } });
    expect(api.uploadProjectFile).toHaveBeenCalledWith(expect.any(File), 'A');
    rerender(<ProjectModal {...props} project={projet('B')} />);
    await screen.findByText('fichier-B.pdf');
    await act(async () => upload.resolve());
    expect(api.listProjectFiles.mock.calls.map(([id]) => id)).toEqual(['A', 'B']);
    expect(screen.getByText('fichier-B.pdf')).toBeInTheDocument();
    expect(screen.queryByText('fichier-A.pdf')).not.toBeInTheDocument();
  });
});
