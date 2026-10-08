import {requestOwnedListener} from '../../auxiliary-ports/runtime/aux_node.mjs';

// L'API appelée par contexte-v3 reste identique. Le parent Session vivant
// possède seul lsof et attribue le PID/birth sur deux scans globaux frais.
export async function verifierListenerPossede(port) {
  if (port !== 17593 && port !== 5173) {
    throw new Error('Port ou processus QA non attribué');
  }
  await requestOwnedListener(port);
}
