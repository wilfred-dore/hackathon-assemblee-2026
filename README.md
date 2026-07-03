# hackathon-assemblee-2026 — IA de confiance juridique

Assistant juridique **sourcé** : chaque réponse s'appuie sur une source vérifiable
(MCP Moulineuse/Parlement, base Canutes, OpenFisca) — **et refuse de répondre s'il
n'a pas de source**. Objectif : zéro citation inventée.

Scaffold agnostique : marche pour les 3 défis (« La loi après la loi »,
« NormaCheck », « IA de confiance souveraine »). Voir [SETUP.md](SETUP.md).

## Lancer en 30 s

```bash
make setup   # crée l'env uv + installe les deps
make smoke   # smoke test end-to-end en mode mock (SANS vraies clés)
make bdd     # scénarios Gherkin (behave)
```

Copie `.env.example` → `.env` et remplis tes tokens quand tu les as (voir SETUP).
Sans clés, tout tourne en **dry-run/mock**.
