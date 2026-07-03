# SETUP — hackathon-assemblee-2026

## Environnement détecté (2026-07-03)

| Outil   | Version        | Rôle |
|---------|----------------|------|
| git     | 2.39.5         | ✅ versionnage |
| python3 | 3.13.2         | ✅ langage principal |
| uv      | 0.11.21        | ✅ gestion env/deps |
| node    | 25.6.1         | ✅ optionnel (schémas Tricoteuses) |
| docker  | **absent**     | ⚠️ non requis pour ce scaffold |
| make    | 3.81           | ✅ raccourcis |

## Démarrage

```bash
cd /Users/wdore/Projects/hackathon-assemblee-2026
make setup     # uv sync + crée .env depuis .env.example
make smoke     # smoke test end-to-end en mode mock (sans clés)
make bdd       # scénarios Gherkin (behave)
```

## À remplir dans `.env` (jamais commité)

| Clé | Où l'obtenir |
|-----|--------------|
| `LLM_BASE_URL` / `LLM_API_KEY` / `LLM_MODEL` | endpoint OpenAI-compatible : Mistral via Modular MAX (AMD). Fallback : playground Qualcomm. |
| `MCP_MOULINEUSE_URL` | déjà pré-rempli (`https://mcp.hackathon2026.leximpact.dev/mcp`) |
| `MCP_PARLEMENT_URL` / `MCP_TOKEN` | **fournis par l'orga sur place** |
| `CANUTES_REST_URL` | déjà pré-rempli |
| `CANUTES_DB_PASSWORD` | fourni par l'orga (si accès DB direct) |

Sans clés, tout tourne en **mock** : le pipeline refuse (« pas de source, pas de
réponse ») — c'est le comportement de confiance à démontrer.

## Accès DB direct (optionnel)

Non installé par défaut. Si tu veux psycopg (jointures SQL lourdes) :

```bash
make db        # = uv sync --extra db
```

## Prochaines actions

1. Remplir `.env` avec les tokens LLM + MCP dès que dispo.
2. Dans [src/pipeline.py](src/pipeline.py), brancher les vrais appels dans
   `retrieve()` (nom réel de l'outil MCP `search`, requêtes Canutes).
3. Confirmer le schéma d'auth MCP dans [src/mcp/client.py](src/mcp/client.py)
   (`TODO(auth)`).
4. Déposer 1–2 lois de démo dans [data/fixtures/](data/fixtures/).
5. (Selon défi) brancher OpenFisca/Catala dans [src/rules/](src/rules/).

## Choix du défi — le scaffold marche pour les 3

1. **« La loi après la loi »** — analyser l'effet d'une loi après adoption
   (retrieval versions consolidées via Canutes/Moulineuse + quantification
   OpenFisca).
2. **« NormaCheck »** — vérifier la conformité/cohérence normative d'un texte
   (retrieval + validation, garde-fous anti-hallucination).
3. **« IA de confiance souveraine »** (notre défi) — LLM souverain (Mistral/MAX
   sur AMD) + sources vérifiables + refus si pas de source.

Le flux commun (question → retrieval → réponse sourcée → validation) est déjà en
place ; seul le branchement des sources/règles change selon le défi.
