//! THÉRÈSE v2 - Tauri Library
//!
//! L'assistante souveraine des entrepreneurs français.
//! Gère le sidecar backend Python en mode release.

use std::sync::Mutex;
use tauri::Emitter;
use tauri::Manager;
use tauri::RunEvent;

/// IPC Commands module
mod commands;

/// Port fixe du backend THÉRÈSE (port obscur, pas de conflit réaliste)
const BACKEND_PORT: u16 = 17293;

/// Écrit dans ~/.therese/logs/sidecar.log
fn log_sidecar(msg: &str) {
    if let Some(home) = dirs::home_dir() {
        let log_dir = home.join(".therese").join("logs");
        let _ = std::fs::create_dir_all(&log_dir);
        let log_file = log_dir.join("sidecar.log");
        if let Ok(mut f) = std::fs::OpenOptions::new()
            .create(true)
            .append(true)
            .open(&log_file)
        {
            use std::io::Write;
            let _ = writeln!(f, "{}", msg);
        }
    }
}

/// Tue les anciens process backend THÉRÈSE zombies restés actifs.
/// Nécessaire lors des mises à jour (ex: v0.1.4 → v0.1.5+).
fn kill_zombie_backends() {
    log_sidecar("Recherche de process backend zombies...");

    #[cfg(unix)]
    {
        let output = std::process::Command::new("pgrep")
            .args(["-f", "backend.*--host.*127\\.0\\.0\\.1"])
            .output();

        if let Ok(output) = output {
            let pids_str = String::from_utf8_lossy(&output.stdout);
            let current_pid = std::process::id();

            let mut found = false;
            for line in pids_str.lines() {
                if let Ok(pid) = line.trim().parse::<u32>() {
                    if pid == current_pid {
                        continue;
                    }
                    found = true;
                    log_sidecar(&format!("Zombie détecté (PID: {}), envoi SIGTERM...", pid));
                    let _ = std::process::Command::new("kill")
                        .args(["-15", &pid.to_string()])
                        .output();
                }
            }

            if found {
                std::thread::sleep(std::time::Duration::from_secs(2));

                // Force kill les survivants
                let output = std::process::Command::new("pgrep")
                    .args(["-f", "backend.*--host.*127\\.0\\.0\\.1"])
                    .output();

                if let Ok(output) = output {
                    let remaining = String::from_utf8_lossy(&output.stdout);
                    let current_pid = std::process::id();
                    for line in remaining.lines() {
                        if let Ok(pid) = line.trim().parse::<u32>() {
                            if pid == current_pid {
                                continue;
                            }
                            log_sidecar(&format!("Zombie résistant (PID: {}), SIGKILL...", pid));
                            let _ = std::process::Command::new("kill")
                                .args(["-9", &pid.to_string()])
                                .output();
                            let _ = std::process::Command::new("pkill")
                                .args(["-9", "-P", &pid.to_string()])
                                .output();
                        }
                    }
                }
            }
        }
    }

    #[cfg(windows)]
    {
        let current_pid = std::process::id();
        let mut found_pids: Vec<u32> = Vec::new();

        // Méthode 1 : wmic (disponible sur Windows 10 et 11 < 25H2)
        // wmic permet un filtre précis par ligne de commande
        let wmic_result = std::process::Command::new("wmic")
            .args([
                "process", "where",
                "name='backend.exe' and commandline like '%--host%127.0.0.1%'",
                "get", "processid", "/format:list",
            ])
            .stdin(std::process::Stdio::null())
            .output();

        if let Ok(output) = &wmic_result {
            if output.status.success() {
                let text = String::from_utf8_lossy(&output.stdout);
                for line in text.lines() {
                    if let Some(pid_str) = line.strip_prefix("ProcessId=") {
                        if let Ok(pid) = pid_str.trim().parse::<u32>() {
                            if pid != current_pid {
                                found_pids.push(pid);
                            }
                        }
                    }
                }
                if !found_pids.is_empty() {
                    log_sidecar(&format!("wmic : {} zombie(s) détecté(s)", found_pids.len()));
                }
            }
        }

        // Méthode 2 : tasklist (fallback Windows 11 25H2+ où wmic est supprimé)
        // tasklist ne filtre que par nom d'image, moins précis mais toujours disponible
        if found_pids.is_empty() {
            log_sidecar("wmic indisponible ou aucun résultat, fallback tasklist...");
            let tasklist_result = std::process::Command::new("tasklist")
                .args(["/FI", "IMAGENAME eq backend.exe", "/FO", "CSV", "/NH"])
                .stdin(std::process::Stdio::null())
                .output();

            if let Ok(output) = tasklist_result {
                let text = String::from_utf8_lossy(&output.stdout);
                for line in text.lines() {
                    // Format CSV : "backend.exe","12345","Console","1","45 000 K"
                    let parts: Vec<&str> = line.split(',').collect();
                    if parts.len() >= 2 {
                        let pid_str = parts[1].trim().trim_matches('"');
                        if let Ok(pid) = pid_str.parse::<u32>() {
                            if pid != current_pid {
                                found_pids.push(pid);
                            }
                        }
                    }
                }
                if !found_pids.is_empty() {
                    log_sidecar(&format!("tasklist : {} zombie(s) détecté(s)", found_pids.len()));
                }
            }
        }

        // Tuer les zombies détectés
        for pid in &found_pids {
            log_sidecar(&format!("Zombie Windows (PID: {}), taskkill /T /F...", pid));
            let _ = std::process::Command::new("taskkill")
                .args(["/T", "/F", "/PID", &pid.to_string()])
                .stdin(std::process::Stdio::null())
                .output();
        }

        // Attendre que Windows libère les handles fichier après taskkill
        if !found_pids.is_empty() {
            log_sidecar("Attente 3s pour libération des handles fichier...");
            std::thread::sleep(std::time::Duration::from_secs(3));
        }
    }

    // Nettoyer le fichier .lock Qdrant
    if let Some(home) = dirs::home_dir() {
        let lock_file = home.join(".therese").join("qdrant").join(".lock");
        if lock_file.exists() {
            log_sidecar("Nettoyage du fichier .lock Qdrant...");
            let _ = std::fs::remove_file(&lock_file);
        }

        // Nettoyer les anciens dossiers _MEI* residuels de PyInstaller
        // Un crash pendant l'extraction laisse un dossier incomplet qui bloque
        // les lancements suivants
        let runtime_dir = home.join(".therese").join("runtime");
        if runtime_dir.exists() {
            if let Ok(entries) = std::fs::read_dir(&runtime_dir) {
                for entry in entries.flatten() {
                    let name = entry.file_name();
                    let name_str = name.to_string_lossy();
                    if name_str.starts_with("_MEI") && entry.path().is_dir() {
                        log_sidecar(&format!("Nettoyage ancien dossier PyInstaller : {}", name_str));
                        let _ = std::fs::remove_dir_all(entry.path());
                    }
                }
            }
        }
    }

    log_sidecar("Nettoyage des zombies terminé");
}

/// Port du backend, accessible depuis le frontend via IPC
pub struct BackendPort(pub Mutex<u16>);

/// État du sidecar backend (release uniquement)
struct SidecarState {
    child: Mutex<Option<tauri_plugin_shell::process::CommandChild>>,
}

/// Initialize Tauri plugins and setup
pub fn run() {
    let app = tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_fs::init())
        .plugin(tauri_plugin_dialog::init())
        .plugin(tauri_plugin_mic_recorder::init())
        .manage(SidecarState {
            child: Mutex::new(None),
        })
        .manage(BackendPort(Mutex::new(BACKEND_PORT)))
        .setup(|app| {
            // Get main window
            if let Some(window) = app.get_webview_window("main") {
                // macOS: Make the title bar transparent
                #[cfg(target_os = "macos")]
                {
                    use tauri::TitleBarStyle;
                    let _ = window.set_title_bar_style(TitleBarStyle::Overlay);
                }

                // Afficher la fenêtre rapidement.
                // F-09 (macOS) : réduit à 100ms (vs 300ms) car index.html contient
                // maintenant un spinner CSS natif qui s'affiche immédiatement,
                // supprimant le besoin d'un délai plus long pour masquer le flash blanc.
                // Sur Windows, le délai est aussi réduit (même bénéfice).
                let w = window.clone();
                std::thread::spawn(move || {
                    std::thread::sleep(std::time::Duration::from_millis(100));
                    let _ = w.show();
                    let _ = w.set_focus();
                });
            }

            // En release uniquement : lancer le sidecar backend
            #[cfg(not(debug_assertions))]
            {
                use tauri_plugin_shell::ShellExt;
                use tauri_plugin_shell::process::CommandEvent;

                // Tuer les anciens process backend zombies AVANT le lancement
                kill_zombie_backends();

                let port = BACKEND_PORT;
                let port_str = port.to_string();

                // Stocker le port pour le frontend
                let backend_port = app.state::<BackendPort>();
                *backend_port.0.lock().unwrap() = port;

                let home_dir = dirs::home_dir().unwrap_or_default();
                let models_path = home_dir
                    .join(".therese/models")
                    .to_string_lossy()
                    .to_string();

                // Rediriger le dossier TEMP du sidecar vers ~/.therese/runtime/
                // Evite le scan antivirus sur %TEMP% qui bloque l'extraction PyInstaller
                let runtime_path = home_dir
                    .join(".therese/runtime")
                    .to_string_lossy()
                    .to_string();
                let _ = std::fs::create_dir_all(&runtime_path);

                log_sidecar(&format!("Démarrage sidecar sur port {}", port));

                // macOS : supprimer la quarantaine préventivement (ciblé, pas tous les xattr)
                #[cfg(target_os = "macos")]
                {
                    if let Ok(exe) = std::env::current_exe() {
                        if let Some(macos_dir) = exe.parent() {
                            log_sidecar(&format!("Suppression quarantaine : {}", macos_dir.display()));
                            let _ = std::process::Command::new("xattr")
                                .args(["-dr", "com.apple.quarantine", &macos_dir.to_string_lossy()])
                                .output();
                        }
                    }
                }

                // Créer la commande sidecar (peut échouer si binaire introuvable)
                match app.shell().sidecar("backend") {
                    Ok(cmd) => {
                        let cmd = cmd
                            .args(["--host", "127.0.0.1", "--port", &port_str])
                            .env("THERESE_PORT", &port_str)
                            .env("THERESE_ENV", "production")
                            .env("SENTENCE_TRANSFORMERS_HOME", &models_path)
                            // Rediriger TEMP/TMP/TMPDIR vers ~/.therese/runtime/
                            // PyInstaller --onefile extrait dans TEMP/_MEIxxxx
                            // %TEMP% est scanne par Windows Defender, causant des crashs silencieux
                            // TMPDIR est prioritaire sur macOS/Linux
                            .env("TMPDIR", &runtime_path)
                            .env("TEMP", &runtime_path)
                            .env("TMP", &runtime_path);

                        match cmd.spawn() {
                            Ok((mut rx, child)) => {
                                let msg = format!("Sidecar démarré (PID: {}, port: {})", child.pid(), port);
                                println!("[THÉRÈSE] {}", msg);
                                log_sidecar(&msg);

                                // Stocker le child pour le kill propre à la fermeture
                                let state = app.state::<SidecarState>();
                                *state.child.lock().unwrap() = Some(child);

                                // Logger stdout/stderr du sidecar dans le fichier de log
                                tauri::async_runtime::spawn(async move {
                                    while let Some(event) = rx.recv().await {
                                        match event {
                                            CommandEvent::Stdout(line) => {
                                                let text = String::from_utf8_lossy(&line);
                                                print!("[backend] {}", text);
                                                log_sidecar(&format!("[stdout] {}", text.trim()));
                                            }
                                            CommandEvent::Stderr(line) => {
                                                let text = String::from_utf8_lossy(&line);
                                                eprint!("[backend] {}", text);
                                                log_sidecar(&format!("[stderr] {}", text.trim()));
                                            }
                                            CommandEvent::Terminated(payload) => {
                                                let msg = format!(
                                                    "Sidecar terminé (code: {:?}, signal: {:?})",
                                                    payload.code, payload.signal
                                                );
                                                println!("[THÉRÈSE] {}", msg);
                                                log_sidecar(&msg);
                                                break;
                                            }
                                            _ => {}
                                        }
                                    }
                                });
                            }
                            Err(e) => {
                                let msg = format!("Erreur lancement sidecar : {}", e);
                                eprintln!("[THÉRÈSE] {}", msg);
                                log_sidecar(&msg);
                                if let Some(window) = app.get_webview_window("main") {
                                    let _ = window.emit("sidecar-error", &msg);
                                }
                            }
                        }
                    }
                    Err(e) => {
                        let msg = format!("Binaire sidecar introuvable : {}", e);
                        eprintln!("[THÉRÈSE] {}", msg);
                        log_sidecar(&msg);
                        if let Some(window) = app.get_webview_window("main") {
                            let _ = window.emit("sidecar-error", &msg);
                        }
                    }
                }
            }

            Ok(())
        })
        .invoke_handler(tauri::generate_handler![
            commands::greet,
            commands::get_system_info,
            commands::get_backend_port,
        ])
        .build(tauri::generate_context!())
        .expect("error while building THÉRÈSE");

    app.run(|app_handle, event| {
        if let RunEvent::Exit = event {
            let state = app_handle.state::<SidecarState>();
            let mut guard = state.child.lock().unwrap();
            if let Some(child) = guard.take() {
                let pid = child.pid();
                let port = *app_handle.state::<BackendPort>().0.lock().unwrap();
                println!("[THÉRÈSE] Arrêt du sidecar backend (PID: {}, port: {})...", pid, port);
                log_sidecar(&format!("Arrêt du sidecar (PID: {}, port: {})", pid, port));

                // Étape 1 : Shutdown graceful via HTTP POST /api/shutdown
                let addr: std::net::SocketAddr = format!("127.0.0.1:{}", port)
                    .parse()
                    .unwrap();
                if let Ok(mut stream) = std::net::TcpStream::connect_timeout(
                    &addr,
                    std::time::Duration::from_secs(2),
                ) {
                    use std::io::Write;
                    let request = format!(
                        "POST /api/shutdown HTTP/1.1\r\nHost: 127.0.0.1:{}\r\nContent-Length: 0\r\nConnection: close\r\n\r\n",
                        port
                    );
                    let _ = stream.write_all(request.as_bytes());
                    let _ = stream.set_read_timeout(
                        Some(std::time::Duration::from_secs(2))
                    );
                    let mut buf = [0u8; 256];
                    let _ = std::io::Read::read(&mut stream, &mut buf);
                    log_sidecar("Shutdown HTTP envoyé, attente du shutdown graceful...");
                } else {
                    log_sidecar("Backend injoignable (timeout 2s), passage au force kill");
                }

                // Étape 2 : Attendre le shutdown graceful (uvicorn + lifespan cleanup)
                std::thread::sleep(std::time::Duration::from_secs(3));

                // Étape 3 : Force kill si toujours vivant
                let _ = child.kill();
                log_sidecar("Force kill envoyé");

                // Étape 4 : Nettoyer les processus enfants orphelins
                // PyInstaller onefile = 2 process (bootloader + Python child)
                // child.kill() ne tue que le process direct, les enfants survivent
                #[cfg(unix)]
                {
                    let _ = std::process::Command::new("pkill")
                        .args(["-9", "-P", &pid.to_string()])
                        .output();
                }
                #[cfg(windows)]
                {
                    let _ = std::process::Command::new("taskkill")
                        .args(["/T", "/F", "/PID", &pid.to_string()])
                        .output();
                }

                log_sidecar("Nettoyage terminé");
            }
        }
    });
}
