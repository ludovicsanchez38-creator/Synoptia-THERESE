# Trois règles Chrome ciblées, proposition diagnostic_only

Acteur préparateur : /root/shared4_execution. Revue physique et statique le 2026-10-08 à 16:20:45 UTC.

Le profil proposé chrome.sb (2 375 octets) conserve exactement le préfixe de 2 067 octets du profil ROOT10, SHA 19808ee2cac3169e9fb8c71c24385bcbb97f924c5ed785f4651817ecaa179b0c. Il ajoute un commentaire diagnostic_only et ces trois formes, sans autre delta :

```scheme
(allow mach-lookup (global-name "com.apple.CARenderServer"))
(allow iokit-open-user-client (iokit-user-client-class "IOSurfaceRootUserClient"))
(allow iokit-open-user-client (iokit-user-client-class "AGXDeviceUserClient"))
```

Le dossier conserve la préimage complète, le diff avant et le diff inverse. Aucun fichier de ROOT10, aucun ancien profil, code, gel, dépôt ou état .app-loop n'a été modifié.

## Provenance des refus

kernel-evidence.json dérive uniquement du journal fermé 25smI0KQ, rehashé à son SHA 6593b92a19c9368dda614ce78e5c41042c3a28cdbc531d865d63eb7869a076fa (139 932 octets). Le reçu MAIN abed48bd… et ses cinq références physiques sont exacts.

Le journal contient 139 événements et 61 messages distincts. Pour la naissance Chrome 70792 / 1791474774 / 727823, jointe exactement au reçu Chrome fermé, il contient quatre refus CARenderServer plus un avis de doublon, un refus IOSurfaceRootUserClient et un refus AGXDeviceUserClient. Les deux derniers ont chacun un message IOUC/MACF adjacent. Ces refus sont constatés ; ils ne prouvent pas la cause de l'échec CDP.

ROOT10 demeure rouge : aucun résultat ni reçu ne devient vert par cette proposition.

## Syntaxe primaire locale

Les références physiques complètes des trois fichiers système sont indexées, comme données de syntaxe seulement. Seuls ces extraits ont servi :

- com.apple.GameOverlayUI.sb, lignes 112–118 : allow mach-lookup / global-name avec le littéral com.apple.CARenderServer.
- com.apple.gputoolsserviced.sb, lignes 28–29 et 45 : allow iokit-open-user-client / iokit-user-client-class, avec exactement les deux classes proposées.
- appsandbox-common.sb, lignes 669–671 : même famille iokit-user-client-class que le RootDomainUserClient déjà présent dans la préimage.

Aucune autre règle de ces profils système n'est copiée ou héritée.

## Contrôles réellement exécutés

14 tests Python purs sont passés, zéro échec/erreur, retour outil edbf5b code 0. returned-output.log est le texte combiné retourné par l'outil, pas un sink stdout/stderr direct. Les tests contrôlent préimage exacte, delta complet, conservation des formes, diffs avant/inverse et refus de modifications supplémentaires, classes/permissions divergentes et syntaxe déséquilibrée.

verify_profile.py est un lecteur limité aux S-expressions utilisées ici, pas le compilateur Apple. Aucun profil n'a été compilé ou exécuté. Aucun Node, Chrome, G1, Session, socket, service, processus QA, scan système, nouvelle racine ou GO n'a été lancé/créé.

Rejeu statique possible, sous une autorisation séparée si souhaitée :

```sh
python3 -I -B -c 'import sys,unittest; sys.path.insert(0,"/private/tmp/therese-c17-chrome-targeted-three-McWh5vFc"); import test_verify_profile; result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(test_verify_profile)); raise SystemExit(0 if result.wasSuccessful() else 1)'
```

## Fermeture du périmètre

Aucun ajout clipboard/pasteboard, AppleEvents, HID, configd, lsd.modifydb, préférences réelles, wildcard IOKit ou lookup Mach global sans nom. Aucun ajout réseau, données, écriture, subpath, exécutable, argument, port ou profil utilisateur. Les droits initiaux sont conservés, pas élargis hors des trois règles nommées.

Les bornes antérieures CDP 5 s / startup 50 s / cleanup 8 s ne sont pas changées : aucun contrôleur n'est dérivé dans ce lot. Flags, capacités, admissions et autorité restent inchangés. Ce profil n'est ni installé ni admis, aucune prochaine mesure native n'est autorisée ici, aucune qualification FULL, produit, A/B ou release n'est revendiquée.

Un futur renderer/runtime et un essai de l'hypothèse demandent une décision externe exacte et une revue indépendante. Le présent INDEX n'est pas cette autorité.
