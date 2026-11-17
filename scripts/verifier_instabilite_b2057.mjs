/** B-2057 : rouge/vert sous la même lenteur, puis vingt processus sous charge.
 * Usage : node scripts/verifier_instabilite_b2057.mjs
 * Dépendances déjà installées seulement ; aucun serveur ni accès réseau.
 */
import { spawn, execFileSync } from 'node:child_process';
import { createWriteStream } from 'node:fs';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';
import { availableParallelism } from 'node:os';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('../', import.meta.url));
const frontend = resolve(root, 'src/frontend');
const relative = 'src/components/onboarding/LLMStep.verificationCle.b1348.test.tsx';
const target = resolve(frontend, relative);
const evidence = resolve(root, 'scratchpad/b2057', new Date().toISOString().replaceAll(':', '-'));
await mkdir(evidence, { recursive: true });
const fixed = await readFile(target, 'utf8');
const original = execFileSync('git', ['show', `HEAD:src/frontend/${relative}`], { cwd: root, encoding: 'utf8' });
const records = [];
const workers = [];
const stopped = [];
let interrupted = false;
process.on('SIGINT', () => { interrupted = true; });
process.on('SIGTERM', () => { interrupted = true; });

function slow(source) {
  const needle = 'apiMocks.setApiKey.mockResolvedValue(undefined);';
  if (source.split(needle).length !== 2) throw new Error('Point d’injection de la lenteur introuvable ou ambigu');
  // Horloge Node réelle : identique avant/après, même sous fake timers.
  return "import { setTimeout as ralentirB2057 } from 'node:timers/promises';\n"
    + source.replace(needle, 'apiMocks.setApiKey.mockImplementation(() => ralentirB2057(250));');
}

async function run(label, filtered = false) {
  if (interrupted) throw new Error('Recette interrompue');
  const report = resolve(evidence, `${label}.json`);
  const log = createWriteStream(resolve(evidence, `${label}.log`));
  const args = ['--no-install', 'vitest', 'run', relative];
  if (filtered) args.push('-t', 'indisponible');
  args.push('--reporter=json', `--outputFile=${report}`);
  const child = spawn('npx', args, {
    cwd: frontend,
    env: { ...process.env, npm_config_offline: 'true', npm_config_update_notifier: 'false', NO_COLOR: '1' },
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  child.stdout.pipe(log, { end: false });
  child.stderr.pipe(log, { end: false });
  const code = await new Promise((done, fail) => { child.on('close', done); child.on('error', fail); });
  await new Promise((done) => log.end(done));
  const data = JSON.parse(await readFile(report, 'utf8'));
  const row = { label, code, passed: data.numPassedTests, failed: data.numFailedTests, total: data.numTotalTests, success: data.success };
  records.push(row);
  console.log(JSON.stringify(row));
  await writeFile(resolve(evidence, 'comptes.json'), JSON.stringify(records, null, 2));
  return row;
}

try {
  await writeFile(resolve(evidence, 'original.tsx'), original);
  await writeFile(resolve(evidence, 'corrige.tsx'), fixed);
  await writeFile(target, slow(original));
  for (let i = 1; i <= 3; i++) {
    const r = await run(`avant-${i}`, true);
    if (r.code !== 1 || r.failed !== 1) throw new Error('Le test original ne reproduit pas le rouge attendu');
  }
  await writeFile(target, slow(fixed));
  for (let i = 1; i <= 3; i++) {
    const r = await run(`apres-lent-${i}`, true);
    if (r.code !== 0 || r.passed !== 1 || r.failed !== 0) throw new Error('Le correctif échoue sous la même lenteur');
  }
  await writeFile(target, fixed);
  const count = Math.max(2, Math.min(8, availableParallelism()));
  const load = `
    process.on('SIGTERM', () => { console.log(JSON.stringify({ pid: process.pid, cpu: process.cpuUsage() })); process.exit(0); });
    let n = 1;
    function burn() { const end = Date.now() + 100; while (Date.now() < end) n = Math.sqrt(n + 1); setImmediate(burn); }
    burn();
  `;
  for (let i = 0; i < count; i++) {
    const child = spawn(process.execPath, ['-e', load], { stdio: ['ignore', 'pipe', 'pipe'] });
    const log = createWriteStream(resolve(evidence, `cpu-${i + 1}.log`));
    child.stdout.pipe(log);
    child.stderr.pipe(log, { end: false });
    workers.push(child);
    stopped.push(new Promise((done) => child.on('close', done)));
  }
  console.log(`Charge : ${count} processus CPU, PID ${workers.map((w) => w.pid).join(', ')}.`);
  for (let i = 1; i <= 20; i++) await run(`charge-${String(i).padStart(2, '0')}`);
  if (records.slice(-20).some((r) => r.code !== 0 || r.passed !== 10 || r.failed !== 0)) {
    throw new Error('Au moins un passage sous charge est en échec');
  }
} finally {
  await writeFile(target, fixed);
  for (const child of workers) child.kill('SIGTERM');
  await Promise.all(stopped);
  console.log(`Preuves conservées : ${evidence}`);
}
