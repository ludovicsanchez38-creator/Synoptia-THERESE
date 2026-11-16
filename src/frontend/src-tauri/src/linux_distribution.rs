//! B-1801 : seule une distribution Debian ou déclarée dérivée accepte le .deb.

pub fn est_debian() -> bool {
    std::fs::read_to_string("/etc/os-release")
        .or_else(|_| std::fs::read_to_string("/usr/lib/os-release"))
        .map(|contenu| est_debian_dans(&contenu))
        .unwrap_or(false)
}

fn est_debian_dans(contenu: &str) -> bool {
    contenu.lines().any(|ligne| {
        let Some((cle, valeur)) = ligne.trim().split_once('=') else {
            return false;
        };
        matches!(cle, "ID" | "ID_LIKE")
            && valeur
                .trim_matches(['"', '\''])
                .split_ascii_whitespace()
                .any(|identifiant| identifiant == "debian")
    })
}

#[cfg(test)]
mod tests {
    use super::est_debian_dans;

    #[test]
    fn debian() {
        assert!(est_debian_dans("ID=debian\n"));
    }
    #[test]
    fn ubuntu() {
        assert!(est_debian_dans("ID=ubuntu\nID_LIKE=debian\n"));
    }
    #[test]
    fn mint() {
        assert!(est_debian_dans("ID=linuxmint\nID_LIKE=\"ubuntu debian\"\n"));
    }
    #[test]
    fn manjaro() {
        assert!(!est_debian_dans("ID=manjaro\nID_LIKE=arch\n"));
    }
    #[test]
    fn fedora() {
        assert!(!est_debian_dans("ID=fedora\nID_LIKE=\"rhel fedora\"\n"));
    }
    #[test]
    fn inconnu() {
        assert!(!est_debian_dans(""));
    }
    #[test]
    fn pas_de_detection_par_sous_chaine() {
        assert!(!est_debian_dans("ID=nondebian\nNAME=debian\n"));
    }
    #[test]
    fn commentaires_et_apostrophes() {
        assert!(!est_debian_dans("# ID=debian\nID=arch\n"));
        assert!(est_debian_dans("ID_LIKE='debian'\n"));
    }
}
