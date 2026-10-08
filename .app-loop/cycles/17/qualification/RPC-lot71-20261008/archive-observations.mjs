import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

const qa = '/private/tmp/therese-c17-wrapper-canary-9818b6b4163e451892dbd3956e1bb492';
const probe = '/private/tmp/therese-c17-getconf-dirhelper-run-8a8cc69977f44172b868bc77b68b663d';
const dest = '/Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE-c15-codex/.app-loop/cycles/17/qualification/RPC-lot71-20261008/observations';
const sources = [
  ['root12/ledger', `${qa}/ledger`],
  ['root12/session-rpc', `${qa}/session-rpc`],
  ['root12/binding.json', `${qa}/binding.json`],
  ['root12/decision.json', `${qa}/decision.json`],
  ['root12/result.json', `${qa}/wrapper-canary-result.json`],
  ['root12/readiness.json', `${qa}/runtime/readiness.json`],
  ['root12/calibration', `${qa}/runtime/calibration`],
  ['wrapper12-preparation', '/private/tmp/therese-c17-wrapper12-metadata-parent-MtcoJZ'],
  ['wrapper12-static', '/private/tmp/therese-c17-wrapper12-static-controls-joVOhA'],
  ['wrapper12-authority', '/private/tmp/therese-c17-root-fresh12-controls-GelOt2Is'],
  ['wrapper12-independent-preparation', '/private/tmp/therese-c17-independent-wrapper12-review-fZezwyXq'],
  ['root11-independent-closure', '/private/tmp/therese-c17-independent-root11-review-bEkNPK4R'],
  ['root12-independent-closure', '/private/tmp/therese-c17-independent-root12-review-86tghbyh'],
  ['root12-chrome-diagnostic', '/private/tmp/therese-c17-root12-chrome40332-diagnostic-Bx0LdE'],
  ['root12-system-log', '/private/tmp/therese-c17-root12-chrome40332-log-authorized-uWc2pv'],
  ['getconf-preparation', '/private/tmp/therese-c17-getconf-dirhelper-XeZCB9'],
  ['getconf/suite-receipt.json', `${probe}/suite-receipt.json`],
  ['getconf/raw', `${probe}/raw`],
];
const privateOutputs = new Set(['main12', 'dirhelper'].flatMap(profile =>
  ['DARWIN_USER_DIR', 'DARWIN_USER_CACHE_DIR', 'DARWIN_USER_TEMP_DIR'].map(key =>
    `${probe}/raw/${profile}-${key}.stdout.bin`)));
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
  if (privateOutputs.has(src)) {
    if (st.uid !== 501 || (st.mode & 0o777) !== 0o600 || st.nlink !== 1) throw new Error(`Private output mode: ${src}`);
    special.push({original: src, kind: 'private-Darwin-stdout-not-copied-not-decoded',
      observed_original_stat: identity(st), sha256: hash(data), bytes: data.length});
    return;
  }
  items.push({src, relative, data, stat: identity(st), sha256: hash(data)});
}

for (const [relative, src] of sources) visit(src, relative);
const bytes = items.reduce((sum, item) => sum + item.data.length, 0);
if (items.length > 512 || bytes > 16 * 1024 * 1024) throw new Error('Bounded archive exceeded');
if (special.filter(item => item.kind === 'private-Darwin-stdout-not-copied-not-decoded').length !== 6)
  throw new Error('Six private outputs expected');
if (process.argv[2] !== '--copy') {
  console.log(JSON.stringify({files: items.length, bytes, private_outputs_excluded: 6, destination: dest, executed: false}));
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
for (const item of special) {
  if (JSON.stringify(identity(fs.lstatSync(item.original))) !== JSON.stringify(item.observed_original_stat))
    throw new Error(`Special source changed: ${item.original}`);
  if (item.sha256 && hash(fs.readFileSync(item.original)) !== item.sha256) throw new Error(`Private output changed: ${item.original}`);
}
const manifest = {
  schema: 'c17-lot71-actual-observations-copy-v1', actor: '/root', copied_at: new Date().toISOString(),
  original_root: qa, scope: 'Closed WRAPPER12 red observations and six-call differential getconf; no FULL or release',
  physical_source_identity_reverified_at_copy: true, copied_inode_or_ownership_proof_claimed: false,
  special_entries_not_copied: special,
  source_files: items.map(({src, relative, data, stat, sha256}) => ({original: src, archived: relative, sha256, bytes: data.length, observed_original_stat: stat})),
};
const data = Buffer.from(JSON.stringify(manifest, null, 2) + '\n');
fs.writeFileSync(path.join(dest, 'MANIFEST.json'), data, {flag: 'wx', mode: 0o600});
console.log(JSON.stringify({files: items.length, bytes, destination: dest, private_outputs_excluded: 6,
  manifest_sha256: hash(data), copied_and_reverified: true}));
