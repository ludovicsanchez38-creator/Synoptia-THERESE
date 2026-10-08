"""Table cinq services et garde pure root avant ACK. Aucune Session importée."""
from pathlib import Path

JOBS = ('rpc-all-runtime_ui-visual_capture-network_capture', 'rpc-screen-negative',
        'rpc-screen-positive-visual', 'rpc-screen-positive-network', 'rpc-screen-restored')
CHROME = '/private/tmp/therese-c17-chrome-qa-copy-RoZmwsja/Google Chrome.app/Contents/MacOS/Google Chrome'
CDP_PORT = 17594  # candidat, ni réservation réelle ni permission admise.


def need(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def plan(root: Path) -> dict:
    need(root.is_absolute() and root.parent == Path('/private/tmp')
         and root.name.startswith('therese-c17-wrapper-canary-'), 'Root auxiliaire hors scope')
    result = {}
    for job in JOBS:
        name = 'aux-chrome-' + job
        options = {'headless': False, 'channel': 'chrome', 'chromiumSandbox': True}
        if job != JOBS[0]:
            options['args'] = ['--disable-background-networking', '--disable-component-update', '--disable-sync']
        result[job] = {'job': job, 'name': name, 'role': 'auxiliary-' + name, 'port': CDP_PORT,
            'executable': CHROME, 'profile': str(root / 'auxiliary' / name / 'profile'),
            'stdout': str(root / 'auxiliary' / name / 'stdout.log'),
            'stderr': str(root / 'auxiliary' / name / 'stderr.log'),
            'start_path': str(root / 'auxiliary' / name / 'start.json'),
            'services_path': str(root / 'auxiliary' / name / 'services.json'),
            'stop_path': str(root / 'auxiliary' / name / 'stop.json'),
            'original_options': options, 'launch_defaults_ref': None,
            'argv': None, 'env': None, 'cwd': None, 'deadline': None}
    return {'schema': 'c17-wrapper-five-chrome-services-definition-v1', 'jobs': result,
            'lifecycle': ['root_start_and_birth_gate', 'root_services_publication', 'job_release',
                          'CDP_owned_listener_check', 'job_exit', 'root_stop_chrome', 'final_RPC_ACK'],
            'command_count_future': 26, 'admission': False, 'OS_qualified': False,
            'shared_port_reuse_requires_previous_stop_and_absence': True}


def require_stop_before_ack(job: str, start: dict, stop: dict, *, job_exit: int) -> dict:
    """Le code métier n'est PAS converti : notamment screen-network non-zéro."""
    need(job in JOBS and type(job_exit) is int, 'Job/code brut auxiliaire invalide')
    name = 'aux-chrome-' + job
    need(start.get('schema') == 'c17-g1-auxiliary-start-v1' and start.get('stage') == job
         and start.get('name') == name and start.get('released') is True
         and isinstance(start.get('root_identity'), dict), 'Start auxiliaire non observé')
    need(stop.get('schema') == 'c17-g1-auxiliary-stop-v1' and stop.get('stage') == job
         and stop.get('name') == name and stop.get('role') == 'auxiliary-' + name
         and stop.get('root_identity') == start['root_identity']
         and all(stop.get(k) == start.get(k) for k in ('actor', 'round_id', 'head', 'binding_sha256')),
         'Stop autre contexte/birth auxiliaire')
    need(stop.get('termination_proved') is True and stop.get('output_archived') is True
         and stop.get('log_stability_proved') is True and stop.get('raw_stable') is True
         and stop.get('clean') is True and stop.get('timed_out') is False and stop.get('taint') is False
         and stop.get('remaining_attributed') == [] and stop.get('ambiguities') == []
         and stop.get('errors') == [] and stop.get('port_absent') == CDP_PORT
         and stop.get('cleanup_deadline_met') is True and type(stop.get('cleanup_elapsed_seconds')) in (int, float)
         and 0 <= stop['cleanup_elapsed_seconds'] <= 8, 'Chrome non fermé/stable avant ACK')
    need(stop.get('controller_signals_attributed') is True and isinstance(stop.get('receipt_refs'), list)
         and len(stop['receipt_refs']) >= 3, 'Bruts/start/cleanup Chrome non référencés')
    return {'job_exit': job_exit, 'chrome_stopped': True,
            'scope': 'pure_join_only_physical_refs_rehash_required_by_root_adapter'}
