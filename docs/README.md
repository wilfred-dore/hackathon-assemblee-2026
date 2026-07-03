# Documentation interne — Le Rapporteur

Index de la doc technique. Diagrammes en Mermaid (rendus par GitHub / dbdiagram).

## Vue d'ensemble
- [architecture.md](architecture.md) — **pipeline de confiance** + **arbre de
  déploiement LLM/GPU** (souveraineté hardware-agnostique) + vulgarisation
  Qualcomm Cloud AI 100.
- [pitch.md](pitch.md) — narratif de pitch, slides à greffer, garde-fous
  d'honnêteté, CiviqHub.
- [defis.md](defis.md) — défis visés.

## Souveraineté / matériel
- [gpu.md](gpu.md) — stratégie backends (Qualcomm Cloud AI 100 *live*, MAX
  AMD/NVIDIA, Colab), statuts honnêtes.

## Données & schéma (asset)
- [ressources.md](ressources.md) — endpoints orga (Canutes, MCP, APIs).
- [canutes-schema.md](canutes-schema.md) — logique de vérification d'article.
- [schema/README.md](schema/README.md) — cartographie du schéma (JSON/DBML/HTML),
  [schema/inferred_relations.md](schema/inferred_relations.md) (relations déduites).
- [mcp.md](mcp.md) — schéma des outils MCP (à compléter sur place).

## Code (rappels)
- Moteur : `src/pipeline.py` (question → LLM → extraction → vérif → sourcé/refus).
- LLM OpenAI-compatible swappable : `src/llm/client.py` (`MODE=demo|live`).
- Vérif Canutes réelle : `src/data/canutes.py::verify_article`, `src/verify.py`.
- API + UI (fusion) : `src/api.py` (sert l'UI de François sur notre moteur).
- Serveur MCP : `poc/rapporteur/api.py` (`/mcp` : `repondre_question`, `verifier_article`).
- Preuves : `features/` (Gherkin FR), régénération schéma : `tools/gen_schema.py`.

## Publication
- Site statique (Pages) : `poc/build_static.py` → `site/` (app + `site/schema/`).
- Workflow : `.github/workflows/deploy-pages.yml`.
