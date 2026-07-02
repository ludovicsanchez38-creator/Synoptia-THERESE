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
; sous le nom "THERESE.lnk" et n'est pas touche par ces suppressions.

!macro NSIS_HOOK_POSTINSTALL
  ; Purge des raccourcis bureau legacy en doublon (BUG-113).
  Delete "$DESKTOP\THÉRÈSE.lnk"
  SetShellVarContext all
  Delete "$DESKTOP\THERESE.lnk"
  Delete "$DESKTOP\THÉRÈSE.lnk"
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
