# Mojo sur Apple Silicon — preuve d'agnosticité matérielle

Petit artefact **reproductible** derrière la promesse « le même code tourne sur
Apple Silicon, sans NVIDIA » de la présentation (slide 06, souveraineté matérielle).

## Ce que ça prouve (et ce que ça ne prouve pas)

- ✅ Mojo compile en **binaire natif arm64** (Mach-O) et s'exécute sur un **MacBook
  M2 Pro**, sans GPU, sans CUDA, sans lib BLAS d'un vendeur.
- ✅ Le **même code source** vise ensuite un GPU NVIDIA ou AMD via le moteur MAX —
  c'est ça l'agnosticité matérielle qu'on revendique.
- ✅ Mojo et Python trouvent le **même `best_idx`** : contrôle de correction
  inter-langage, dans l'esprit « de confiance ».
- ❌ On ne prétend **pas** battre NumPy. Notre kernel est mono-thread et naïf ;
  NumPy s'appuie sur un BLAS multi-thread et reste devant ici. Le point de Mojo
  n'est pas « plus rapide que NumPy sur un kernel », c'est **du code façon Python à
  vitesse native + portabilité GPU**, sans dépendre d'une lib compilée tierce.

## Résultats mesurés (M2 Pro, 100 000 comparaisons, dim 384)

| Implémentation | Temps | Note |
|---|---|---|
| Python pur | ~850 ms | lisible mais interprété |
| **Mojo** (SIMD, natif arm64) | **~7,6 ms** | ~114× vs Python pur, code façon Python |
| NumPy (BLAS multi-thread) | ~2,9 ms | baseline honnête, reste devant |

Les trois trouvent `best_idx = 68` (score ≈ 1,0).

## Lancer

```bash
# Mojo (toolchain installé localement)
mojo run retrieval_similarity.mojo
mojo build retrieval_similarity.mojo -o /tmp/sim && /tmp/sim

# hello
mojo run hello.mojo

# Comparaison Python / NumPy
uv run --with numpy python retrieval_similarity.py
```

## Note de version

Validé sur le toolchain **Mojo 0.7.0** installé sur la machine. L'API Mojo évolue
vite (imports `memory` / `SIMD`, gestion des pointeurs) ; sur un toolchain récent,
adapter les imports si la compilation échoue. L'algorithme, lui, ne change pas.

## Pourquoi c'est dans « Le Rapporteur »

La vérification juridique du Rapporteur passe aujourd'hui par une requête **directe**
dans Canutes (déterministe, pas d'embedding). Ce kernel illustre le **chemin chaud
d'un RAG** (scorer N articles candidats) si on l'ajoutait : il montre que cette
brique peut tourner en Mojo, portable d'Apple Silicon au GPU, sans réécrire le code
par plateforme. C'est une **démonstration d'agnosticité**, pas un composant actif du
pipeline.
