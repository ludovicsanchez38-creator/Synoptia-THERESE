# U4 - En fenêtre réduite, l'établi ne peut jamais être entièrement dégagé

- **Gravité** : mineur
- **Nature** : friction_ux
- **Source** : constaté à l'écran, 900 × 700 px

À 900 × 700, le composeur est en surimpression au bas de la colonne. Mesures
après **défilement maximal** de la zone :

```
composeur    y = 520
établi       y = 486, hauteur 38  →  bas à 524
```

Les cinq verbes (*Écrire*, *Retrouver*, *Préparer*, *Facturer*, *Décider*)
finissent donc **4 px sous** le bord haut du composeur, et rien ne permet de les
dégager : le défilement est déjà en butée.

Pas de débordement horizontal, le rail reste visible, le composeur reste
utilisable. L'établi reste lisible et cliquable sur 34 de ses 38 px. C'est un
défaut de mise en page, pas une perte de fonction — d'où la gravité mineure.

Il vaut surtout comme signal : c'est le genre d'écart qu'aucun test unitaire ne
mesure, et qui devient visible dès qu'on réduit la fenêtre.
