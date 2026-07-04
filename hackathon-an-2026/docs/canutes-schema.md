# Schéma Canutes — introspection

> Introspecté en direct (PostgreSQL, `information_schema`) le 2026-07-03.
> Base **unifiée `canutes`** (253 tables/vues). Le PostgREST public
> (`db.code4code.eu/canutes/`) n'expose QUE 3 tables génériques
> (`services`, `communes`, `version`) → pour les articles, passer par la
> **connexion directe** (`.env` `CANUTES_DB_*`) ou le SQL Moulineuse.

## Bases sur le serveur
`canutes` (unifiée, routée par PgBouncer — la seule connectable directement),
`canutes_assemblee`, `canutes_europe`, `canutes_legifrance`, `senat`.

## Schémas de `canutes`
| Schéma | Contenu |
|---|---|
| `legifrance` | **articles, textes, codes, sections, JO, dossiers législatifs** |
| `assemblee` | acteurs, amendements, dossiers, réunions, scrutins, Éliasse (temps réel), dérouleur |
| `senat` | `ameli_*`, `debats_*`, `dosleg_*` (noms très cryptiques) |
| `droits_et_demarches` | fiches pratiques Service-public |
| `annuaire` | communes, services |
| `europe`, `anomalies` | liens titres UE ; anomalies de données |

## Table clé : `legifrance.article`
| Colonne | Type | Note |
|---|---|---|
| `id` | character | ID Légifrance (`LEGIARTI…`, `JORFARTI…`) → URL `legifrance.gouv.fr/codes/article_lc/{id}` |
| `num` | text | numéro, **format variable** : `L3121-27` ou `L. 3121-27` |
| `data` | jsonb | XML Légifrance : `META` (NUM, **ETAT** VIGUEUR/ABROGE, dates), `CONTEXTE` (hiérarchie du code), `BLOC_TEXTUEL.CONTENU` (texte), `LIENS`, `NOTA`, `VERSIONS` |

### Vérifier un article (implémenté dans `src/data/canutes.py::verify_article`)
1. `num` : matcher par **variantes exactes** (`L3121-27`, `L. 3121-27`, …) —
   PAS de `regexp_replace` sur toute la table (scan complet → statement timeout).
2. `code` : filtrer `data::text ILIKE '%<code>%'` (le nom du code est dans le
   JSON) + re-check accent-insensible côté Python.
3. Préférer **ETAT = VIGUEUR**. Renvoyer l'ID LEGIARTI (→ URL) + extrait.
- Un `num` peut exister dans plusieurs codes → le filtre code est indispensable
  (ex. `L. 4321-7` existe ailleurs mais **pas** dans le Code du travail).

## Piste « asset » (pitch)
Les noms `senat.ameli_*` / `dosleg_*` sont opaques et peu documentés. Une
**cartographie annotée** du schéma (générée + enrichie) est une contribution
réutilisable — voir [pitch.md](pitch.md) et [ressources.md](ressources.md).
