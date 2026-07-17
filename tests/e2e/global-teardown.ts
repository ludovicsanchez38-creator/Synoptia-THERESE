/**
 * Détruit le data dir du backend E2E jetable (revue 0.40). Le trap bash du
 * script backend ne suffit pas : Playwright termine ses webServers par
 * SIGKILL, ce teardown Node est le seul passage garanti.
 */
import { rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { E2E_BACKEND_PORT } from './stories/helpers/backend';

export default function globalTeardown(): void {
  const dataDir = join(process.env.TMPDIR ?? tmpdir(), `therese-e2e-${E2E_BACKEND_PORT}`);
  rmSync(dataDir, { recursive: true, force: true });
}
