; Hooks NSIS personnalises pour l'installeur Windows de THERESE (Tauri v2).
;
; ENCODAGE : ce fichier DOIT rester en UTF-8 AVEC BOM. La macro POSTINSTALL
; contient des noms de fichiers accentues ("THÉRÈSE.lnk") ; sans BOM,
; makensis interprete le fichier dans la codepage ANSI du systeme et les
; litteraux accentues sont corrompus (le Delete viserait un mauvais nom).
;
; BUG-113 : jusqu'a la v0.1.15, productName valait "THÉRÈSE" (accentue) et
; l'installeur creait un raccourci bureau "THÉRÈSE.lnk". Le renommage en
; "THERESE" (v0.1.16) a laisse cet ancien .lnk orphelin : Windows est
; insensible a la casse mais pas aux accents, donc chaque installation ou
; mise a jour recree "THERESE.lnk" A COTE de l'ancien -> deux icones qui
; pointent sur la meme cible. On purge donc le raccourci legacy (bureau
; utilisateur ET bureau commun, au cas ou une vieille installation machine
; en aurait laisse un). L'installation courante est perUser (installMode
; par defaut de Tauri) : son raccourci frais vit dans le bureau utilisateur
; sous le nom "THERESE.lnk" et n'est pas touche quand la purge commune aboutit.
;
; BUG-180 : un installeur currentUser n'a pas toujours le droit de supprimer
; le raccourci du bureau commun. Delete echoue alors silencieusement et
; l'Explorateur affiche a la fois ce raccourci commun et celui de l'utilisateur.
; Apres la tentative de purge, si le raccourci commun subsiste ET pointe bien
; vers le binaire installe, on conserve celui-ci et supprime son doublon dans
; le bureau utilisateur. Le test de cible evite de sacrifier le raccourci frais
; au profit d'un raccourci commun obsolete ou sans rapport avec cette install.

!macro NSIS_HOOK_POSTINSTALL
  ; Purge des raccourcis bureau legacy en doublon (BUG-113, BUG-180).
  Delete "$DESKTOP\THÉRÈSE.lnk"
  SetShellVarContext all
  Delete "$DESKTOP\THERESE.lnk"
  Delete "$DESKTOP\THÉRÈSE.lnk"

  ; Une suppression dans le bureau commun peut etre refusee sans elevation.
  ; Ne retirer le raccourci utilisateur que si le commun restant vise la meme
  ; installation : il reste ainsi exactement un raccourci fonctionnel.
  !insertmacro IsShortcutTarget "$DESKTOP\THERESE.lnk" "$INSTDIR\${MAINBINARYNAME}.exe"
  Pop $0
  ${If} $0 = 1
    SetShellVarContext current
    Delete "$DESKTOP\THERESE.lnk"
  ${EndIf}
  SetShellVarContext current
!macroend

; BUG-111 : a la desinstallation, quand l'utilisateur coche
; "Supprimer les donnees de l'application", Tauri efface bien les dossiers
; standards de l'app ($APPDATA / $LOCALAPPDATA\fr.synoptia.therese), MAIS pas
; le dossier de donnees backend de THERESE, situe dans le profil utilisateur
; (~/.therese, soit $PROFILE\.therese sous Windows). Resultat : parametrages,
; projets, conversations, comptes etc. survivaient a une desinstall "avec
; suppression des donnees", empechant de repartir d'un profil vierge.
;
; Ce hook s'execute APRES le bloc de suppression standard de Tauri, dans la
; section de desinstallation. La variable $DeleteAppDataCheckboxState vaut 1
; quand la case "supprimer les donnees" a ete cochee : on supprime alors aussi
; le dossier de donnees backend.

!macro NSIS_HOOK_POSTUNINSTALL
  ; Purge aussi le raccourci legacy accentue a la desinstallation (BUG-113).
  Delete "$DESKTOP\THÉRÈSE.lnk"
  ${If} $DeleteAppDataCheckboxState = 1
    ; Dossier de donnees backend THERESE (db, parametrages, projets, images,
    ; conversations, comptes, cle de chiffrement...).
    RMDir /r "$PROFILE\.therese"
  ${EndIf}
!macroend
