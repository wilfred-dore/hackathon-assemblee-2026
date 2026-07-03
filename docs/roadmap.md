# Roadmap — fait / à faire (honnête)

Document de travail **interne** : distinguer ce qui **tourne** de ce qui est **visé**.
(Une version orientée jury peut en être dérivée, mais celle-ci est pour nous.)

## ✅ Fait (démontrable)
- Moteur de confiance **generate → verify** : réponse sourcée ou **refus explicite**.
- **Vérification en base Canutes directe** (`legifrance.article`, num+code+VIGUEUR → lien Légifrance réel). Fail-closed.
- **Backend LLM souverain LIVE** : Qualcomm Cloud AI 100 (Cirrascale, Llama-3.1-8B), OpenAI-compatible, swappable (`MODE=demo|live`).
- **Preuve BDD Gherkin FR** (3 scénarios), exécutée en continu.
- **API** `/answer`, `/verify` (fact-check CiviqHub) + **serveur MCP** (`repondre_question`, `verifier_article`).
- **UI institutionnelle** (François) servie par notre moteur ; **deck de pitch** ; **panneau frugalité** (latence/tokens/s).
- **Asset doc schéma Canutes** (JSON/DBML/SchemaSpy + relations déduites).

## 🗺️ À faire
### 1. RAG / ancrage amont (retrieve → generate)  ← la question du moment
Aujourd'hui on ne fait **pas** de RAG (generate → verify seulement).

**Faut-il Qdrant / une base vectorielle ? NON, pas obligatoire.**
- **RAG lexical** (recherche plein-texte) — *pas de vector DB* :
  - via **MCP Moulineuse** (exécute du SQL/JS — c'est *fait pour ça*, « recettes métier »), **idéalement** ; nom d'outil à confirmer sur place (`describe_tools`),
  - ou **Postgres FTS direct** (`to_tsvector('french', …)` sur le contenu d'article).
- **RAG sémantique** (embeddings + Qdrant) : meilleure recall sur paraphrases, **mais** indexer *tout* Canutes (millions d'articles) = infaisable en 1 jour → **roadmap lointaine**. *(Cirrascale expose des embeddings BAAI/bge : techniquement possible, l'indexation est le mur.)*

**Estimation (RAG lexical) : ~2–4 h.** Étapes : mots-clés de la question → recherche
plein-texte (MCP Moulineuse **ou** Postgres) → top-K passages → passer en contexte à
`generate()` (**déjà supporté** : `llm.complete(question, context)`).

**Ce qui manque / le risque :** un **index plein-texte** sur les articles. Sans index,
une FTS sur toute la table `legifrance.article` = **timeout** (cf. notre souci regexp
initial). Donc : (a) l'outil de recherche **MCP Moulineuse** (optimisé — à confirmer
sur place), (b) une colonne `text_search`/index existante, ou (c) scoper à un
sous-corpus (quelques codes). **Le vrai inconnu = la voie de recherche efficace, pas le vector DB.**

### 2. Mistral en live
Aujourd'hui Qualcomm ne sert que Llama-3.1-8B. Mistral via **MAX/AMD** ou Colab auto-hébergé.

### 3. Bench Modular MAX + Mojo (NVIDIA / AMD)
Hot-path Mojo benchmarké (perf/watt) — sur place, quand GPU dispo.

### 4. Unifier le serveur MCP sur notre moteur
Le `/mcp` (poc) utilise le moteur POC ; le faire pointer sur la vérif Canutes live.
