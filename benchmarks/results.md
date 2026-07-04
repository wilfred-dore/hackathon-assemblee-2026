# Résultats de benchmark

Mesures **réelles** sur un MacBook **M2 Pro (16 Go)**, le **2026-07-04**.
Reproduire les graphiques : `uv run --with matplotlib python benchmarks/plot_benchmarks.py`

## 1. Kernel de calcul (Apple Silicon) — `compute_kernel.png`

Similarité cosinus, 100 000 comparaisons, dimension 384 (représentatif du scoring RAG).
Code et détail : [`examples/mojo/`](../examples/mojo/).

| Implémentation | Temps | Note |
|---|---|---|
| Python pur | ~850 ms | interprété |
| **Mojo** (SIMD, natif arm64) | **~7,6 ms** | **114×** vs Python pur, sans lib BLAS |
| NumPy (BLAS multi-thread) | ~2,9 ms | reste devant — honnête |

Les trois trouvent le même `best_idx` (contrôle inter-langage).

## 2. Portabilité (PAS un benchmark de perf) — `llm_backends.png`

⚠️ **Ce n'est pas un classement matériel apples-to-apples** : modèles et infras
différents. C'est une **démonstration de portabilité** — le même pipeline tourne du
cloud souverain FR au 100 % local sur un Mac, en changeant une variable d'env.

| Backend | Latence | Débit | Rôle |
|---|---|---|---|
| Mistral La Plateforme (FR) | 0,86 s | 39,4 tok/s | cloud souverain FR |
| Ollama local, Mistral 7B (M2 Pro) | 1,21 s | 32,3 tok/s | 100 % local, hors-ligne |

**Qualcomm Cloud AI 100 retiré du graphique** : l'endpoint mesuré était un **essai
gratuit Cirrascale** (instance partagée/bridée, modèle Llama-3.1-8B), ~1,49 s / 22
tok/s — **non représentatif** du Cloud AI 100 Ultra. Sa vraie force (frugalité) est
au §3, sourcée UCSD. Un vrai comparatif matériel demanderait le **même modèle** sur
NVIDIA / AMD / Qualcomm (serveur) et Apple / Snapdragon X Elite (bureau) — travaux futurs.

## 2bis. La thèse — hallucination — `hallucination_thesis.png`

Agrégé de la mini-étude (§4) : petit modèle local **83 %** d'hallucination, grand
modèle **~8 %**, **Le Rapporteur 0 %** (présentée). Le graphique clé du projet.

## 3. Frugalité — `energy_efficiency.png`

**Donnée externe citée, non mesurée par nous.** UCSD, arXiv 2507.00418 : Qualcomm
Cloud AI 100 = **10 à 35× moins d'énergie** qu'un NVIDIA A100 (12 LLM open source).

## 4. Pourquoi on vérifie : hallucinations observées en direct

Même question (« durée légale du travail en France ? », bonne réponse : **article
L. 3121-27 du Code du travail**). Citations produites :

| Backend | Article cité | Correct ? |
|---|---|---|
| Ollama local (Mistral 7B) | L. 3121-1 **et** L. 3121-2 | ❌ faux |
| Qualcomm (Llama-3.1-8B) | L. 3122-2 | ❌ faux |
| Mistral La Plateforme | variable selon l'appel | ⚠️ à confirmer |

**Trois backends, trois numéros d'article inventés.** C'est précisément ce que la
couche de vérification attrape : *on ne fait confiance à aucun modèle, on vérifie.*
La mesure systématique de ce taux (avec vs sans vérification) est le cœur de notre
benchmark de recherche (gardé privé).
