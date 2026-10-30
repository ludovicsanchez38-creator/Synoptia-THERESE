# Contre-épreuve CPython réelle

Deux extensions du `.deb` THÉRÈSE v0.82.0 publié, jamais exécutées :
`THERESE_0.82.0_amd64.deb`, SHA-256
`211423b73bd5d5ba19b2520cce936a8322f0fee95626cb7ed3b48c17ce39fd3b`.
Chemin dans le paquet :
`usr/lib/THERESE/binaries/backend-libs/_internal/python3.13/lib-dynload/`.

| Fichier décompressé | Octets | SHA-256 |
| --- | ---: | --- |
| `pyexpat.cpython-313-x86_64-linux-gnu.so` | 957232 | `83b0fc81ac9b06f2871ef4c2c884954d8f0cf258d3408d7ddb5dc58e161709e0` |
| `_decimal.cpython-313-x86_64-linux-gnu.so` | 1915176 | `a7760dba58eb7feb93dfbb508d073383c5651943bda673591728037e779732f5` |

Compression gzip déterministe (`mtime=0`), sans modification des ELF. Provenance :
témoins de `/tmp/therese-relecture6-d94p6vfv/`, rapprochés une nouvelle fois du
paquet publié. CPython est sous PSF-2.0 ; Expat incorporé sous MIT et libmpdec
sous BSD-2-Clause. pyexpat incorpore aussi le SipHash-2-4 de William Ahern sous
CC0-1.0, attesté par ses définitions `sip24_update` et `sip24_final`.
Notices originales dans `licenses/cpython/`, reprises dans
`THIRD_PARTY_LICENSES`. Les définitions locales et versions sont enregistrées
dans `licenses/cpython/evidence-v0820.json`.

`THIRD_PARTY_LICENSES-round6.txt.gz` conserve les 6 009 037 octets de la notice
du commit `b6d629c39ebb49fb129a641c44cecdd3709ac45a` : SHA-256 décompressé
`1a3b4b00637a184daca7a2f2bb0a96ccfee237892cf15a3ec9826beb8888c23a`.
Ce témoin défectueux est uniquement une entrée négative du test, jamais une
ressource du produit. Il rend le test autonome sur un checkout CI superficiel.

Le test reprend les propriétés de runner de la contre-épreuve (stdlib, version
et suffixe ABI) et les vraies fonctions `record_analysis`, `build_inventory`,
`load_build`, puis la CLI `verify_packaged_licenses.py`. Ni classification,
ni empreintes, ni résultats de garde ne sont simulés. Le paquet test est
assemblé par `dpkg-deb`, sans installation. Aucun appel de publication.
