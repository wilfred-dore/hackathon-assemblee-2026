# Carte de schéma Canutes — `legifrance` + `assemblee`

Documentation **lisible par un agent/LLM** (l'asset : les schémas Tricoteuses en
ligne sont derrière un anti-bot Anubis ; Canutes est cryptique et sous-exposé).

## Fichiers
- **`canutes_schema.json`** — machine-readable (tables → colonnes, types, PK).
  À donner à un LLM/MCP pour écrire du SQL correct.
- **`canutes.dbml`** — coller sur <https://dbdiagram.io> pour un diagramme.
- Régénérer : `MODE=live uv run python tools/gen_schema.py` (extra `db`).

Périmètre : 42 tables, 164 colonnes (`legifrance` + `assemblee`).

## ⚠️ Aucune clé étrangère déclarée en base
Canutes est **dénormalisé** (colonnes `jsonb` `data`, pas de contraintes FK).
Conséquence : **ni dbdiagram ni SchemaSpy ne tracent de relations** (il n'y en a
pas à découvrir automatiquement). Les liens sont **implicites**, encodés dans les
`id` Légifrance et le `data` jsonb. D'où l'intérêt de la carte annotée ci-dessous.

> 🌐 Site statique publiable (SchemaSpy + formats machine, **sans endpoint/secret**)
> dans [`/site`](../../site) → prêt pour GitHub Pages.
> 🔗 Relations **déduites** (Mermaid, étiquetées) : [inferred_relations.md](inferred_relations.md).

## Relations implicites clés (curées, `legifrance`) — *inférées, non contraintes*
Les `id` Légifrance portent le type dans leur préfixe :
- `LEGIARTI…` = article · `LEGISCTA…` = section (hiérarchie du code) ·
  `LEGITEXT…` = texte/code · `JORFARTI…` = version JO.

| Table | Rôle | Lien implicite |
|---|---|---|
| `legifrance.article` | articles (`id`, `num`, `data`) | `data.CONTEXTE` → sections `LEGISCTA` (arbre du code) ; `data.META…ETAT` = VIGUEUR/ABROGE |
| `legifrance.article_contenu_avec_liens` | contenu + liens résolus | par `id` d'article |
| `legifrance.article_lien` / `article_lien_extrait` | liens entre articles | `LEGIARTI` → `LEGIARTI` |
| `legifrance.section_ta` / `section_ta_git` | sections (arbre) | `LEGISCTA` ; parent de l'article |
| `legifrance.texte_version` / `_lien` / `_git` | texte/code | `LEGITEXT` ; racine = le code |
| `legifrance.dossier_legislatif` | dossiers | liés aux textes AN (voir `texte_version_dossier_legislatif_assemblee_associations`) |

Pour `assemblee` : `acteurs`, `amendements`, `dossiers`, `documents`, `organes`,
`reunions`, `scrutins`, `eliasse_amendements` (temps réel) — liens par `uid`/`ref`
dans les colonnes `jsonb` (idem : pas de FK déclarée).

## Vérifier un article (déjà implémenté)
Voir [`../canutes-schema.md`](../canutes-schema.md) et
`src/data/canutes.py::verify_article` : num (variantes) + code (ILIKE) + VIGUEUR
→ ID LEGIARTI → URL Légifrance.

## SchemaSpy (rendu HTML humain) — généré
Site HTML navigable (colonnes, types, détail par table). Généré en local pour
`legifrance` (23 tables) et `assemblee` (19 tables) → `out/schemaspy/` (gitignoré,
volumineux ; partager en zip ou régénérer). **Relations quasi vides** (pas de FK
en base) — d'où l'intérêt des relations implicites curées ci-dessus.

Reproduire :
```bash
# 1) deps
brew install graphviz            # fournit `dot`
curl -L -o schemaspy.jar   https://github.com/schemaspy/schemaspy/releases/download/v6.2.4/schemaspy-6.2.4.jar
curl -L -o postgresql.jar  https://repo1.maven.org/maven2/org/postgresql/postgresql/42.7.4/postgresql-42.7.4.jar
# 2) run (password lu depuis .env, jamais en dur)
PW=$(grep -E '^CANUTES_DB_PASSWORD=' .env | cut -d= -f2-)
java -jar schemaspy.jar -t pgsql -dp postgresql.jar \
  -host hackathon2026.leximpact.dev -port 5432 -db canutes \
  -u hackathon2026 -p "$PW" -s legifrance -o out/schemaspy/legifrance -imageformat png
```
> ⚠️ Le fat jar est celui des **releases GitHub** (pas Maven Central, qui n'est
> pas exécutable). Les warnings `dot ... cell size too small` sont cosmétiques.
