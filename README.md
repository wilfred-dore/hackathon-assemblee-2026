# hackathon-assemblee-2026 — IA de confiance juridique

> 🌐 **Démo & docs en ligne** : **<https://wilfred-dore.github.io/hackathon-assemblee-2026/>** (hall d'accueil)
> · [Présentation](https://wilfred-dore.github.io/hackathon-assemblee-2026/presentation/)
> · [Démo](https://wilfred-dore.github.io/hackathon-assemblee-2026/demo.html)
> · [Comment ça marche](https://wilfred-dore.github.io/hackathon-assemblee-2026/details.html)
> · [Schéma Canutes](https://wilfred-dore.github.io/hackathon-assemblee-2026/schema/)
>
> La **présentation** (deck Slidev) est publiée sous `/presentation/`. Les autres pages
> statiques utilisent l'extension `.html` (un `404.html` rattrape les URL sans extension).

Assistant juridique **sourcé** : le LLM répond, puis **chaque article cité est
vérifié** dans les sources officielles (base **Canutes / Légifrance**). Au moindre
article introuvable, ou en l'absence de citation vérifiable, la réponse est un
**refus explicite** (« Je ne trouve pas de texte applicable »). Objectif : zéro
citation inventée.

> **Notre parti pris** : on vérifie par la voie la plus directe et déterministe,
> la base Canutes elle-même, et on **expose cette vérification en MCP** pour que
> tout l'écosystème puisse la réutiliser.

Aujourd'hui : *génération → vérification* (fact-check a posteriori). L'ancrage
amont (RAG) est sur la [roadmap](docs/roadmap.md). Scaffold agnostique : marche
pour les 3 défis (« La loi après la loi », « NormaCheck », « IA de confiance
souveraine »). Voir [SETUP.md](SETUP.md) · [FAQ technique](docs/faq.md).

## Résultats (mesurés le 2026-07-04, MacBook M2 Pro)

Mini-étude, 12 questions de droit, vérité-terrain = le bon article :

| | Citations juridiques hallucinées |
|---|---|
| Petit modèle local (Mistral 7B, frugal/souverain) | **83 %** |
| Grand modèle (moyenne du panel testé) | ~8 % |
| **Le Rapporteur (LLM + vérification)** | **0 % présentée** |

**Plus on veut une IA frugale et locale, plus la vérification est indispensable.**
Le même pipeline tourne sur Mistral La Plateforme (🇫🇷), en 100 % local sur Mac
(Ollama) et sur Qualcomm Cloud AI 100, en changeant une seule variable d'env.
Détail : [benchmarks/](benchmarks/) · [graphiques](benchmarks/results.md) ·
[papier (draft)](paper/main.pdf) · [ressources exploitées](docs/ressources-exploitees.md).

## Lancer en 30 s

```bash
make setup   # crée l'env uv + installe les deps
make smoke   # smoke test end-to-end en mode démo (SANS vraies clés)
make bdd     # scénarios Gherkin (behave) — 3 scénarios de confiance
```

Démo du refus en direct (hors-ligne, LLM démo déterministe) :

```bash
uv run python -m src.cli "Quelle est la durée légale du travail ?"  # -> RÉPONSE SOURCÉE + lien Légifrance
uv run python -m src.cli "Ai-je droit à la prime de Noël ?"          # -> REFUS (article inventé détecté)
```

Copie `.env.example` → `.env`. `MODE=demo` par défaut (hors-ligne) ; passe à
`MODE=live` + tokens pour brancher MAX/MCP réels.

## Pipeline

`question → génération LLM → extraction des citations → vérification en base
(Canutes / Légifrance) → réponse sourcée ou refus`
(voir [src/pipeline.py](src/pipeline.py)).
