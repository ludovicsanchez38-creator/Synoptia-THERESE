"""Exécute le bloc Windows de production avec des commandes simulées.

Aucun processus réel n'est interrogé ou arrêté : seul le bloc Rust est compilé
avec un remplacement local de std::process.
"""

import os
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

RUST_LIB = Path(__file__).resolve().parents[1] / "src/frontend/src-tauri/src/lib.rs"


def _bloc(source: str, debut: int) -> str:
    """Extrait un bloc Rust équilibré pour le compiler dans le harnais."""
    ouverture = source.index("{", debut)
    niveau = 0
    for position in range(ouverture, len(source)):
        if source[position] == "{":
            niveau += 1
        elif source[position] == "}":
            niveau -= 1
            if niveau == 0:
                return source[ouverture : position + 1]
    raise AssertionError("Bloc Rust non terminé")


def _simuler_windows(tmp_path: Path, scenario: str) -> list[str]:
    source = RUST_LIB.read_text(encoding="utf-8")
    fonction = source.index("fn kill_zombie_backends()")
    windows = source.index("#[cfg(windows)]", fonction)
    bloc_windows = _bloc(source, windows)
    signature = "fn est_moteur_therese(args: &str) -> bool"
    predicat = signature + " " + _bloc(source, source.index(signature))
    harnais = r'''
mod simulation {
    const BACKEND_PORT: u16 = 17293;
    fn log_sidecar(_: &str) {}
    mod std {
        pub mod time { pub use ::std::time::Duration; }
        pub mod thread { pub fn sleep(_: ::std::time::Duration) {} }
        pub mod process {
            pub use ::std::process::Stdio;
            use ::std::sync::Mutex;
            static ARRETS: Mutex<Vec<String>> = Mutex::new(Vec::new());
            pub fn id() -> u32 { 999 }
            pub struct Status;
            impl Status { pub fn success(&self) -> bool { true } }
            pub struct Output { pub status: Status, pub stdout: Vec<u8> }
            pub struct Command { name: String, args: Vec<String> }
            impl Command {
                pub fn new(name: &str) -> Self {
                    Self { name: name.to_string(), args: Vec::new() }
                }
                pub fn args<I, S>(mut self, args: I) -> Self
                where I: IntoIterator<Item = S>, S: AsRef<str> {
                    self.args.extend(args.into_iter().map(|v| v.as_ref().to_string()));
                    self
                }
                pub fn stdin(self, _: Stdio) -> Self { self }
                pub fn output(self) -> ::std::io::Result<Output> {
                    let scenario = ::std::env::args().nth(1).unwrap();
                    if self.name == "wmic" && scenario == "wmic_absent" {
                        return Err(::std::io::Error::new(::std::io::ErrorKind::NotFound, "WMIC absent"));
                    }
                    let texte = match self.name.as_str() {
                        "wmic" if scenario == "wmic_vide" || scenario == "wmic_indisponible_moteur" => String::new(),
                        "wmic" => {
                            let port = if scenario == "port_inexact" { "172930" } else { "17293" };
                            if self.args.iter().any(|arg| arg.split(',').any(|champ| champ.eq_ignore_ascii_case("commandline"))) {
                                format!("CommandLine=\"C:\\Program Files\\THERESE\\backend.exe\" --host 127.0.0.1 --port {}\r\nProcessId=4242\r\n\r\n", port)
                            } else {
                                "ProcessId=4242\r\n".to_string()
                            }
                        }
                        "tasklist" => {
                            let pid = if scenario == "wmic_indisponible_moteur" { 4242 } else { 414 };
                            format!("\"backend.exe\",\"{}\",\"Console\",\"1\",\"42 K\"\r\n", pid)
                        }
                        "powershell" => {
                            let port = if scenario == "wmic_indisponible_moteur" { "17293" } else { "8000" };
                            format!("\"C:\\Program Files\\THERESE\\backend.exe\" --host 127.0.0.1 --port {}\r\n", port)
                        }
                        "taskkill" => {
                            ARRETS.lock().unwrap().push(self.args.last().unwrap().clone());
                            String::new()
                        }
                        autre => panic!("Commande inattendue : {}", autre),
                    };
                    let stdout = if scenario == "port_exact_utf16" {
                        let mut octets = vec![0xff, 0xfe];
                        octets.extend(texte.encode_utf16().flat_map(u16::to_le_bytes));
                        octets
                    } else { texte.into_bytes() };
                    Ok(Output { status: Status, stdout })
                }
            }
            pub fn arrets() -> Vec<String> { ARRETS.lock().unwrap().clone() }
        }
    }
    __PREDICAT__
    pub fn run() -> Vec<String> {
        __BLOC_WINDOWS__
        std::process::arrets()
    }
}
fn main() {
    for pid in simulation::run() { println!("{}", pid); }
}
'''
    harnais = harnais.replace("__PREDICAT__", predicat).replace("__BLOC_WINDOWS__", bloc_windows)
    chemin = tmp_path / "simulation.rs"
    binaire = tmp_path / "simulation"
    chemin.write_text(harnais, encoding="utf-8")
    compilation = subprocess.run(
        ["rustc", "--edition=2021", "-o", str(binaire), str(chemin)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert compilation.returncode == 0, compilation.stderr
    execution = subprocess.run([str(binaire), scenario], capture_output=True, text=True, check=False)
    assert execution.returncode == 0, execution.stderr
    return execution.stdout.splitlines()


def test_b1835_wmic_vide_ne_tue_pas_un_backend_non_identifie(tmp_path: Path) -> None:
    assert _simuler_windows(tmp_path, "wmic_vide") == []
    assert _simuler_windows(tmp_path, "wmic_indisponible_moteur") == ["4242"]


def test_b1836_seul_le_port_exact_designe_un_moteur(tmp_path: Path) -> None:
    assert _simuler_windows(tmp_path, "port_inexact") == []
    assert _simuler_windows(tmp_path, "port_exact") == ["4242"]
    assert _simuler_windows(tmp_path, "port_exact_utf16") == ["4242"]


def _nettoyage_python_simule(monkeypatch, tmp_path: Path, scenario: str) -> list[str]:
    """Lance la seconde étape sans interroger ni arrêter de vrai processus."""
    import main as point_d_entree

    arrets: list[str] = []

    def faux_run(commande, **_kwargs):
        if commande[0] == "wmic":
            if scenario == "wmic_absent":
                raise FileNotFoundError("WMIC simulé absent")
            return SimpleNamespace(stdout="ProcessId=414\r\n", returncode=0)
        if commande[0] == "tasklist":
            pid = {
                "moteur": "4242",
                "pid_courant": str(os.getpid()),
                "pid_parent": str(os.getppid()),
            }.get(scenario, "414")
            lignes = f'"backend.exe","{pid}","Console","1","42 K"\r\n'
            if scenario == "cim_un_echoue":
                lignes += '"backend.exe","4242","Console","1","42 K"\r\n'
            return SimpleNamespace(
                stdout=lignes, returncode=0
            )
        if commande[0] == "powershell":
            if scenario == "cim_indisponible":
                raise FileNotFoundError("CIM simulé indisponible")
            if scenario == "cim_un_echoue" and "ProcessId = 414" in commande[-1]:
                raise subprocess.TimeoutExpired(commande, 5)
            port = {
                "autre_port": "8000",
                "port_prefixe": "172930",
                "wmic_absent": "8000",
            }.get(scenario, "17293")
            return SimpleNamespace(
                stdout=f'"C:\\Program Files\\THERESE\\backend.exe" --host 127.0.0.1 --port {port}',
                returncode=1 if scenario == "cim_echec" else 0,
            )
        if commande[0] == "taskkill":
            arrets.append(commande[-1])
            return SimpleNamespace(stdout="", returncode=0)
        raise AssertionError(f"Commande non simulée : {commande[0]}")

    with monkeypatch.context() as contexte:
        contexte.setenv("THERESE_DATA_DIR", str(tmp_path / "profil-jetable"))
        contexte.setattr(sys, "platform", "win32")
        contexte.setattr(subprocess, "run", faux_run)
        contexte.setattr(time, "sleep", lambda _delai: None)
        point_d_entree._kill_zombie_backends()
    return arrets


@pytest.mark.parametrize(
    ("scenario_rust", "scenario_python"),
    [("wmic_absent", "wmic_absent"), ("port_inexact", "autre_port")],
)
def test_les_deux_nettoyages_epargnent_un_backend_tiers(
    tmp_path: Path, monkeypatch, scenario_rust: str, scenario_python: str
) -> None:
    assert _simuler_windows(tmp_path, scenario_rust) == []
    assert _nettoyage_python_simule(monkeypatch, tmp_path, scenario_python) == []


def test_le_nettoyage_python_identifie_un_moteur_restant(tmp_path: Path, monkeypatch) -> None:
    assert _nettoyage_python_simule(monkeypatch, tmp_path, "moteur") == ["4242"]


@pytest.mark.parametrize(
    "scenario", ["pid_courant", "pid_parent", "port_prefixe", "cim_indisponible", "cim_echec"]
)
def test_le_nettoyage_python_epargne_les_pid_non_identifies(
    tmp_path: Path, monkeypatch, scenario: str
) -> None:
    assert _nettoyage_python_simule(monkeypatch, tmp_path, scenario) == []


def test_un_echec_cim_ne_masque_pas_le_candidat_suivant(tmp_path: Path, monkeypatch) -> None:
    assert _nettoyage_python_simule(monkeypatch, tmp_path, "cim_un_echoue") == ["4242"]
