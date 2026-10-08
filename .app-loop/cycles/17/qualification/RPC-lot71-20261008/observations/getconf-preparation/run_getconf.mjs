import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

// Diagnostic préparé, non exécuté par son auteur. Le stdout peut contenir un
// chemin Darwin personnel : il reste brut, privé (0600) et n'est jamais décodé.
const here = path.dirname(fileURLToPath(import.meta.url));
const profiles = Object.freeze([
  { name: 'main12', file: path.join(here, 'profiles/main12.sb'), sha256: '980b12368975718d33dba1572ce94da04ca378ca827df1be10a1ed15a7104cdb' },
  { name: 'dirhelper', file: path.join(here, 'profiles/dirhelper.sb'), sha256: '2ecae3a24ec871a44827b3f712ced1ef5e84d8f778906c37b3a5b51bb374dcdf' },
]);
const keys = Object.freeze(['DARWIN_USER_DIR', 'DARWIN_USER_CACHE_DIR', 'DARWIN_USER_TEMP_DIR']);
const maxOutputBytes = 65536;
const timeoutMs = 10000;
const outputPattern = /^\/private\/tmp\/therese-c17-getconf-dirhelper-run-[0-9a-f]{32}$/;

function digest(bytes) {
  return crypto.createHash('sha256').update(bytes).digest('hex');
}

function requireCondition(condition, message) {
  if (!condition) throw new Error(message);
}

function exclusiveBytes(file, bytes) {
  fs.writeFileSync(file, bytes, { flag: 'wx', mode: 0o600 });
  return { path: file, sha256: digest(bytes), bytes: bytes.length };
}

function exclusiveJson(file, value) {
  return exclusiveBytes(file, Buffer.from(JSON.stringify(value, null, 2) + '\n', 'utf8'));
}

function verifyProfiles() {
  const [base, candidate] = profiles.map((profile) => {
    const stat = fs.lstatSync(profile.file);
    requireCondition(stat.isFile() && !stat.isSymbolicLink() && stat.nlink === 1, 'Profil non régulier ou lié');
    const bytes = fs.readFileSync(profile.file);
    requireCondition(digest(bytes) === profile.sha256, 'Empreinte du profil différente');
    return bytes;
  });
  const onlyDelta = Buffer.from('(allow mach-lookup (global-name "com.apple.bsd.dirhelper"))\n');
  requireCondition(candidate.equals(Buffer.concat([base, onlyDelta])), 'Delta du profil non unique');
}

function createPrivateLayout(output) {
  requireCondition(outputPattern.test(output), 'Racine de sortie non admise');
  requireCondition(fs.realpathSync('/private/tmp') === '/private/tmp', 'TMP parent non canonique');
  requireCondition(!fs.existsSync(output), 'Sortie déjà présente');
  fs.mkdirSync(output, { mode: 0o700 });
  requireCondition(fs.realpathSync(output) === output, 'Sortie non canonique');
  const qaRoot = path.join(output, 'qa');
  const auxiliaryParent = path.join(qaRoot, 'auxiliary');
  const auxiliaryRoot = path.join(auxiliaryParent, 'getconf-probe');
  const homeRoot = path.join(auxiliaryRoot, 'home');
  const tmpRoot = path.join(auxiliaryRoot, 'tmp');
  const rawRoot = path.join(output, 'raw');
  for (const dir of [qaRoot, auxiliaryParent, auxiliaryRoot, homeRoot, tmpRoot, rawRoot]) {
    fs.mkdirSync(dir, { mode: 0o700 });
    requireCondition(fs.realpathSync(dir) === dir, 'Répertoire QA non canonique');
  }
  return { qaRoot, auxiliaryParent, auxiliaryRoot, homeRoot, tmpRoot, rawRoot };
}

function runOne(profile, key, layout, environment, definitions) {
  const label = `${profile.name}-${key}`;
  const argv = [
    '-D', `QA_ROOT=${layout.qaRoot}`,
    '-D', `AUXILIARY_PARENT=${layout.auxiliaryParent}`,
    '-D', `AUXILIARY_ROOT=${layout.auxiliaryRoot}`,
    '-D', `HOME_ROOT=${layout.homeRoot}`,
    '-D', `TMP_ROOT=${layout.tmpRoot}`,
    '-f', profile.file,
    '/usr/bin/getconf', key,
  ];
  const startedAt = new Date().toISOString();
  const startedMonotonic = process.hrtime.bigint();
  const result = spawnSync('/usr/bin/sandbox-exec', argv, {
    cwd: layout.qaRoot,
    env: environment,
    encoding: null,
    timeout: timeoutMs,
    killSignal: 'SIGKILL',
    maxBuffer: maxOutputBytes,
    windowsHide: true,
  });
  const elapsedMs = Number(process.hrtime.bigint() - startedMonotonic) / 1e6;
  const stdout = Buffer.isBuffer(result.stdout) ? result.stdout : Buffer.alloc(0);
  const stderr = Buffer.isBuffer(result.stderr) ? result.stderr : Buffer.alloc(0);
  const stdoutRef = exclusiveBytes(path.join(layout.rawRoot, `${label}.stdout.bin`), stdout);
  const stderrRef = exclusiveBytes(path.join(layout.rawRoot, `${label}.stderr.bin`), stderr);
  const caseReceipt = {
    schema: 'c17-root12-getconf-dirhelper-case-v1',
    diagnostic_only: true,
    started_at: startedAt,
    completed_at: new Date().toISOString(),
    elapsed_ms: elapsedMs,
    timeout_ms: timeoutMs,
    max_output_bytes: maxOutputBytes,
    profile: profile.name,
    profile_ref: { path: profile.file, sha256: profile.sha256, bytes: fs.statSync(profile.file).size },
    key,
    executable: '/usr/bin/sandbox-exec',
    argv,
    cwd: layout.qaRoot,
    qa_parameter_paths: definitions,
    environment_keys: Object.keys(environment).sort(),
    pid: result.pid ?? null,
    exit_code: result.status,
    signal: result.signal,
    error: result.error ? { code: result.error.code ?? null, message: result.error.message } : null,
    stdout_ref: stdoutRef,
    stderr_ref: stderrRef,
    stdout_never_decoded_or_printed: true,
    returned_path_never_opened_or_listed: true,
  };
  const receiptRef = exclusiveJson(path.join(layout.rawRoot, `${label}.receipt.json`), caseReceipt);
  return { profile: profile.name, key, exit_code: result.status, signal: result.signal,
    error_code: result.error?.code ?? null, elapsed_ms: elapsedMs, receipt_ref: receiptRef };
}

function main() {
  const args = process.argv.slice(2);
  requireCondition(args.length === 3 && args[0] === '--execute' && args[1] === '--out',
    'Usage fermé : node run_getconf.mjs --execute --out /private/tmp/therese-c17-getconf-dirhelper-run-<32hex>');
  requireCondition(process.getuid() === 501, 'UID différent du Chrome QA MAIN12');
  process.umask(0o077);
  verifyProfiles();
  const layout = createPrivateLayout(args[2]);
  const definitions = {
    QA_ROOT: layout.qaRoot,
    AUXILIARY_PARENT: layout.auxiliaryParent,
    AUXILIARY_ROOT: layout.auxiliaryRoot,
    HOME_ROOT: layout.homeRoot,
    TMP_ROOT: layout.tmpRoot,
  };
  const environment = {
    PATH: '/usr/bin:/bin:/usr/sbin:/sbin',
    HOME: layout.homeRoot,
    CFFIXED_USER_HOME: layout.homeRoot,
    TMPDIR: layout.tmpRoot,
    LANG: 'en_US.UTF-8',
    LC_ALL: 'en_US.UTF-8',
    __CF_USER_TEXT_ENCODING: '0x1F5:0:0',
  };
  const rows = [];
  let complete = true;
  for (const profile of profiles) {
    for (const key of keys) {
      const row = runOne(profile, key, layout, environment, definitions);
      rows.push(row);
      if (row.error_code !== null) {
        complete = false;
        break;
      }
    }
    if (!complete) break;
  }
  const receipt = {
    schema: 'c17-root12-getconf-dirhelper-suite-v1',
    scope: 'Trois confstr Darwin via getconf, deux profils QA ne différant que par bsd.dirhelper',
    diagnostic_only: true,
    process_count: rows.length,
    expected_process_count: 6,
    complete,
    outer_sandbox_absence_not_proved: true,
    qa_parameter_paths: definitions,
    cases: rows,
    no_stdout_path_content_in_receipt: true,
    Chrome_launched: false,
    browser_qualification: false,
  };
  const suiteRef = exclusiveJson(path.join(args[2], 'suite-receipt.json'), receipt);
  process.stdout.write(JSON.stringify({ suite_ref: suiteRef, complete, cases: rows.length }) + '\n');
  process.exitCode = complete && rows.length === 6 ? 0 : 1;
}

try {
  main();
} catch (error) {
  process.stderr.write(`Diagnostic non lancé ou interrompu : ${error.message}\n`);
  process.exitCode = 2;
}
