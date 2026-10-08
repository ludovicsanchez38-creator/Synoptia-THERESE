#!/usr/bin/env node
// Supplément lot 68 : ce fichier n'archive rien sans --execute et les deux pins externes.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import zlib from 'node:zlib';

const HERE = path.dirname(new URL(import.meta.url).pathname);
const PLAN_PATH = path.join(HERE, 'PLAN.json');
const LIMIT = 64 * 1024 * 1024;
const MAX_MEMBERS = 4096;
const SOURCE_ROOT = '/private/tmp/therese-c17-direct-source-F4KirwuR';
const SOURCE_LITERALS = new Set([
  'source/.git/HEAD',
  'source/pyproject.toml',
  'source/uv.lock',
  'source/package-lock.json',
  'source/src/frontend/package-lock.json',
]);

function fail(message) { throw new Error(message); }
function sha(bytes) { return crypto.createHash('sha256').update(bytes).digest('hex'); }
function isHex(value) { return typeof value === 'string' && /^[a-f0-9]{64}$/.test(value); }
function exactChild(root, file) {
  if (path.resolve(root) !== root || path.resolve(file) !== file) fail(`chemin non absolu canonique: ${file}`);
  const rel = path.relative(root, file);
  if (!rel || rel === '..' || rel.startsWith(`..${path.sep}`) || path.isAbsolute(rel)) fail(`hors racine: ${file}`);
  return rel;
}
function safeFile(file, root) {
  exactChild(root, file);
  const st = fs.lstatSync(file);
  if (!st.isFile() || st.isSymbolicLink()) fail(`non-fichier régulier: ${file}`);
  if (fs.realpathSync(file) !== file) fail(`lien physique ou parent non canonique: ${file}`);
  return st;
}
function sameStat(a, b) {
  return ['dev','ino','size','mtimeMs','mode','uid','gid','nlink'].every(key => a[key] === b[key]);
}
function readStable(file, root) {
  const before = safeFile(file, root);
  const fd = fs.openSync(file, fs.constants.O_RDONLY | (fs.constants.O_NOFOLLOW ?? 0));
  let bytes;
  try {
    const opened = fs.fstatSync(fd);
    if (!sameStat(before, opened)) fail(`mutation ouverture: ${file}`);
    bytes = fs.readFileSync(fd);
    if (!sameStat(opened, fs.fstatSync(fd))) fail(`mutation lecture: ${file}`);
  } finally {
    fs.closeSync(fd);
  }
  if (!sameStat(before, safeFile(file, root)) || bytes.length !== before.size) fail(`mutation après lecture: ${file}`);
  return { file, bytes, sha256: sha(bytes), size: bytes.length,
    mode: before.mode & 0o7777, uid: before.uid, gid: before.gid,
    mtime: Math.floor(before.mtimeMs / 1000), identity: before };
}
function readJsonPinned(file, root, expectedSha) {
  const record = readStable(file, root);
  if (record.sha256 !== expectedSha) fail(`pin SHA divergent: ${file}`);
  try { return JSON.parse(record.bytes.toString('utf8')); }
  catch { fail(`JSON invalide: ${file}`); }
}
function collectRecursive(root) {
  const files = [];
  const excluded = [];
  let visited = 0;
  function walk(dir) {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true }).sort((a,b) => a.name.localeCompare(b.name))) {
      if (++visited > 10000) fail(`limite de parcours dépassée: ${root}`);
      const full = path.join(dir, entry.name);
      exactChild(root, full);
      if (entry.name.startsWith('._') || entry.name === '__pycache__') {
        excluded.push(path.relative(root, full)); continue;
      }
      if (entry.name === '.git' || entry.name === 'node_modules' || entry.name === '.venv' || entry.name === 'venv')
        fail(`dépendances ou Git non sélectionnés: ${full}`);
      const st = fs.lstatSync(full);
      if (st.isSymbolicLink()) fail(`lien symbolique refusé: ${full}`);
      if (st.isSocket()) { excluded.push(path.relative(root, full)); continue; }
      if (st.isDirectory()) { if (fs.realpathSync(full) !== full) fail(`parent non canonique: ${full}`); walk(full); continue; }
      if (!st.isFile()) fail(`type non régulier refusé: ${full}`);
      files.push(full);
      if (files.length > MAX_MEMBERS) fail(`trop de fichiers: ${root}`);
    }
  }
  walk(root);
  if (files.length === 0) fail(`répertoire vide: ${root}`);
  return { files, excluded };
}
function collectSourceSelected(root, anchorSha) {
  if (root !== SOURCE_ROOT) fail('racine source inattendue');
  const indexPath = path.join(root, 'proofs', 'INDEX.json');
  const index = readJsonPinned(indexPath, root, anchorSha);
  if (!Array.isArray(index.selected_refs) || index.selected_refs.length !== 24) fail('selected_refs != 24');
  const seen = new Set();
  const seenSource = new Set();
  const expected = new Map();
  for (const ref of index.selected_refs) {
    if (!ref || typeof ref.path !== 'string' || !isHex(ref.sha256) || !Number.isSafeInteger(ref.bytes) || ref.bytes < 0)
      fail('selected_ref invalide');
    const rel = exactChild(root, ref.path);
    if (seen.has(rel)) fail(`selected_ref dupliquée: ${rel}`);
    if (!rel.startsWith('proofs/') && !SOURCE_LITERALS.has(rel)) fail(`selected_ref imprévue: ${rel}`);
    if (rel.startsWith('proofs/') && (rel.includes('/.git/') || rel.includes('/node_modules/') || rel.includes('/venv'))) fail(`preuve hors périmètre: ${rel}`);
    if (SOURCE_LITERALS.has(rel)) seenSource.add(rel);
    seen.add(rel); expected.set(ref.path, ref);
  }
  if (seenSource.size !== 5 || [...SOURCE_LITERALS].some(x => !seenSource.has(x))) fail('cinq littéraux source manquants');
  if (seen.size !== 24 || [...seen].filter(x => x.startsWith('proofs/')).length !== 19) fail('cardinalité preuves source erronée');
  return { files: [indexPath, ...index.selected_refs.map(x => x.path)], excluded: [], expected };
}
function validatePlan(plan) {
  if (plan.schema !== 'therese-c17-lot68-supplement-plan-v1' || plan.status !== 'prepared_only_not_executed' ||
      plan.archive_limit_bytes !== LIMIT || !Array.isArray(plan.archives) || plan.archives.length !== 12)
    fail('plan ou cardinalité inattendus');
  const roots = new Set(), ids = new Set();
  for (const row of plan.archives) {
    if (!row || !/^[0-9]{2}-[a-z0-9-]+$/.test(row.id) || ids.has(row.id) ||
        typeof row.root !== 'string' || roots.has(row.root) || !row.root.startsWith('/private/tmp/therese-c17-') ||
        typeof row.anchor !== 'string' || row.anchor.startsWith('/') || row.anchor.includes('..') || !isHex(row.anchor_sha256))
      fail('ligne de plan non fermée');
    if (row.root === plan.native_root_deferred || row.root.includes('wrapper-canary-b90937')) fail('ROOT10 natif différé');
    if (row.root === SOURCE_ROOT && row.selection !== 'index_selected_refs_exactly_24') fail('source sans sélection fermée');
    if (row.root !== SOURCE_ROOT && row.selection) fail('sélection spéciale hors source');
    ids.add(row.id); roots.add(row.root);
  }
}
function prepareRow(row) {
  const root = row.root;
  const st = fs.lstatSync(root);
  if (!st.isDirectory() || st.isSymbolicLink() || fs.realpathSync(root) !== root) fail(`racine non physique: ${root}`);
  const anchorPath = path.join(root, row.anchor);
  const anchor = readStable(anchorPath, root);
  if (anchor.sha256 !== row.anchor_sha256) fail(`ancre différente: ${anchorPath}`);
  if (row.result) {
    const receipt = readJsonPinned(path.join(root, row.result.file), root, row.anchor_sha256);
    if (receipt[row.result.field] !== row.result.equals) fail(`classification rouge/vert non prouvée: ${root}`);
  }
  const selection = row.selection ? collectSourceSelected(root, row.anchor_sha256) : collectRecursive(root);
  if (!selection.files.includes(anchorPath)) fail(`ancre absente de sélection: ${root}`);
  return { ...row, ...selection };
}
function tarPath(name) {
  if (name.startsWith('/') || name.split('/').some(x => !x || x === '.' || x === '..') || name.includes('\\') || name.includes('\0'))
    fail(`membre TAR non sûr: ${name}`);
  const b = Buffer.byteLength(name);
  if (b <= 100) return { name, prefix: '' };
  for (let i = name.lastIndexOf('/'); i > 0; i = name.lastIndexOf('/', i-1)) {
    const prefix = name.slice(0,i), suffix = name.slice(i+1);
    if (Buffer.byteLength(prefix) <= 155 && Buffer.byteLength(suffix) <= 100) return { name:suffix, prefix };
  }
  fail(`chemin trop long pour ustar: ${name}`);
}
function writeText(block, offset, length, value) {
  const b = Buffer.from(String(value), 'utf8');
  if (b.length > length) fail('champ ustar trop long');
  b.copy(block, offset);
}
function octal(value, width) {
  if (!Number.isSafeInteger(value) || value < 0) fail('valeur ustar non entière');
  const s = value.toString(8);
  if (s.length > width - 1) fail('valeur ustar trop longue');
  return s.padStart(width-1,'0') + '\0';
}
function tarHeader(member, record) {
  const { name, prefix } = tarPath(member);
  const b = Buffer.alloc(512);
  writeText(b,0,100,name); writeText(b,100,8,octal(record.mode,8));
  writeText(b,108,8,octal(record.uid,8)); writeText(b,116,8,octal(record.gid,8));
  writeText(b,124,12,octal(record.size,12)); writeText(b,136,12,octal(record.mtime,12));
  b.fill(32,148,156); b[156] = 48;
  writeText(b,257,6,'ustar\0'); writeText(b,263,2,'00'); writeText(b,345,155,prefix);
  const sum = b.reduce((a,x) => a+x,0);
  const check = sum.toString(8).padStart(6,'0');
  if (check.length !== 6) fail('checksum ustar trop long');
  writeText(b,148,6,check); b[154]=0; b[155]=32;
  return b;
}
function buildTar(records) {
  let total = 1024;
  const parts = [];
  for (const record of records) {
    const padded = Math.ceil(record.size/512)*512;
    total += 512 + padded;
    if (total > LIMIT) fail('archive ustar non compressée > 64 MiB');
    parts.push(tarHeader(record.member, record), record.bytes);
    if (padded !== record.size) parts.push(Buffer.alloc(padded-record.size));
  }
  parts.push(Buffer.alloc(1024));
  return Buffer.concat(parts,total);
}
function parseOctal(b) {
  const s = b.toString('ascii').replace(/\0.*$/s,'').trim();
  if (!/^[0-7]+$/.test(s)) fail('nombre TAR invalide');
  return parseInt(s,8);
}
function tarString(b) { return b.toString('utf8').replace(/\0.*$/s,''); }
function verifyTar(gzip, expected) {
  const tar = zlib.gunzipSync(gzip, { maxOutputLength: LIMIT });
  if (tar.length > LIMIT || tar.length % 512 !== 0) fail('taille TAR invalide');
  const pending = new Map(expected.map(x => [x.member,x]));
  let pos=0, count=0;
  while (pos + 512 <= tar.length) {
    const block=tar.subarray(pos,pos+512); pos+=512;
    if (block.every(x=>x===0)) {
      if (tar.length-pos < 512 || !tar.subarray(pos).every(x=>x===0)) fail('fin TAR non nulle');
      if (pending.size) fail('membres TAR manquants');
      return count;
    }
    const rawCheck=parseOctal(block.subarray(148,156));
    const checked=Buffer.from(block); checked.fill(32,148,156);
    if (checked.reduce((a,x)=>a+x,0)!==rawCheck) fail('checksum TAR faux');
    if (tarString(block.subarray(257,263))!=='ustar') fail('format TAR inattendu');
    if (block[156]!==48 && block[156]!==0) fail('membre TAR non régulier');
    const name=tarString(block.subarray(0,100)), prefix=tarString(block.subarray(345,500));
    const member=prefix ? `${prefix}/${name}` : name;
    tarPath(member);
    const ref=pending.get(member);
    if (!ref) fail(`membre TAR supplémentaire ou répété: ${member}`);
    const size=parseOctal(block.subarray(124,136));
    if (size!==ref.size || parseOctal(block.subarray(100,108))!==ref.mode ||
        parseOctal(block.subarray(108,116))!==ref.uid || parseOctal(block.subarray(116,124))!==ref.gid)
      fail(`métadonnées TAR divergentes: ${member}`);
    if (pos+size>tar.length || sha(tar.subarray(pos,pos+size))!==ref.sha256) fail(`octets TAR divergents: ${member}`);
    pos+=Math.ceil(size/512)*512;
    pending.delete(member); count++;
  }
  fail('TAR sans fermeture');
}
function archiveRow(row, outDir) {
  const records=[];
  for (const file of row.files) {
    const rel=exactChild(row.root,file);
    const data=readStable(file,row.root);
    const expected=row.expected?.get(file);
    if (expected && (data.sha256!==expected.sha256 || data.size!==expected.bytes)) fail(`selected_ref divergente: ${file}`);
    const member=`${row.id}/${rel.split(path.sep).join('/')}`;
    tarPath(member);
    records.push({ ...data, member });
  }
  if (records.length<1 || records.length>MAX_MEMBERS) fail(`cardinalité archive invalide: ${row.id}`);
  records.sort((a,b)=>a.member.localeCompare(b.member));
  const tar=buildTar(records);
  const gzip=zlib.gzipSync(tar,{level:9,mtime:0});
  if (gzip.length>LIMIT) fail(`archive compressée > 64 MiB: ${row.id}`);
  const archive=path.join(outDir,`${row.id}.tar.gz`);
  const fd=fs.openSync(archive,'wx',0o600);
  try { fs.writeFileSync(fd,gzip); fs.fsyncSync(fd); }
  finally { fs.closeSync(fd); }
  const saved=readStable(archive,outDir);
  if (saved.sha256!==sha(gzip) || saved.size!==gzip.length) fail(`archive altérée après écriture: ${archive}`);
  const count=verifyTar(saved.bytes,records);
  for (const old of records) {
    const fresh=readStable(old.file,row.root);
    if (fresh.sha256!==old.sha256 || fresh.size!==old.size || !sameStat(fresh.identity,old.identity))
      fail(`entrée modifiée après archivage: ${old.file}`);
  }
  return { id:row.id,class:row.class,archive,sha256:saved.sha256,bytes:saved.size,member_count:count,
    excluded:row.excluded, members:records.map(x=>({path:x.member,sha256:x.sha256,bytes:x.size,mode:x.mode,uid:x.uid,gid:x.gid})) };
}
function main() {
  const args=process.argv.slice(2);
  if (args.length!==5 || args[0]!=='--execute' || args[1]!=='--expected-plan-sha256' || args[3]!=='--out-dir' || !isHex(args[2]))
    fail('usage: node archive_lot68_supplement.mjs --execute --expected-plan-sha256 <sha256> --out-dir /private/tmp/therese-c17-lot68-supplement-archive-<id>');
  const outDir=args[4];
  if (!/^\/private\/tmp\/therese-c17-lot68-supplement-archive-[A-Za-z0-9_-]+$/.test(outDir) || outDir===HERE || fs.existsSync(outDir))
    fail('destination non neuve ou hors périmètre');
  const planBytes=fs.readFileSync(PLAN_PATH);
  if (sha(planBytes)!==args[2]) fail('pin externe PLAN.json divergent');
  const plan=JSON.parse(planBytes.toString('utf8'));
  validatePlan(plan);
  const rows=plan.archives.map(prepareRow);
  fs.mkdirSync(outDir,{mode:0o700});
  const done=[];
  try {
    for (const row of rows) done.push(archiveRow(row,outDir));
    const receipt={schema:'therese-c17-lot68-supplement-archive-receipt-v1',status:'archives_verified_not_runtime_qualification',
      plan_sha256:args[2],max_archive_bytes:LIMIT,archive_count:done.length,archives:done,
      native_root_deferred:plan.native_root_deferred};
    fs.writeFileSync(path.join(outDir,'receipt.json'),JSON.stringify(receipt,null,2)+'\n',{flag:'wx',mode:0o600});
    process.stdout.write(JSON.stringify({status:receipt.status,receipt:path.join(outDir,'receipt.json'),archive_count:done.length})+'\n');
  } catch(error) {
    const failed={schema:'therese-c17-lot68-supplement-archive-failure-v1',status:'archive_incomplete_not_qualified',
      plan_sha256:args[2],error:String(error),completed_archives:done.map(x=>({id:x.id,sha256:x.sha256,bytes:x.bytes}))};
    fs.writeFileSync(path.join(outDir,'failure.json'),JSON.stringify(failed,null,2)+'\n',{flag:'wx',mode:0o600});
    throw error;
  }
}
main();
