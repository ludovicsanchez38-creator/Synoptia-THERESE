// Ports candidats : aucun import child_process, lancement Chrome ou socket.
import {createHash, randomUUID} from 'node:crypto';
import * as fs from 'node:fs';
import {resolve, dirname} from 'node:path';

export const JOBS = Object.freeze([
  'rpc-all-runtime_ui-visual_capture-network_capture', 'rpc-screen-negative',
  'rpc-screen-positive-visual', 'rpc-screen-positive-network', 'rpc-screen-restored',
]);
export const AB_DIRECT_SITES = Object.freeze({
  'recipe-general': 'runtime/recette-c17.mjs',
  'recipe-invoices': 'runtime/recette-facturation-p160-v2.mjs',
  'recipe-crm': 'runtime/recette-crm-focus.mjs',
  B1713: 'complements/instruments/b1713-clavier-v3.mjs',
  'P157-800': 'complements/instruments/p157-pipeline-root-oracle.mjs',
  'P157-1440': 'complements/instruments/p157-pipeline-root-oracle.mjs',
  B1755: 'complements/instruments/b1755-garde-v3.mjs',
  P162: 'complements/instruments/p162-colonnes-v3.mjs',
  coverage: 'runtime/couverture-ecran-c17.mjs',
});
export const AB_DIRECT_JOBS = Object.freeze(Object.keys(AB_DIRECT_SITES));
export const AB_JOBS = Object.freeze([...JOBS, ...AB_DIRECT_JOBS]);
export const PROTOCOL = 'exclusive-pending-fsync-hardlink-v1';
const sha = raw => createHash('sha256').update(raw).digest('hex');
const need = (ok, message) => {if (!ok) throw new Error(message);};
const same = (a, b) => JSON.stringify(canonical(a)) === JSON.stringify(canonical(b));
const canonical = value => Array.isArray(value) ? value.map(canonical) : value && typeof value === 'object'
  ? Object.fromEntries(Object.keys(value).sort().map(key => [key, canonical(value[key])])) : value;
export const monotonic = () => Number(process.hrtime.bigint()) / 1e9;

export function regular(path, root = null) {
  need(path === resolve(path) && fs.realpathSync(path) === path && (!root || path.startsWith(root + '/')), 'Chemin auxiliaire non canonique');
  const fd = fs.openSync(path, fs.constants.O_RDONLY | fs.constants.O_NOFOLLOW);
  try {
    const before = fs.fstatSync(fd), raw = fs.readFileSync(fd), after = fs.fstatSync(fd), named = fs.lstatSync(path);
    need(before.isFile() && before.dev === after.dev && before.ino === after.ino && before.size === after.size
      && before.mtimeMs === after.mtimeMs && named.ino === before.ino && named.dev === before.dev, 'Brut auxiliaire remplacé');
    return raw;
  } finally {fs.closeSync(fd);}
}
export const reference = (path, root = null) => {const raw = regular(path, root); return {path, sha256: sha(raw), bytes: raw.length};};
export function checked(ref, root = null) {
  need(ref && same(Object.keys(ref).sort(), ['bytes', 'path', 'sha256']), 'Référence auxiliaire exacte requise');
  const raw = regular(ref.path, root);
  need(raw.length === ref.bytes && sha(raw) === ref.sha256, 'SHA/bytes auxiliaire divergent');
  return raw;
}
export function published(path, root) {
  const raw = regular(path, root), pending = path + '.pending';
  const staged = regular(pending, root), a = fs.lstatSync(path), b = fs.lstatSync(pending);
  need(a.uid === process.getuid() && a.ino === b.ino && a.dev === b.dev && a.nlink === 2 && b.nlink === 2
    && (a.mode & 0o777) === 0o600 && raw.equals(staged), 'Publication non hardlink fermé exclusif');
  return JSON.parse(raw);
}
export function publish(path, value, root) {
  need(path === resolve(path) && path.startsWith(root + '/') && fs.realpathSync(dirname(path)) === dirname(path), 'Publication extérieure');
  const pending = path + '.pending', fd = fs.openSync(pending, fs.constants.O_CREAT | fs.constants.O_EXCL | fs.constants.O_WRONLY | fs.constants.O_NOFOLLOW, 0o600);
  try {fs.writeFileSync(fd, JSON.stringify(value) + '\n'); fs.fsyncSync(fd);} finally {fs.closeSync(fd);}
  fs.linkSync(pending, path);
  const directory = fs.openSync(dirname(path), fs.constants.O_RDONLY);
  try {fs.fsyncSync(directory);} finally {fs.closeSync(directory);}
  return reference(path, root);
}

export function gitHead(snapshotRef, source) {
  const data = JSON.parse(checked(snapshotRef));
  need(data.schema === 'c17-wrapper-physical-git-snapshot-v1' && data.source_root === source, 'Git autre source/schéma');
  const head = checked(data.head_stdout).toString('ascii').trim(), commit = checked(data.commit_raw);
  checked(data.tree_raw); // Python root lie également la liste récursive au tree du commit.
  const oid = createHash('sha1').update(Buffer.concat([Buffer.from(`commit ${commit.length}\0`), commit])).digest('hex');
  need(/^[0-9a-f]{40}$/.test(head) && head === data.head && oid === head, 'HEAD/commit Git différent');
  need(data.physical_refs.length > 0 && data.physical_refs[0].path === source + '/.git/HEAD', 'HEAD physique absent');
  const values = data.physical_refs.map(ref => checked(ref).toString('ascii').trim());
  for (let i = 0; i < values.length - 1; i += 1) {
    need(/^ref: refs\//.test(values[i]) && !values[i].slice(5).split('/').includes('..')
      && data.physical_refs[i + 1].path === source + '/.git/' + values[i].slice(5), 'Chaîne refs physique différente');
  }
  need(values.at(-1) === head, 'HEAD physique changé');
  return head;
}

export function environmentContext(environment = process.env) {
  const ref = JSON.parse(environment.C17_AUX_CONTEXT_REF), context = JSON.parse(checked(ref));
  const wrapper = context.schema === 'c17-wrapper-auxiliary-context-v1'
    && context.scope === 'WRAPPER_CANARY' && JOBS.includes(context.stage)
    && context.root.startsWith('/private/tmp/therese-c17-wrapper-canary-');
  const match = /^\/private\/tmp\/therese-(c17-direct-round-([ab])-[0-9a-f]{12})$/.exec(context.root);
  const ab = context.schema === 'c17-ab-auxiliary-context-v1'
    && context.scope === 'runtime78_exact_round' && AB_JOBS.includes(context.stage)
    && match && context.round_id === match[1] && context.round_name === match[2].toUpperCase();
  need((wrapper || ab) && context.root === environment.C17_SESSION_ROOT
    && context.stage === environment.C17_SESSION_STAGE && context.actor === environment.C17_SESSION_ACTOR
    && context.round_id === environment.C17_SESSION_ROUND_ID && context.head === environment.C17_SESSION_HEAD
    && fs.realpathSync(context.root) === context.root, 'Contexte auxiliaire non prélié à Session');
  if (ab) {
    need(context.product_source_root === fs.realpathSync(context.product_source_root)
      && context.product_source_root.startsWith('/private/tmp/therese-c17-')
      && context.product_source_root.endsWith('/source')
      && context.source_checkout_ref?.path === `${context.root}/authorization/source-checkout.json`
      && context.git_snapshot_ref?.path === `${context.root}/authorization/git-snapshot.json`,
      'Checkout/snapshot A-B non prélié à une source QA canonique');
    const checkout = JSON.parse(checked(context.source_checkout_ref, context.root));
    need(checkout.schema === 'c17-direct-round-source-checkout-v1'
      && checkout.product_source_root === context.product_source_root
      && checkout.head === context.head && checkout.git_head === context.head
      && gitHead(context.git_snapshot_ref, context.product_source_root) === context.head,
      'Contexte auxiliaire A-B autre checkout Git/HEAD physique');
    if (AB_DIRECT_JOBS.includes(context.stage)) {
      need(context.source_script === AB_DIRECT_SITES[context.stage]
        && process.argv.includes(`${context.root}/${context.source_script}`),
        'Script Node direct A-B autre que le site métier fermé');
    } else {
      need(context.source_script === null, 'Source directe déclarée par enfant RPC');
    }
  }
  // Le contexte préémis ne contient ni SHA du futur binding ni birth Chrome.
  // G1 publie ce registre APRÈS admission Chrome, AVANT release du job Node.
  const name = 'aux-chrome-' + context.stage;
  const registry = published(`${context.root}/auxiliary/${name}/services.json`, context.root);
  need(registry.schema === 'c17-g1-auxiliary-services-v1' && registry.scope === context.scope
    && registry.stage === context.stage
    && registry.actor === context.actor && registry.round_id === context.round_id && registry.head === context.head
    && registry.decision_id === environment.C17_SESSION_DECISION_ID
    && registry.binding_sha256 === environment.C17_SESSION_BINDING_SHA256, 'Registre services root absent/différent');
  return {...context, ...registry};
}

export function createAuxiliary(context, {clock = monotonic, wallClock = () => Date.now() / 1000, pause = ms => new Promise(r => setTimeout(r, ms)),
    readPublished = published, publishNew = publish, referenceOf = reference, checkedRef = checked} = {}) {
  need(context.scope === 'WRAPPER_CANARY' && JOBS.includes(context.stage)
    || context.scope === 'runtime78_exact_round' && AB_JOBS.includes(context.stage),
    'Stage auxiliaire hors cinq WRAPPER/quatorze A-B');
  const root = context.root, scans = new Map();
  async function scan(port) {
    const name = {17593: 'backend', 5173: 'vite', 17594: 'chrome'}[port], service = context.services?.[name];
    need(service && service.port === port && service.birth_identity?.pid > 0, 'Port/service auxiliaire non prélié');
    const journal = root + '/ownership-traces.jsonl', started = clock(), nonce = randomUUID().replaceAll('-', '');
    const path = `${root}/session-events/listener-request-${context.stage}-${nonce}.json`;
    const request = {publication_protocol: PROTOCOL, schema: 'c17-runtime78-owned-listener-node-request-v2',
      actor: context.actor, round_id: context.round_id, head: context.head, qa_root: root, stage: context.stage,
      decision_id: context.decision_id, binding_sha256: context.binding_sha256, port,
      expected_root_identity: service.birth_identity, journal, deadline_seconds: 5,
      request_wall_time_unix: wallClock(), requester_hrtime_seconds: started,
      clock_domain: 'unix-wall-request+requester-local-hrtime-v1'};
    need(Number.isFinite(request.request_wall_time_unix) && request.request_wall_time_unix > 0,
      'Horloge murale Node absente');
    const requestRef = publishNew(path, request, root), responsePath = path + '.response';
    while (clock() < started + 5) {
      let response;
      try {response = readPublished(responsePath, root);} catch (error) {if (error.code !== 'ENOENT') throw error; await pause(10); continue;}
      const observation = JSON.parse(checkedRef(response.observation, root));
      need(clock() < started + 5, 'Observation lue après délai5s');
      need(response.schema === 'c17-runtime78-owned-listener-response-v1' && response.status === 'owned'
        && same(response.request, requestRef), 'Réponse listener étrangère/refusée');
      for (const key of ['actor', 'round_id', 'head', 'qa_root', 'stage', 'port']) {
        need(response[key] === request[key] && observation[key] === request[key], 'Join listener divergent : ' + key);
      }
      need(observation.schema === 'c17-runtime78-owned-listener-observation-v1' && observation.status === 'owned'
        && observation.journal === journal && same(observation.root_identity, service.birth_identity)
        && observation.pid === observation.identity?.pid && observation.scans?.length === 2
        && observation.scans.every(item => same(item.pids, [observation.pid])), 'Listener sans birth/double scan exact');
      return {response: referenceOf(responsePath, root), observation: response.observation, result: observation};
    }
    throw new Error('Parent listener absent au délai5s ; aucun fallback');
  }
  async function listener(port) {
    if (!scans.has(port)) {
      const promise = scan(port);
      scans.set(port, promise);
      try {return await promise;} finally {if (scans.get(port) === promise) scans.delete(port);}
    }
    return scans.get(port);
  }
  async function connect(chromium, options) {
    need(options.headless === false && options.channel === 'chrome' && options.chromiumSandbox === true,
      'Options Chrome originales divergentes');
    const chrome = context.chrome;
    need(chrome?.name === 'aux-chrome-' + context.stage && chrome.port === 17594
      && chrome.profile === `${root}/auxiliary/${chrome.name}/profile`
      && same(chrome.original_options, options), 'Chrome autre ligne root fermée');
    const start = JSON.parse(checkedRef(chrome.start_ref, root));
    need(start.schema === 'c17-g1-auxiliary-start-v1' && start.stage === context.stage && start.name === chrome.name
      && start.role === 'auxiliary-' + chrome.name && start.released === true
      && same(start.root_identity, context.services.chrome.birth_identity)
      && same(start.original_options, options) && start.user_data_dir === chrome.profile
      && start.endpoint === chrome.endpoint && start.actor === context.actor && start.round_id === context.round_id
      && start.head === context.head && start.binding_sha256 === context.binding_sha256, 'Chrome non lancé/libéré par root exact');
    const gate = JSON.parse(checkedRef(start.gate_ref, root)), release = JSON.parse(checkedRef(start.release_ref, root));
    need(gate.pid === start.root_identity.pid && gate.ppid === start.root_identity.ppid
      && gate.uid === start.root_identity.uid && gate.pgid === start.root_identity.pgid
      && same(gate.command, start.gated_command) && same(release.gate, gate)
      && same(release.identity, start.root_identity), 'Joins gate/release/birth Chrome divergents');
    const endpoint = new URL(chrome.endpoint);
    need(endpoint.protocol === 'ws:' && endpoint.hostname === '127.0.0.1' && endpoint.port === '17594'
      && /^\/devtools\/browser\/[a-zA-Z0-9-]+$/.test(endpoint.pathname)
      && !endpoint.username && !endpoint.password && !endpoint.search && !endpoint.hash, 'Endpoint CDP non exact');
    await listener(17594); // Aucun CDP envoyé avant observation root fraîche.
    return chromium.connectOverCDP(chrome.endpoint, {timeout: 5000});
  }
  return {listener, connect}; // browser.close déconnecte ; root doit stop Chrome avant ACK.
}

let auxiliary;
export function getAuxiliary() {
  if (!auxiliary) auxiliary = createAuxiliary(environmentContext());
  return auxiliary;
}
export const requestOwnedListener = port => getAuxiliary().listener(port);
export const connectOwnedChrome = (chromium, options) => getAuxiliary().connect(chromium, options);
