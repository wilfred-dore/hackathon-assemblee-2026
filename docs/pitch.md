# Pitch — narratif cohérent (à intégrer dans slides.md)

> Ce fichier propose des **ajouts** au deck de François (`slides.md` sur `main`).
> Ne rien supprimer : ce sont des slides/angles à greffer. Wilfred pitche.

## Le fil rouge (une phrase)
**« Une IA juridique de confiance ET souveraine : elle ne cite que du droit
vérifié (Canutes/Légifrance), et elle tourne sur du matériel souverain
non-NVIDIA — même code, du Qualcomm Cloud AI 100 à l'AMD via Modular MAX. »**

## 3 piliers (cohérents entre eux)
1. **Confiance** — le LLM répond, chaque article cité est **vérifié en base
   (Canutes `legifrance.article`, version EN VIGUEUR, lien Légifrance réel)** ;
   au moindre article introuvable → **refus explicite**. Prouvé en Gherkin.
2. **Souveraineté hardware-agnostique** — la couche de confiance est
   **indépendante du fournisseur GPU**. La plupart des déploiements open-source
   sont de fait verrouillés CUDA/NVIDIA ; nous démontrons le **même pipeline**
   sur **Qualcomm Cloud AI 100** (live, prouvé) et, cible, **AMD via Modular
   MAX/Mojo** — swap = 3 variables d'env.
3. **Frugalité & utilité** — perf/watt des accélérateurs dédiés (Cloud AI 100,
   AMD) ; utile pour l'Assemblée (vérif de références dans amendements/questions)
   et pour le citoyen.

## Slides à ajouter (proposition)

### Slide « Le piège NVIDIA » (nouveau)
- Servir un LLM open-source ≈ dépendre de CUDA/NVIDIA (dispo, coût, souveraineté).
- Notre thèse : **portabilité par Modular MAX/Mojo** → écrire une fois, exécuter
  sur AMD / Qualcomm / NVIDIA. Le droit souverain ne devrait pas dépendre d'un
  seul fournisseur US de silicium.

### Slide « Démo hardware-agnostique » (nouveau)
- Live : question citoyenne → réponse **sur Qualcomm Cloud AI 100** (Llama-3.1-8B).
- Panneau **Frugalité & souveraineté** : backend, modèle, latence, tokens/s
  (déjà dans la CLI, `MODE=live`).
- Message : « on change `LLM_BASE_URL`, le même pipeline tourne sur AMD/MAX. »

### Slide « Modular MAX & Mojo » (nouveau)
- **MAX** : runtime d'inférence portable (container OpenAI-compat, AMD/NVIDIA/Apple).
- **Mojo** : langage de kernels — piste : réécrire un hot-path (reranking/matching)
  et le benchmarker (perf/watt). *Stretch goal, à cadrer.*

### Slide « Notre contribution : cartographie Canutes » (nouveau)
- Canutes = 253 tables, schémas cryptiques (`senat.ameli_*`…), PostgREST n'expose
  que 3 tables. Nous avons **introspecté + documenté** le schéma
  ([canutes-schema.md](canutes-schema.md)) → **contribution réutilisable**,
  reversable à Tricoteuses (aligné « Contribuer »). Option : diagramme SchemaSpy.

## ⚠️ Honnêteté (à tenir devant un jury — Wilfred est staff)
- **Perf/watt** : on montre **latence + tokens/s réels** ; les watts ne sont pas
  mesurés sur ces endpoints → citer les specs constructeur (Cloud AI 100 =
  TOPS/W élevé), ne PAS inventer de chiffre de conso.
- **Limite connue** : la vérif contrôle que l'article **existe** (num + code +
  vigueur), pas encore que le **contenu** correspond au propos. Ex. observé : le
  modèle a cité L.2122-4 (existe, mais hors sujet). → **Travaux futurs** :
  ancrage RAG (SQL Moulineuse) + vérif sémantique. À présenter comme feuille de
  route, pas comme déjà fait.
- **Mistral** : non servi par le playground Qualcomm (Llama-3.1-8B only) ; Mistral
  visé via AMD/MAX ou auto-hébergé (Colab). Ne pas prétendre Mistral live tant
  que non branché.

## CiviqHub (side goal) — à faire proprement
Objectif : soutenir la startup d'un étudiant de Wilfred. **Ne pas annoncer un
partenariat ou un intérêt non confirmés** (risque réputationnel + jury). Options
honnêtes, par ordre de préférence :
1. **Le rendre vrai** : un message/quote de CiviqHub confirmant l'intérêt →
   citer nominativement avec accord.
2. **« Integration-ready »** : exposer notre vérification comme **API réutilisable**
   et montrer un adaptateur CiviqHub → dire « prêt à intégrer », ce qui est vrai.
3. **Cas d'usage** : présenter CiviqHub comme *exemple* de débouché (« ce type de
   plateforme citoyenne pourrait consommer notre API »), sans affirmer d'accord.

## Pitch 30 s (Wilfred)
« Les IA juridiques hallucinent des articles — en droit, une réponse fausse est
pire que pas de réponse. Le Rapporteur ne cite que du droit **vérifié dans
Canutes/Légifrance**, sinon il **refuse**. Et il est **souverain jusqu'au
silicium** : le même moteur tourne sur Qualcomm Cloud AI 100 et sur AMD via
Modular MAX — sans CUDA, sans dépendance NVIDIA. Confiance prouvée en Gherkin,
souveraineté prouvée en direct. »
