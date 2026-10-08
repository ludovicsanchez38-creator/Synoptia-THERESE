import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { fileURLToPath } from 'node:url';

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const base = fs.readFileSync(path.join(root, 'profiles/main12.sb'));
const candidate = fs.readFileSync(path.join(root, 'profiles/dirhelper.sb'));
const runner = fs.readFileSync(path.join(root, 'run_getconf.mjs'), 'utf8');
const hash = (bytes) => crypto.createHash('sha256').update(bytes).digest('hex');

test('MAIN12 exact et candidat à une seule règle Mach littérale', () => {
  assert.equal(hash(base), '980b12368975718d33dba1572ce94da04ca378ca827df1be10a1ed15a7104cdb');
  assert.equal(hash(candidate), '2ecae3a24ec871a44827b3f712ced1ef5e84d8f778906c37b3a5b51bb374dcdf');
  assert.deepEqual(candidate, Buffer.concat([
    base,
    Buffer.from('(allow mach-lookup (global-name "com.apple.bsd.dirhelper"))\n'),
  ]));
});

test('six appels fermés, aucun Chrome, stdout brut non imprimé', () => {
  for (const key of ['DARWIN_USER_DIR', 'DARWIN_USER_CACHE_DIR', 'DARWIN_USER_TEMP_DIR']) {
    assert.ok(runner.includes(`'${key}'`));
  }
  assert.match(runner, /const profiles = Object\.freeze\(\[/);
  assert.match(runner, /spawnSync\('\/usr\/bin\/sandbox-exec'/);
  assert.match(runner, /'\/usr\/bin\/getconf', key/);
  assert.match(runner, /timeoutMs = 10000/);
  assert.match(runner, /maxOutputBytes = 65536/);
  assert.match(runner, /stdout_never_decoded_or_printed: true/);
  assert.doesNotMatch(runner, /stdout\.toString\(/);
  assert.doesNotMatch(runner, /Google Chrome\.app\/Contents\/MacOS\/Google Chrome/);
});

test('deux profils avec les mêmes paramètres QA et la même identité UID', () => {
  assert.match(runner, /process\.getuid\(\) === 501/);
  assert.match(runner, /const definitions = \{/);
  assert.match(runner, /for \(const profile of profiles\)/);
  assert.match(runner, /for \(const key of keys\)/);
  assert.match(runner, /env: environment/);
  assert.match(runner, /qa_parameter_paths: definitions/);
});
