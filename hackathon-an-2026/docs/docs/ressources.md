# Ressources orga — endpoints & exploitation

> Source : deck officiel « Présentation des ressources » (E. Raviart & P. Drège,
> 3–4 juillet 2026), 26 pages. ✅ = confirmé par le deck.
> ⚠️ Aucun secret ici (fichier commité) → mots de passe / tokens dans `.env`.

## Données brutes (open data)
| Source | URL | Format |
|---|---|---|
| Assemblée nationale | `https://data.assemblee-nationale.fr/` | XML, JSON, CSV (manque les *textes*) |
| Sénat | `https://data.senat.fr/` | dump PostgreSQL ancien |
| Légifrance (Dila) | `https://echanges.dila.gouv.fr/OPENDATA/` | XML — **textes consolidés (codes)** |
| Service-public.fr (Dila) | `https://echanges.dila.gouv.fr/OPENDATA/` | XML — guide droits & démarches |

## Données nettoyées (Tricoteuses, sous Git, JSON)
| Source | URL |
|---|---|
| Assemblée nettoyée | `https://git.en-root.org/tricoteuses/data/assemblee-nettoye` |
| Sénat | `https://git.tricoteuses.fr/senat` |
| Légifrance/Dila | `https://git.tricoteuses.fr/dila` (XML + Markdown/HTML) |
| **Codes consolidés** | `https://git.tricoteuses.fr/codes` ← vérité de référence articles |
| Constitution 1958 | `https://git.tricoteuses.fr/constitution/constitution_du_4_octobre_1958` |
| Schémas JSON | `https://www.tricoteuses.fr/{assemblee,senat,legifrance}/schemas` |

## Base de données Canutes (PostgreSQL unifiée)
- Dumps hebdo : `https://dump.tricoteuses.fr/`
- **Accès direct** : `hackathon2026.leximpact.dev:5432` · user `hackathon2026` ·
  dbname `hackathon2026` · **mot de passe → `.env` (`CANUTES_DB_PASSWORD`)**
- Données ajoutées : textes AN, temps réel (vidéos, dérouleur « jaune » de séance,
  Éliasse = amendements en temps réel, scrutins).

## APIs
| API | URL | Contenu |
|---|---|---|
| **PostgREST** | `https://db.code4code.eu/canutes/` | tout Canutes, structuré, REST filtré |
| **Parlement** | `https://parlement.tricoteuses.fr/docs` | AN + Sénat, données à plat |

## MCP (Model Context Protocol)
| MCP | URL | Nature |
|---|---|---|
| **Moulineuse** | `https://mcp.hackathon2026.leximpact.dev/mcp` (ou `tricoteuses.fr/services/mcp-moulineuse`) | **exécute SQL + JavaScript** sur tout Canutes (« API survitaminée »), recettes métier |
| **Parlement** | `https://www.tricoteuses.fr/services/mcp-parlement` | MCP classique, outils ≈ API Parlement, AN+Sénat |

> ⚠️ **Moulineuse n'est PAS un outil `search`** : c'est de l'exécution SQL/JS.
> Notre `retrieve()`/`MoulineuseVerifier` devront appeler l'outil réel (type
> `execute_sql`) — faire `describe_tools()` sur place, cf. [mcp.md](mcp.md).

## GPU / LLM
**❌ ABSENT du deck ressources.** Aucun endpoint d'inférence, MAX, AMD ni Qualcomm
n'est fourni par l'orga dans ce document. À confirmer via le canal orga (Wilfred
est staff) ou on amène le nôtre. Stratégie retenue → voir [gpu.md](gpu.md).

## Comment on exploite chaque ressource (pipeline de confiance)
- **Vérification de citation** (cœur) : MCP Moulineuse → SQL sur Canutes pour
  prouver qu'un article existe + récupérer le texte consolidé. Repli :
  PostgREST (`db.code4code.eu/canutes/`) si le MCP tombe.
- **Ancrage / RAG** : SQL/JS Moulineuse pour ramener les passages sourcés.
- **Fixtures démo hors-ligne** : cloner `git.tricoteuses.fr/codes` (1–2 codes)
  dans `data/fixtures/` → vérité de référence sans réseau.
- **Défis « loi après la loi » / territoire** : API/MCP Parlement (amendements,
  dossiers, scrutins) + Éliasse temps réel.
- **Schémas Tricoteuses** : partie Node (validation JSON) + pour connaître la
  forme réelle des tables/champs avant d'écrire le SQL.

## Défis officiels (site) — 6, pas 3
Webmcp-AN · **ComparIA juridique** (fiabilité LLM sur questions juridiques
citoyennes ← notre moteur de confiance) · fil hypertexte continu · analyse
groupes d'intérêt · ParlementClair · loi & territoire.
