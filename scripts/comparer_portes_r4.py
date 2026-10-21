"""Comparer les portes R4 par nom de test et par diagnostic, sans réseau."""
import collections
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

LOGS = Path(__file__).resolve().parents[1] / '.recette-r4/logs'


def junit(phase, suite):
    tests = {}
    for t in ET.parse(LOGS / f'{phase}-{suite}.xml').iter('testcase'):
        nom = t.get('classname', '') + '::' + t.get('name', '')
        statut = 'passed'
        for s in ('skipped', 'failure', 'error'):
            if t.find(s) is not None:
                statut = 'xfail' if t.find(s).get('type') == 'pytest.xfail' else s
        if nom in tests:
            raise ValueError(f'JUnit {phase} : nom dupliqué {nom}')
        tests[nom] = statut
    return tests


def vitest(phase):
    tests = {}
    donnees = json.loads((LOGS / f'{phase}-vitest.json').read_text())
    for fichier in donnees['testResults']:
        nom_fichier = fichier['name'].split('/src/frontend/')[-1]
        for t in fichier['assertionResults']:
            nom = nom_fichier + '::' + t['fullName']
            if nom in tests:
                raise ValueError(f'Vitest {phase} : nom dupliqué {nom}')
            tests[nom] = t['status']
    if len(tests) != donnees['numTotalTests']:
        raise ValueError(f"Vitest {phase} : suite incomplète, {len(tests)} noms pour {donnees['numTotalTests']} tests déclarés")
    if any(f['status'] == 'failed' and not any(t['status'] == 'failed' for t in f['assertionResults'])
           for f in donnees['testResults']):
        raise ValueError(f'Vitest {phase} : échec de fichier sans résultat de test')
    return tests


def diagnostics(phase):
    motifs = collections.Counter()
    for ligne in (LOGS / f'{phase}-mypy.log').read_text().splitlines():
        m = re.match(r'(.+?):\d+(?::\d+)?: (error|warning): (.+)', ligne)
        if m:
            fichier = m[1].split('src/backend/')[-1]
            motifs[(fichier, m[2] + ': ' + m[3])] += 1
    sortie = (LOGS / f'{phase}-mypy.log').read_text()
    total = re.search(r'Found (\d+) errors?', sortie)
    compte = sum(v for (_, message), v in motifs.items() if message.startswith('error:'))
    if total is None and 'Success: no issues found' not in sortie:
        raise ValueError(f'mypy {phase} : résultat incomplet ou erreur sans localisation')
    if total and int(total[1]) != compte:
        raise ValueError(f'mypy {phase} : des diagnostics ne sont pas comptés')
    return motifs


def main():
    bilan = {}
    regres = False
    for suite, lecteur in [('pytest', lambda p: junit(p, 'pytest')),
                            ('autonome', lambda p: junit(p, 'autonome')), ('vitest', vitest)]:
        avant, apres = lecteur('avant'), lecteur('apres')
        retires = sorted(avant.keys() - apres.keys())
        ajoutes = sorted(apres.keys() - avant.keys())
        changements = {n: [avant[n], apres[n]] for n in avant.keys() & apres.keys() if avant[n] != apres[n]}
        mauvais = {n: v for n, v in changements.items() if v[1] != 'passed'}
        mauvais.update({n: [None, apres[n]] for n in ajoutes if apres[n] != 'passed'})
        bilan[suite] = {'avant': dict(collections.Counter(avant.values())),
            'apres': dict(collections.Counter(apres.values())), 'retires': retires,
            'ajoutes': ajoutes, 'changements': changements, 'regressions': mauvais}
        (LOGS / f'{suite}-resultats-par-nom.json').write_text(json.dumps(
            {'avant': avant, 'apres': apres}, ensure_ascii=False, indent=2, sort_keys=True))
        regres |= bool(retires or mauvais)
    avant, apres = diagnostics('avant'), diagnostics('apres')
    nouveaux, resolus = apres - avant, avant - apres
    bilan['mypy'] = {'avant': sum(avant.values()), 'apres': sum(apres.values()),
        'nouveaux': [[*k, v] for k, v in nouveaux.items()], 'retires': [[*k, v] for k, v in resolus.items()]}
    regres |= bool(nouveaux)
    (LOGS / 'comparaison.json').write_text(json.dumps(bilan, ensure_ascii=False, indent=2))
    print(json.dumps(bilan, ensure_ascii=False, indent=2))
    raise SystemExit(int(regres))


if __name__ == '__main__':
    main()
