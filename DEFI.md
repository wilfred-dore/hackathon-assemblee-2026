# Le Rapporteur — IA de confiance juridique et souveraine

> Hackathon Assemblée nationale 2026 · Défi « IA de confiance souveraine »  
> Équipe : **Wilfred Doré** · **François Amat**

---

## Le défi

Défi **« IA de confiance souveraine »** — et, par sa conception modulaire, applicable aux deux autres défis (« La loi après la loi », « NormaCheck »).

**Problème :** les LLM répondent en prose fluide et autoritaire aux questions juridiques, mais ils inventent des références qui n'existent pas. Une citation confiante mais fausse est *pire* qu'un aveu d'ignorance. Dahl et al. (2024) montrent que les LLM généralistes produisent des hallucinations légales à taux élevé et systématique.

**Notre invariant :** **Zéro article inventé. Chaque citation vérifiée.** Le système refuse plutôt que fabriquer.

---

## La solution

**Le Rapporteur** est un assistant juridique *fail-closed* : le LLM génère librement, mais aucune réponse n'atteint l'utilisateur sans que chaque article cité ait été vérifié, un par un, contre la base de données juridique de référence (Canutes / Légifrance). Le premier article non résolu — ou toute erreur de vérification — déclenche un refus explicite : *« Je ne trouve pas de texte applicable. »*

Le pipeline en quatre étapes :

```
Question → LLM (souverain) → Extraire citations → Vérifier chacune (Canutes/Légifrance)
                                                            ↓
                               Toutes vérifiées → Réponse sourcée + lien Légifrance
                               Au moins une absente → REFUS explicite
```

---

## Architecture technique

| Composant | Choix | Statut |
|---|---|---|
| LLM | Mistral/Llama via endpoint OpenAI-compatible | live (Qualcomm Cloud AI 100) |
| Retrieval / vérification | MCP Moulineuse (SQL/JS, Canutes complet) | live |
| Base juridique | Canutes — miroir PostgreSQL Légifrance (253 tables) | live |
| Rules-as-code | OpenFisca (API web) | branché |
| Tests | behave (Gherkin FR — Soit/Quand/Alors) | 3 scénarios verts |
| Serving souverain | Qualcomm Cloud AI 100 (live) · AMD via Modular MAX (visé) | live |
| Langage | Python (uv) | — |

**Vérificateur cite-friendly :** les numéros d'articles Légifrance s'écrivent de façon inconsistante (`L3121-27`, `L. 3121-27`, `L.3121-27`…). Plutôt qu'un scan regex (timeout), on étend chaque citation en un ensemble fermé de variantes exactes et on interroge l'index `num` par égalité — vérification interactive sans scan de table.

**Service réutilisable :** `POST /verify` soumet *n'importe quel* texte (sortie d'un autre LLM) et retourne, citation par citation, si elle est réelle et en vigueur + le lien Légifrance primaire. Exposé aussi en serveur **MCP** (JSON-RPC 2.0) pour qu'un agent tiers hérite de la garantie.

---

## Démo en ligne

🌐 **<https://wilfred-dore.github.io/hackathon-assemblee-2026/>**

| Page | URL |
|---|---|
| Accueil | [/](https://wilfred-dore.github.io/hackathon-assemblee-2026/) |
| Démo interactive | [/demo.html](https://wilfred-dore.github.io/hackathon-assemblee-2026/demo.html) |
| Comment ça marche | [/details.html](https://wilfred-dore.github.io/hackathon-assemblee-2026/details.html) |
| Consulter les sources | [/sources.html](https://wilfred-dore.github.io/hackathon-assemblee-2026/sources.html) |
| Schéma Canutes | [/schema/](https://wilfred-dore.github.io/hackathon-assemblee-2026/schema/) |

---

## Lancer en local

```bash
make setup   # crée l'env uv + installe les deps
make smoke   # smoke test end-to-end (mode démo, sans vraies clés)
make bdd     # scénarios Gherkin (3 scénarios de confiance)
make bench   # benchmark 100 questions (MODE=live + .env)
```

```bash
# Exemples hors-ligne (mode démo déterministe)
uv run python -m src.cli "Quelle est la durée légale du travail ?"
# -> RÉPONSE SOURCÉE + lien Légifrance (L.3121-27)
uv run python -m src.cli "Ai-je droit à la prime de Noël ?"
# -> REFUS (L.4321-7 inventé — n'existe pas dans la base)
```

---

## Diapositives de présentation

#### Diapositives de présentation
[Diapositives de présentation](docs/diapositives.pdf)

---

## Papier de recherche

Papier VLDB/PVLDB (format *acmart sigconf*) — 8 pages.  
Compilation : `cd paper && tectonic main.tex`

#### Papier de recherche
[Le Rapporteur — Fail-Closed, Database-Verified Legal QA on Sovereign Hardware](docs/paper.pdf)

---

## Dépôt

<https://github.com/wilfred-dore/hackathon-assemblee-2026>
