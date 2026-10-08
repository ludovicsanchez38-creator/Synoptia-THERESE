import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';

const qa = '/private/tmp/therese-c17-wrapper-canary-187602c63a0b498a95d25c19843000a8';
const dest = '/Users/synoptia/Desktop/Dev Synoptia/Synoptia-THERESE-c15-codex/.app-loop/cycles/17/qualification/RPC-lot73-20261009/observations';
const workspace = '/Users/synoptia/Documents/Codex/2026-09-04/on';
const sources = [
  ['root14/ledger', `${qa}/ledger`],
  ['root14/session-rpc', `${qa}/session-rpc`],
  ['root14/binding.json', `${qa}/binding.json`],
  ['root14/decision.json', `${qa}/decision.json`],
  ['root14/result.json', `${qa}/wrapper-canary-result.json`],
  ['root14/readiness.json', `${qa}/runtime/readiness.json`],
  ['root14/calibration', `${qa}/runtime/calibration`],
  ['root14/chrome-stdout.log', `${qa}/auxiliary/aux-chrome-rpc-all-runtime_ui-visual_capture-network_capture/stdout.log`],
  ['root14/chrome-stderr.log', `${qa}/auxiliary/aux-chrome-rpc-all-runtime_ui-visual_capture-network_capture/stderr.log`],
  ['wrapper14-preparation', '/private/tmp/therese-c17-wrapper14-chromium-tmp-SYH6Mx'],
  ['wrapper14-static', '/private/tmp/therese-c17-wrapper14-static-controls-v8N7I1yV'],
  ['wrapper14-authority', '/private/tmp/therese-c17-root-fresh14-controls-ZNqqLhtv'],
  ['root14-independent-closure', '/private/tmp/therese-c17-independent-root14-review-0aSe6XZd'],
  ['root14-system-log', '/private/tmp/therese-c17-root14-chrome52371-log-sLdxZLOA'],
  ['full-builder-v2', '/private/tmp/therese-c17-full-physical-builder-v2-dxGPne'],
  ['full-builder-v3', '/private/tmp/therese-c17-full-physical-builder-v3-A0yyXP'],
  ['full-builders-independent-review', '/private/tmp/therese-c17-independent-full-builders-review-HDGgpJzx'],
  ['main-reviews/WRAPPER14.md', `${workspace}/WRAPPER14-REVUE-MAIN.md`],
  ['main-reviews/DIAGNOSTIC-MAIN14.md', `${workspace}/DIAGNOSTIC-MAIN14.md`],
  ['main-reviews/FULL-V2.md', `${workspace}/FULL-V2-REVUE-MAIN.md`],
  ['main-reviews/FULL-V3.md', `${workspace}/FULL-V3-REVUE-MAIN.md`],
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
  schema: 'c17-lot73-actual-observations-copy-v1', actor: '/root', copied_at: new Date().toISOString(),
  original_root: qa, scope: 'Closed WRAPPER14 RED, targeted Mach diagnostic and pure FULL v2/v3 preparations; no FULL or release',
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
