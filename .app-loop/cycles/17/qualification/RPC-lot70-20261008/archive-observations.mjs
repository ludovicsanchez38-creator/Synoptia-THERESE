import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

const qa = '/private/tmp/therese-c17-wrapper-canary-eff7b4e4f24649dd8628503bc7bfc8b3';
const dest = '/Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE-c15-codex/.app-loop/cycles/17/qualification/RPC-lot70-20261008/observations';
const sources = [
  ['root11/ledger', `${qa}/ledger`],
  ['root11/session-rpc', `${qa}/session-rpc`],
  ['root11/binding.json', `${qa}/binding.json`],
  ['root11/decision.json', `${qa}/decision.json`],
  ['root11/result.json', `${qa}/wrapper-canary-result.json`],
  ['root11/readiness.json', `${qa}/runtime/readiness.json`],
  ['root11/calibration', `${qa}/runtime/calibration`],
  ['static-v3', '/private/tmp/therese-c17-root11-static-controls-v3-hK9Iql'],
  ['static-v4', '/private/tmp/therese-c17-root11-static-controls-v4-25ix3j'],
  ['static-v5', '/private/tmp/therese-c17-root11-static-controls-v5-CWh0zu'],
  ['chrome-signature-red', '/private/tmp/therese-c17-chrome-recheck-OiYEpV'],
  ['chrome-signature-green', '/private/tmp/therese-c17-chrome-recheck-oQS1S0'],
  ['chrome-diagnostic', '/private/tmp/therese-c17-root11-chrome34667-diagnostic-PrqxhI'],
  ['budget-before.json', '/private/tmp/therese-c17-resume-deadline-20261008-GvYugGrD/budget-before.json'],
];
const items = [];
const special = [];
const hash = data => crypto.createHash('sha256').update(data).digest('hex');
const identity = st => [st.dev, st.ino, st.mode, st.uid, st.gid, st.nlink, st.size, st.mtimeMs, st.ctimeMs];
function visit(src, relative) {
  const st = fs.lstatSync(src);
  if (fs.realpathSync(src) !== src || st.isSymbolicLink()) throw new Error(`Noncanonical source: ${src}`);
  if (st.isDirectory()) {
    for (const name of fs.readdirSync(src).sort()) visit(path.join(src, name), path.join(relative, name));
    return;
  }
  if (src === `${qa}/session-rpc/peer.sock` && st.isSocket() && st.uid === 501 && st.nlink === 1) {
    special.push({original: src, kind: 'socket-not-copied-not-opened', observed_original_stat: identity(st)});
    return;
  }
  if (!st.isFile() || st.size > 3_000_000) throw new Error(`Nonregular/oversized source: ${src}`);
  if (st.nlink !== 1) {
    const inProtocolTree = src.startsWith(`${qa}/ledger/`) || src.startsWith(`${qa}/session-rpc/`);
    const pair = src.endsWith('.pending') ? src.slice(0, -8) : `${src}.pending`;
    const paired = inProtocolTree && st.nlink === 2 && fs.existsSync(pair) && fs.lstatSync(pair);
    if (!paired || !paired.isFile() || paired.dev !== st.dev || paired.ino !== st.ino || paired.nlink !== 2)
      throw new Error(`Unreviewed hardlink: ${src}`);
  }
  const data = fs.readFileSync(src);
  if (JSON.stringify(identity(st)) !== JSON.stringify(identity(fs.lstatSync(src)))) throw new Error(`Source changed: ${src}`);
  items.push({src, relative, data, stat: identity(st), sha256: hash(data)});
}
for (const [relative, src] of sources) visit(src, relative);
const bytes = items.reduce((sum, item) => sum + item.data.length, 0);
if (items.length > 512 || bytes > 16 * 1024 * 1024) throw new Error('Bounded archive exceeded');
if (process.argv[2] !== '--copy') {
  console.log(JSON.stringify({files: items.length, bytes, destination: dest, executed: false}));
  process.exit(0);
}
if (fs.existsSync(dest)) throw new Error('Destination exists; no overwrite');
fs.mkdirSync(dest, {mode: 0o700});
for (const item of items) {
  const target = path.join(dest, item.relative);
  fs.mkdirSync(path.dirname(target), {recursive: true, mode: 0o700});
  fs.writeFileSync(target, item.data, {flag: 'wx', mode: 0o600});
  if (hash(fs.readFileSync(target)) !== item.sha256 || hash(fs.readFileSync(item.src)) !== item.sha256
      || JSON.stringify(identity(fs.lstatSync(item.src))) !== JSON.stringify(item.stat)) throw new Error(`Verification failed: ${item.src}`);
}
const manifest = {
  schema: 'c17-lot70-actual-observations-copy-v1', actor: '/root', copied_at: new Date().toISOString(),
  original_root: qa, scope: 'Closed WRAPPER11 observations and static/signature/diagnostic controls; not FULL, not a release',
  physical_source_identity_reverified_at_copy: true, copied_inode_or_ownership_proof_claimed: false,
  special_entries_not_copied: special,
  source_files: items.map(({src, relative, data, stat, sha256}) => ({original: src, archived: relative, sha256, bytes: data.length, observed_original_stat: stat})),
};
for (const item of special) {
  if (JSON.stringify(identity(fs.lstatSync(item.original))) !== JSON.stringify(item.observed_original_stat))
    throw new Error(`Special source changed: ${item.original}`);
}
const data = Buffer.from(JSON.stringify(manifest, null, 2) + '\n');
fs.writeFileSync(path.join(dest, 'MANIFEST.json'), data, {flag: 'wx', mode: 0o600});
console.log(JSON.stringify({files: items.length, bytes, destination: dest, manifest_sha256: hash(data), copied_and_reverified: true}));
