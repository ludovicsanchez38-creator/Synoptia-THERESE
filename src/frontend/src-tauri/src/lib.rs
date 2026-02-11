//! THÉRÈSE v2 - Tauri Library
//!
//! L'assistante souveraine des entrepreneurs français.
//! Gère le sidecar backend Python en mode release.

use std::net::TcpListener;
use std::sync::Mutex;
use tauri::Emitter;
use tauri::Manager;
use tauri::RunEvent;

/// IPC Commands module
mod commands;

/// Trouve un port TCP libre en laissant l'OS en assigner un.
fn find_free_port() -> u16 {
    let listener = TcpListener::bind("127.0.0.1:0")
        .expect("Impossible de trouver un port libre");
    let port = listener.local_addr().unwrap().port();
    drop(listener);
    port
}

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
        let output = std::process::Command::new("wmic")
            .args([
                "process", "where",
                "name='backend.exe' and commandline like '%--host%127.0.0.1%'",
                "get", "processid", "/format:list",
            ])
            .output();

        if let Ok(output) = output {
            let text = String::from_utf8_lossy(&output.stdout);
            let current_pid = std::process::id();

            for line in text.lines() {
                if let Some(pid_str) = line.strip_prefix("ProcessId=") {
                    if let Ok(pid) = pid_str.trim().parse::<u32>() {
                        if pid == current_pid {
                            continue;
                        }
                        log_sidecar(&format!("Zombie Windows (PID: {}), taskkill...", pid));
                        let _ = std::process::Command::new("taskkill")
                            .args(["/T", "/F", "/PID", &pid.to_string()])
                            .output();
                    }
                }
            }
        }
    }

    // Nettoyer le fichier .lock Qdrant
    if let Some(home) = dirs::home_dir() {
        let lock_file = home.join(".therese").join("qdrant").join(".lock");
        if lock_file.exists() {
            log_sidecar("Nettoyage du fichier .lock Qdrant...");
            let _ = std::fs::remove_file(&lock_file);
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
        .manage(BackendPort(Mutex::new(8000)))
        .setup(|app| {
            // Get main window
            if let Some(window) = app.get_webview_window("main") {
                // macOS: Make the title bar transparent
                #[cfg(target_os = "macos")]
                {
                    use tauri::TitleBarStyle;
                    let _ = window.set_title_bar_style(TitleBarStyle::Overlay);
                }

                // Focus window
                let _ = window.set_focus();
            }

            // En release uniquement : lancer le sidecar backend
            #[cfg(not(debug_assertions))]
            {
                use tauri_plugin_shell::ShellExt;
                use tauri_plugin_shell::process::CommandEvent;

                // Tuer les anciens process backend zombies AVANT le lancement
                kill_zombie_backends();

                let port = find_free_port();
                let port_str = port.to_string();

                // Stocker le port pour le frontend
                let backend_port = app.state::<BackendPort>();
                *backend_port.0.lock().unwrap() = port;

                let models_path = dirs::home_dir()
                    .unwrap_or_default()
                    .join(".therese/models")
                    .to_string_lossy()
                    .to_string();

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
                            .env("SENTENCE_TRANSFORMERS_HOME", &models_path);

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
