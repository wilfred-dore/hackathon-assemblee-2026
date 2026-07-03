# CLAUDE.md — Contexte projet

## Contexte
Hackathon Assemblée nationale 2026 (48h). Thème : « Le parcours de la loi : vers une IA de confiance ».
Ce qui gagne : CONFIANCE (sourçage, zéro hallucination) + SOUVERAINETÉ + UTILITÉ pour l'AN. Pas le côté "wow".
Équipe : Wilfred (infra/build/pitch), François (scénarios juridiques + réseau). Défi PAS encore verrouillé → rester modulaire.
Défis candidats : (1) La loi après la loi, (2) NormaCheck, (3) notre défi "IA de confiance souveraine". Le code doit marcher pour les 3.

## Règle d'architecture NON négociable
Le LLM ne répond JAMAIS de mémoire. Il interroge le MCP / Canutes, cite la source primaire, et REFUSE explicitement si aucune source fiable ("Je ne trouve pas de texte applicable").
Les chiffres passent par OpenFisca/Catala (rules-as-code), jamais inventés. Une couche Gherkin/BDD valide chaque réponse (citation existe, pas de jurisprudence inventée, chiffres corrects).

## Stack (décidée)
- LLM : Mistral souverain via endpoint OpenAI-compatible (Modular MAX sur AMD, distant). Fallback : playground Qualcomm (Llama).
- Retrieval : MCP Moulineuse (SQL/JS, tout Canutes) + MCP Parlement ; sinon API PostgREST Canutes.
- Rules-as-code : OpenFisca (API web), Catala.
- Tests : behave (Gherkin), scénarios EN FRANÇAIS (`# language: fr`, Soit/Quand/Alors), lisibles par un juriste.
- Langage : Python (uv). Node seulement pour les schémas Tricoteuses.

## Nuances techniques importantes
- En LOCAL je suis un CLIENT d'un endpoint distant : NE PAS lancer `docker run --gpus` sur ce Mac. Le GPU AMD est distant (TensorWave/AMD cloud).
- Avant d'appeler un outil MCP : vérifier son schéma réel (describe) — ne pas inventer la forme des tools/params.
- Secrets UNIQUEMENT dans .env (jamais dans le code ni dans ce CLAUDE.md).

## Style de travail attendu
- Priorité vitesse et lisibilité (hackathon). Pas d'over-engineering.
- Proposer un plan court avant les grosses modifs ; demander avant toute install lourde ou commande destructive.
- Commits fréquents et petits. Tenir SETUP.md à jour (avancement + prochaines actions).
- Toujours garder un mode dry-run/mock qui tourne SANS vraies clés.
- Wilfred est ingénieur senior en calcul accéléré → être dense et technique, pas de hand-holding.
- François écrit les `.feature` → scénarios en français, langage métier, pas techniques.
- Wilfred pitche → à chaque étape, générer un court résumé "ce que fait la démo en 30 s".

## Contraintes temps
Gel samedi 14h (restitution ~16h). Rendu + démo prêts 2h avant. Ce qui doit être VISIBLE à la démo : sources cliquables, scénarios Gherkin vert/rouge, panneau frugalité (perf/watt).

## Repères repo
- `make setup | smoke | bdd` — voir [README.md](README.md) / [SETUP.md](SETUP.md).
- Flux de confiance : [src/pipeline.py](src/pipeline.py) (question → retrieval → réponse sourcée → validation, refus si pas de source).
- Endpoints/tokens : `.env` (jamais commité), template dans [.env.example](.env.example).
- Docs de référence (endpoints exacts, défis, schémas MCP) : [docs/](docs/).
