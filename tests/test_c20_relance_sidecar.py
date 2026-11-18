"""Exécute les relances Rust avec une horloge et un sidecar simulés."""

import subprocess
from pathlib import Path

import pytest

from tests.test_c20_windows_zombies import _bloc

TAURI_SRC = Path(__file__).resolve().parents[1] / "src/frontend/src-tauri/src"


def _lire_etats(sortie: bytes) -> list[str]:
    # Protocole ASCII distinct des journaux Rust, quel que soit leur encodage.
    return [ligne.removeprefix(b"ETAT ").decode("ascii")
            for ligne in sortie.splitlines() if ligne.startswith(b"ETAT ")]


@pytest.mark.parametrize("journal", [
    "[THÉRÈSE] Sidecar terminé".encode("utf-8"),
    "[THÉRÈSE] Sidecar terminé".encode("cp1252"),
    b"journal non decodable: \xff\x81",
], ids=["utf8", "cp1252", "octets-inconnus"])
def test_lecture_des_etats_independante_des_journaux(journal: bytes) -> None:
    sortie = b"ETAT 1\r\nETAT 2\r\nETAT false 0\r\n" + journal + b"\r\nETAT true 1\r\nETAT false\r\n"
    assert _lire_etats(sortie) == ["1", "2", "false 0", "true 1", "false"]


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
fn emit_sidecar_status(_: &tauri::AppHandle, _: &str, _: u32, _: u64) {}
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
fn restart_backend(app: tauri::AppHandle) -> Result<u64, String> __RELANCE_MANUELLE__
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
    assert_eq!(restart_backend(app.clone()).unwrap(), 1);
    std::thread::expirer();
    println!("ETAT {}", app.0.lancements.load(Ordering::SeqCst));
    schedule_sidecar_retry(&app);
    std::thread::expirer();
    println!("ETAT {}", app.0.lancements.load(Ordering::SeqCst));
    simuler_terminaison(app.clone(), ancienne_generation);
    println!("ETAT {} {}", app.0.sidecar_termine.load(Ordering::SeqCst),
        app.0.terminaisons.load(Ordering::SeqCst));
    let generation_courante = app.0.generation_relance.load(Ordering::SeqCst);
    simuler_terminaison(app.clone(), generation_courante);
    println!("ETAT {} {}", app.0.sidecar_termine.load(Ordering::SeqCst),
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
    println!("ETAT {}", terminee_trop_tot);
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
        capture_output=True, encoding="utf-8", check=False, timeout=30,
    )
    assert compilation.returncode == 0, compilation.stderr
    execution = subprocess.run([str(binaire)], capture_output=True, check=False, timeout=30)
    assert execution.returncode == 0, execution.stderr
    assert _lire_etats(execution.stdout) == ["1", "2", "false 0", "true 1", "false"]


@pytest.mark.parametrize("plateforme", ["linux", "macos", "windows"])
def test_generations_des_evenements_et_de_la_commande(tmp_path: Path, plateforme: str) -> None:
    """Exécute les émetteurs Rust réels avec un sidecar et une fenêtre simulés."""
    lib = (TAURI_SRC / "lib.rs").read_text(encoding="utf-8")
    commandes = (TAURI_SRC / "commands.rs").read_text(encoding="utf-8")

    def fonction(source: str, signature: str) -> str:
        return signature + " " + _bloc(source, source.index(signature))

    spawn = fonction(lib, "pub(crate) fn spawn_backend_sidecar(app: &tauri::AppHandle)")
    # Sélectionner les branches de l'extrait indépendamment du système du banc.
    for cible in ("linux", "macos", "windows"):
        spawn = spawn.replace(
            f'#[cfg(target_os = "{cible}")]', f'#[cfg(feature = "simulation_{cible}")]'
        )
    relance = fonction(lib, "fn schedule_sidecar_retry(app: &tauri::AppHandle)")
    statut = fonction(
        lib, "fn emit_sidecar_status(app: &tauri::AppHandle, status: &str, attempt: u32, generation: u64)"
    )
    debut = commandes.index("pub fn restart_backend(")
    manuel = _bloc(commandes, commandes.index("#[cfg(not(debug_assertions))]", debut))
    harnais = r'''
#![allow(dead_code, unused_imports)]
use ::std::sync::{Arc, Mutex};
use ::std::sync::atomic::{AtomicBool, AtomicU32, AtomicU64, Ordering};

#[derive(Debug, PartialEq)]
enum Evenement { Erreur(String, u64), Statut(String, u32, u64) }
#[macro_export]
macro_rules! json {
    ({ "message": $m:expr, "generation": $g:expr }) => { Evenement::Erreur($m.to_string(), $g) };
    ({ "state": $s:expr, "attempt": $a:expr, "generation": $g:expr }) => { Evenement::Statut($s.to_string(), $a, $g) };
}
mod serde_json { pub use crate::json; }
mod std {
    pub mod sync { pub mod atomic { pub use ::std::sync::atomic::*; } }
    pub mod time { pub use ::std::time::{Duration, Instant}; }
    pub mod thread {
        pub fn sleep(_: ::std::time::Duration) {}
        pub fn spawn<F: FnOnce() + Send + 'static>(_: F) {}
    }
    pub mod fs { pub fn create_dir_all(_: &str) -> Result<(), ()> { Ok(()) } }
    pub mod env {
        pub fn current_exe() -> ::std::io::Result<::std::path::PathBuf> {
            Err(::std::io::Error::new(::std::io::ErrorKind::NotFound, "simulé"))
        }
    }
    pub mod process {
        pub struct Command;
        impl Command {
            pub fn new(_: &str) -> Self { Self }
            pub fn args<I, S>(&mut self, _: I) -> &mut Self
            where I: IntoIterator<Item = S>, S: AsRef<str> { self }
            pub fn output(&mut self) -> Result<(), ()> { Ok(()) }
        }
    }
}
mod dirs { pub fn home_dir() -> Option<::std::path::PathBuf> { None } }
struct Child;
impl Child {
    fn pid(&self) -> u32 { 42 }
    fn kill(self) -> Result<(), ()> { Ok(()) }
}
struct SidecarState {
    child: Mutex<Option<Child>>,
    shutting_down: AtomicBool,
    sidecar_termine: AtomicBool,
    restart_attempts: AtomicU32,
    generation_relance: AtomicU64,
    verrou_relance: Mutex<()>,
}
struct BackendPort(Mutex<u16>);
struct Application { state: SidecarState, port: BackendPort, mode: AtomicU32, events: Mutex<Vec<Evenement>> }
mod tauri {
    use super::*;
    pub trait Manager {}
    #[derive(Clone)]
    pub struct AppHandle(pub Arc<Application>);
    impl Manager for AppHandle {}
    pub trait Etat { fn get(app: &Application) -> &Self; }
    impl Etat for SidecarState { fn get(app: &Application) -> &Self { &app.state } }
    impl Etat for BackendPort { fn get(app: &Application) -> &Self { &app.port } }
    impl AppHandle {
        pub fn state<T: Etat>(&self) -> &T { T::get(&self.0) }
        pub fn get_webview_window(&self, _: &str) -> Option<Window> { Some(Window(self.clone())) }
        pub fn path(&self) -> PathResolver { PathResolver }
    }
    pub struct PathResolver;
    impl PathResolver {
        pub fn resource_dir(&self) -> ::std::io::Result<::std::path::PathBuf> {
            Ok(::std::path::PathBuf::from("ressources-simulees"))
        }
    }
    pub struct Window(AppHandle);
    impl Window {
        pub fn emit(&self, nom: &str, evenement: Evenement) -> Result<(), ()> {
            match &evenement {
                Evenement::Erreur(_, _) => assert_eq!(nom, "sidecar-error"),
                Evenement::Statut(_, _, _) => assert_eq!(nom, "sidecar-status"),
            }
            self.0.0.events.lock().unwrap().push(evenement);
            Ok(())
        }
    }
    pub mod async_runtime {
        pub fn spawn<F: ::std::future::Future<Output = ()> + Send + 'static>(_: F) {}
    }
}
mod tauri_plugin_shell {
    use super::*;
    pub mod process {
        pub struct Payload { pub code: Option<i32>, pub signal: Option<i32> }
        pub enum CommandEvent { Stdout(Vec<u8>), Stderr(Vec<u8>), Terminated(Payload), Autre }
        pub struct Receiver;
        impl Receiver { pub async fn recv(&mut self) -> Option<CommandEvent> { None } }
    }
    pub trait ShellExt { fn shell(&self) -> Shell; }
    impl ShellExt for tauri::AppHandle { fn shell(&self) -> Shell { Shell(self.clone()) } }
    pub struct Shell(tauri::AppHandle);
    impl Shell {
        pub fn sidecar(&self, _: &str) -> Result<Command, &'static str> {
            if self.0.0.mode.load(Ordering::SeqCst) == 1 { Err("introuvable") }
            else { Ok(Command(self.0.clone())) }
        }
    }
    pub struct Command(tauri::AppHandle);
    impl Command {
        pub fn args<I, S>(self, _: I) -> Self where I: IntoIterator<Item = S>, S: AsRef<str> { self }
        pub fn env<S: AsRef<str>>(self, _: &str, _: S) -> Self { self }
        pub fn spawn(self) -> Result<(process::Receiver, Child), &'static str> {
            if self.0.0.mode.load(Ordering::SeqCst) == 2 { Err("spawn simulé") }
            else { Ok((process::Receiver, Child)) }
        }
    }
}
const BACKEND_PORT: u16 = 17293;
fn kill_zombie_backends() {}
fn log_sidecar(_: &str) {}
fn handle_sidecar_termination(_: &tauri::AppHandle, _: ::std::time::Instant, _: Option<i32>) {}
__SPAWN__
__RELANCE__
__STATUT__
fn restart_backend(app: tauri::AppHandle) -> Result<u64, String> __MANUEL__
fn main() {
    let app = tauri::AppHandle(Arc::new(Application {
        state: SidecarState {
            child: Mutex::new(None), shutting_down: AtomicBool::new(false),
            sidecar_termine: AtomicBool::new(false), restart_attempts: AtomicU32::new(0),
            generation_relance: AtomicU64::new(4), verrou_relance: Mutex::new(()),
        },
        port: BackendPort(Mutex::new(0)), mode: AtomicU32::new(1), events: Mutex::new(Vec::new()),
    }));
    spawn_backend_sidecar(&app);
    app.0.mode.store(2, Ordering::SeqCst);
    spawn_backend_sidecar(&app);
    app.0.mode.store(3, Ordering::SeqCst);
    assert_eq!(restart_backend(app.clone()).unwrap(), 5);
    app.0.mode.store(2, Ordering::SeqCst);
    assert_eq!(restart_backend(app.clone()).unwrap(), 6);
    app.0.state.restart_attempts.store(3, Ordering::SeqCst);
    schedule_sidecar_retry(&app);
    assert_eq!(*app.0.events.lock().unwrap(), vec![
        Evenement::Erreur("Binaire sidecar introuvable : introuvable".into(), 4),
        Evenement::Statut("restarting".into(), 1, 4),
        Evenement::Erreur("Erreur lancement sidecar : spawn simulé".into(), 4),
        Evenement::Statut("restarting".into(), 2, 4),
        Evenement::Statut("running".into(), 0, 5),
        Evenement::Erreur("Erreur lancement sidecar : spawn simulé".into(), 6),
        Evenement::Statut("restarting".into(), 1, 6),
        Evenement::Statut("failed".into(), 3, 6),
    ]);
}
'''
    for marqueur, code in {
        "__SPAWN__": spawn, "__RELANCE__": relance, "__STATUT__": statut, "__MANUEL__": manuel,
    }.items():
        harnais = harnais.replace(marqueur, code)
    source = tmp_path / "evenements.rs"
    binaire = tmp_path / "evenements"
    source.write_text(harnais, encoding="utf-8")
    compilation = subprocess.run(
        ["rustc", "--edition=2021", "--cfg", f'feature="simulation_{plateforme}"', "-o", str(binaire), str(source)],
        capture_output=True, text=True, check=False, timeout=30,
    )
    assert compilation.returncode == 0, compilation.stderr
    execution = subprocess.run([str(binaire)], capture_output=True, text=True, check=False, timeout=30)
    assert execution.returncode == 0, execution.stderr
