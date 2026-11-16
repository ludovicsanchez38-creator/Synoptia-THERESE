"""Exécute les relances Rust avec une horloge et un sidecar simulés."""

import subprocess
from pathlib import Path

from tests.test_c20_windows_zombies import _bloc

TAURI_SRC = Path(__file__).resolve().parents[1] / "src/frontend/src-tauri/src"


def test_ancienne_relance_automatique_ne_remplace_pas_la_reprise_manuelle(tmp_path: Path) -> None:
    lib = (TAURI_SRC / "lib.rs").read_text(encoding="utf-8")
    commandes = (TAURI_SRC / "commands.rs").read_text(encoding="utf-8")
    signature = "fn schedule_sidecar_retry(app: &tauri::AppHandle)"
    relance_auto = signature + " " + _bloc(lib, lib.index(signature))
    terminaison = _bloc(lib, lib.index("CommandEvent::Terminated(payload) =>"))
    debut_commande = commandes.index("pub fn restart_backend(")
    release = commandes.index("#[cfg(not(debug_assertions))]", debut_commande)
    relance_manuelle = _bloc(commandes, release)
    harnais = r'''
#![allow(dead_code, unused_imports)]
use ::std::sync::{Arc, Mutex};
use ::std::sync::atomic::{AtomicBool, AtomicU32, AtomicU64, AtomicUsize, Ordering};

struct SidecarState {
    shutting_down: AtomicBool,
    restart_attempts: AtomicU32,
    child: Mutex<Option<Child>>,
    sidecar_termine: AtomicBool,
    generation_relance: AtomicU64,
    verrou_relance: Mutex<()>,
    lancements: AtomicUsize,
    terminaisons: AtomicUsize,
}
struct Child;
impl Child { fn kill(self) -> Result<(), ()> { Ok(()) } }
static BLOCAGE: Mutex<Option<(
    ::std::sync::mpsc::Sender<()>, ::std::sync::mpsc::Receiver<()>
)>> = Mutex::new(None);
mod tauri {
    use super::*;
    pub trait Manager {}
    #[derive(Clone)]
    pub struct AppHandle(pub Arc<SidecarState>);
    impl Manager for AppHandle {}
    impl AppHandle {
        pub fn state<T>(&self) -> &SidecarState { &self.0 }
    }
}
mod std {
    pub mod sync { pub mod atomic { pub use ::std::sync::atomic::*; } }
    pub mod time { pub use ::std::time::Duration; }
    pub mod thread {
        use ::std::sync::Mutex;
        static ATTENTE: Mutex<Vec<Box<dyn FnOnce() + Send>>> = Mutex::new(Vec::new());
        pub fn spawn<F: FnOnce() + Send + 'static>(f: F) { ATTENTE.lock().unwrap().push(Box::new(f)); }
        pub fn sleep(_: ::std::time::Duration) {}
        pub fn expirer() { let f = ATTENTE.lock().unwrap().remove(0); f(); }
    }
}
fn log_sidecar(_: &str) {}
fn emit_sidecar_status(_: &tauri::AppHandle, _: &str, _: u32) {}
fn spawn_backend_sidecar(app: &tauri::AppHandle) {
    let blocage = BLOCAGE.lock().unwrap().take();
    if let Some((signaler, attendre)) = blocage {
        signaler.send(()).unwrap();
        attendre.recv_timeout(::std::time::Duration::from_secs(3)).unwrap();
    }
    app.0.lancements.fetch_add(1, Ordering::SeqCst);
    *app.0.child.lock().unwrap() = Some(Child);
}
struct Payload { code: Option<i32>, signal: Option<i32> }
fn handle_sidecar_termination(app: &tauri::AppHandle, _: ::std::time::Instant, _: Option<i32>) {
    app.0.terminaisons.fetch_add(1, Ordering::SeqCst);
}
fn simuler_terminaison(handle: tauri::AppHandle, generation: u64) {
    let payload = Payload { code: Some(1), signal: None };
    let started_at = ::std::time::Instant::now();
    loop __TERMINAISON__
}
async fn verifier_future_send(handle: tauri::AppHandle, generation: u64) {
    let started_at = ::std::time::Instant::now();
    while let Some(payload) = async { Some(Payload { code: Some(1), signal: None }) }.await
        __TERMINAISON__
}
fn exiger_send<T: Send>(_: T) {}
__RELANCE_AUTO__
fn restart_backend(app: tauri::AppHandle) -> Result<(), String> __RELANCE_MANUELLE__
fn main() {
    let app = tauri::AppHandle(Arc::new(SidecarState {
        shutting_down: AtomicBool::new(false),
        restart_attempts: AtomicU32::new(0),
        child: Mutex::new(None),
        sidecar_termine: AtomicBool::new(false),
        generation_relance: AtomicU64::new(0),
        verrou_relance: Mutex::new(()),
        lancements: AtomicUsize::new(0),
        terminaisons: AtomicUsize::new(0),
    }));
    exiger_send(verifier_future_send(app.clone(), 0));
    let ancienne_generation = app.0.generation_relance.load(Ordering::SeqCst);
    schedule_sidecar_retry(&app);
    restart_backend(app.clone()).unwrap();
    std::thread::expirer();
    println!("{}", app.0.lancements.load(Ordering::SeqCst));
    schedule_sidecar_retry(&app);
    std::thread::expirer();
    println!("{}", app.0.lancements.load(Ordering::SeqCst));
    simuler_terminaison(app.clone(), ancienne_generation);
    println!("{} {}", app.0.sidecar_termine.load(Ordering::SeqCst),
        app.0.terminaisons.load(Ordering::SeqCst));
    let generation_courante = app.0.generation_relance.load(Ordering::SeqCst);
    simuler_terminaison(app.clone(), generation_courante);
    println!("{} {}", app.0.sidecar_termine.load(Ordering::SeqCst),
        app.0.terminaisons.load(Ordering::SeqCst));

    // Un ancien délai est déjà entré dans le lancement quand l'utilisateur
    // demande une relance : celle-ci doit attendre sa fin et passer en dernier.
    let (entre_tx, entre_rx) = ::std::sync::mpsc::channel();
    let (liberer_tx, liberer_rx) = ::std::sync::mpsc::channel();
    *BLOCAGE.lock().unwrap() = Some((entre_tx, liberer_rx));
    schedule_sidecar_retry(&app);
    let automatique = ::std::thread::spawn(|| std::thread::expirer());
    entre_rx.recv_timeout(::std::time::Duration::from_secs(3)).unwrap();
    let (commence_tx, commence_rx) = ::std::sync::mpsc::channel();
    let (fini_tx, fini_rx) = ::std::sync::mpsc::channel();
    let app_manuelle = app.clone();
    let manuelle = ::std::thread::spawn(move || {
        commence_tx.send(()).unwrap();
        restart_backend(app_manuelle).unwrap();
        fini_tx.send(()).unwrap();
    });
    commence_rx.recv_timeout(::std::time::Duration::from_secs(3)).unwrap();
    let terminee_trop_tot = fini_rx.recv_timeout(::std::time::Duration::from_millis(200)).is_ok();
    liberer_tx.send(()).unwrap();
    automatique.join().unwrap();
    manuelle.join().unwrap();
    println!("{}", terminee_trop_tot);
}
'''
    harnais = harnais.replace("__RELANCE_AUTO__", relance_auto)
    harnais = harnais.replace("__RELANCE_MANUELLE__", relance_manuelle)
    harnais = harnais.replace("__TERMINAISON__", terminaison)
    source = tmp_path / "relance.rs"
    binaire = tmp_path / "relance"
    source.write_text(harnais, encoding="utf-8")
    compilation = subprocess.run(
        ["rustc", "--edition=2021", "-o", str(binaire), str(source)],
        capture_output=True, text=True, check=False, timeout=30,
    )
    assert compilation.returncode == 0, compilation.stderr
    execution = subprocess.run([str(binaire)], capture_output=True, text=True, check=False, timeout=30)
    assert execution.returncode == 0, execution.stderr
    lignes = [ligne for ligne in execution.stdout.splitlines() if not ligne.startswith("[THÉRÈSE]")]
    assert lignes[:2] == ["1", "2"]
    assert lignes[2:] == ["false 0", "true 1", "false"]
