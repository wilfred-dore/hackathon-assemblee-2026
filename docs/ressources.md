# Ressources orga — endpoints & schémas

> ⚠️ À COMPLÉTER : colle ici le deck ressources de l'orga (URLs exactes,
> identifiants publics, schémas). Ne mets JAMAIS de token/secret ici → `.env`.

## Endpoints connus (déjà câblés dans .env.example)
| Ressource | URL | Auth |
|-----------|-----|------|
| MCP Moulineuse | `https://mcp.hackathon2026.leximpact.dev/mcp` | à confirmer (TODO auth) |
| MCP Parlement | *(fourni par l'orga sur place)* | `MCP_TOKEN` |
| Canutes PostgREST | `https://db.code4code.eu/canutes/` | public ? à confirmer |
| Canutes DB directe | `hackathon2026.leximpact.dev:5432` (user `hackathon2026`) | `CANUTES_DB_PASSWORD` |
| LLM (OpenAI-compat) | Modular MAX / AMD (distant) — fallback playground Qualcomm | `LLM_API_KEY` |

## À coller depuis le deck orga
- [ ] Liste exacte des tables/vues Canutes utiles.
- [ ] Schéma d'auth MCP (Bearer ? header custom ? session initialize ?).
- [ ] URL exacte + modèle de l'endpoint LLM souverain.
- [ ] Schémas Tricoteuses (Node) si utilisés.
