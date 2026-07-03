# hackathon-assemblee-2026 — IA de confiance juridique

> 🌐 **Démo & docs en ligne** : **<https://wilfred-dore.github.io/hackathon-assemblee-2026/>** (hall d'accueil)
> · [Pitch](https://wilfred-dore.github.io/hackathon-assemblee-2026/pitch.html)
> · [Démo](https://wilfred-dore.github.io/hackathon-assemblee-2026/demo.html)
> · [Comment ça marche](https://wilfred-dore.github.io/hackathon-assemblee-2026/details.html)
> · [Schéma Canutes](https://wilfred-dore.github.io/hackathon-assemblee-2026/schema/)
>
> ⚠️ Sur GitHub Pages (statique), utiliser les URL **avec `.html`** (le `/pitch` sans
> extension est rattrapé par un `404.html` de secours). Les URL propres `/pitch`,
> `/demo` ne marchent qu'en **live** (`make api`).

Assistant juridique **sourcé** : le LLM répond, puis **chaque article cité est
vérifié** contre les sources (MCP Moulineuse / Canutes-Légifrance). Au moindre
article introuvable — ou en l'absence de citation vérifiable — la réponse est un
**refus explicite** (« Je ne trouve pas de texte applicable »). Objectif : zéro
citation inventée.

Défense en profondeur : ancrage RAG (retrieval) **+** fact-check des citations a
posteriori. Scaffold agnostique : marche pour les 3 défis (« La loi après la
loi », « NormaCheck », « IA de confiance souveraine »). Voir [SETUP.md](SETUP.md).

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

`question → (ancrage retrieval) → génération LLM → extraction des citations →
vérification de chaque article → réponse sourcée ou refus`
(voir [src/pipeline.py](src/pipeline.py)).
