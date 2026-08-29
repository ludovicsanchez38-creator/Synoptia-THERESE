/**
 * Donne une vraie sémantique de stockage au localStorage mocké en no-op par
 * src/test/setup.ts. À appeler dans un beforeEach ; retourne le Map support
 * pour inspection/nettoyage.
 */
import { vi } from 'vitest';

export function installLocalStorageStub(): Map<string, string> {
  const store = new Map<string, string>();
  vi.mocked(localStorage.getItem).mockImplementation((k: string) => store.get(k) ?? null);
  vi.mocked(localStorage.setItem).mockImplementation(
    (k: string, v: string) => void store.set(k, String(v))
  );
  vi.mocked(localStorage.removeItem).mockImplementation((k: string) => void store.delete(k));
  vi.mocked(localStorage.clear).mockImplementation(() => store.clear());
  // Énumération : indispensable pour tester tout code qui balaie le stockage.
  vi.mocked(localStorage.key).mockImplementation((i: number) => [...store.keys()][i] ?? null);
  Object.defineProperty(localStorage, 'length', {
    get: () => store.size,
    configurable: true,
  });
  return store;
}
