# FAQ technique — anticiper les questions (jury + nous)

Questions difficiles qu'on peut nous poser, avec des réponses **honnêtes et défendables**.
Distinguer toujours ce qui est **fait** de ce qui est **roadmap** (cf. [roadmap.md](roadmap.md)).

## Modèle & souveraineté

**C'est vraiment souverain si le modèle est Llama (Meta, US) ?**
La souveraineté ici, c'est **contrôler l'exécution** : poids **ouverts**, auto-hébergeables,
aucun appel à un service tiers américain, sur du **matériel qu'on choisit**. La nationalité
du créateur des poids compte moins que le fait qu'ils soient ouverts et exécutés chez nous.
Notre cible modèle est **Mistral** (français, open-weight) ; Llama-3.1-8B est ce que sert
notre backend de démo (Qualcomm Cloud AI 100).

**Pourquoi insister sur « open source / modèle ouvert » ?**
Sans poids ouverts, pas de souveraineté possible (on dépend d'une API fermée US). Les poids
ouverts sont la condition de tout le reste : auto-hébergement, choix du silicium, frugalité.

## Matériel & Modular

**Pourquoi MAX plutôt que vLLM ?**
Les deux sont des moteurs de service **OpenAI-compatibles**. **vLLM** est le standard mature
(PagedAttention, gros écosystème) et c'est même lui qui tourne sur Qualcomm Cloud AI 100 (fork
Qualcomm). **Modular MAX/Mojo** apporte la **portabilité par un seul code** (Mojo → AMD, NVIDIA,
Apple, sans réécriture par vendeur) et des perfs annoncées en tête. Notre pipeline étant
**agnostique** (interface OpenAI-compatible), on peut utiliser **l'un ou l'autre** : on met MAX/Mojo
en avant pour la thèse *portabilité/souveraineté*, vLLM reste une alternative valable.

**Qualcomm Cloud AI 100 tourne-t-il sous MAX ?**
**Non.** Il utilise le **SDK Qualcomm** (compilation ONNX → QPC, avec un fork vLLM). MAX/Mojo
cible **AMD/NVIDIA/Apple**, pas Qualcomm. C'est pour ça que, dans notre schéma, Qualcomm est une
branche *séparée* de MAX. Notre client OpenAI-compatible, lui, parle à n'importe quel endpoint.

**Sur quel matériel tourne MAX/Mojo, concrètement ?**
NVIDIA, AMD, Apple Silicon (même source → CUDA/ROCm/Metal) + CPU. **Pas le TPU** aujourd'hui
(Mojo *vise* à généraliser, non implémenté).

**Le TPU Google, pourquoi pas ?**
Trois raisons : (1) **MAX ne le supporte pas** ; (2) c'est une puce **US (Google)** → ça
contredit la souveraineté matérielle ; (3) y accéder « souverainement » via S3NS (Thales+Google)
ne marche pas non plus, car **S3NS n'est pas SecNumCloud** (ANSSI : infra Google = Cloud Act).

**Apple Silicon peut-il servir nos Mistral en production ?**
Non : c'est du **dev local** (un Mac fait tourner un 7B pour tester, pas pour servir des
utilisateurs). En prod, cibles **datacenter** = AMD / NVIDIA. C'est pourquoi Apple Silicon
n'est pas dans le schéma de déploiement.

## Performance & énergie

**Vous avez fait le benchmark perf/watt vous-mêmes ?**
Non, soyons clairs. On **cite une étude tierce** (UCSD, *Serving LLMs in HPC Clusters*, arXiv
2507.00418) : sur 12 LLM open source, Qualcomm Cloud AI 100 Ultra consomme **10 à 35× moins**
d'énergie qu'un A100 pour un service équivalent (ex. granite-3.2-8B : 36 W vs 1 246 W).
Notre démo, elle, affiche **latence et débit en direct**. On **voulait benchmarker ce cas
d'usage nous-mêmes** ; faute de temps pendant le hackathon, on cite l'étude et on l'assume :
un hackathon, c'est des **arbitrages**. Le benchmark AMD vs NVIDIA via MAX est sur la roadmap.

**Frugalité = argument marketing ?**
Non : un datacenter d'IA, c'est une facture d'électricité et du CO₂. Une puce d'inférence
**dédiée** fait le même travail pour bien moins de watts (et consomme peu à l'idle, cf. l'étude).
Frugalité = **souveraineté énergétique + écologie**.

## Vérification & données

**Pourquoi la DB Canutes directe plutôt que le MCP Moulineuse ?**
Pour la vérification exacte (« l'article existe-t-il dans ce code, en vigueur ? »), un `SELECT`
indexé est **plus rapide, déterministe, sous notre contrôle**. Moulineuse *exécute du SQL* →
c'est la **même base** + une couche protocole. On avait les identifiants → utilisable tout de
suite. Et on n'ignore pas MCP : **on expose notre propre serveur MCP** (`repondre_question`,
`verifier_article`) pour l'interop. Le RAG (roadmap) passera, lui, par le SQL de Moulineuse.
> En une phrase : **on vérifie par la voie la plus directe et déterministe (la base Canutes
> elle-même), et on expose cette vérification en MCP pour que tout l'écosystème puisse la
> réutiliser.**

**Pourquoi *generate → verify* et pas du RAG ?**
Aujourd'hui : le LLM répond, puis on **vérifie l'existence** de chaque article cité (garde-fou
anti-hallucination fort, prouvé en Gherkin). Le **RAG** (ancrer le *contenu*) est la prochaine
étape — défense en profondeur. On l'assume comme roadmap, on ne prétend pas l'avoir.

**Limite connue : et si le modèle cite un vrai article, mais hors-sujet ?**
On valide aujourd'hui l'**existence** (num + code + vigueur), pas encore la **pertinence
sémantique**. C'est exactement ce que le RAG corrigera. On le dit franchement.

**Le RAG a-t-il besoin d'une base vectorielle (Qdrant) ?**
Non, pas obligatoire : un RAG **lexical** (recherche plein-texte Canutes, ou l'outil SQL de
Moulineuse) suffit. Le vector store (recall sémantique) est une étape ultérieure.

## Déploiement & production

**Comment ça passerait à l'échelle à l'Assemblée ?**
Souveraineté **à deux étages** : (1) puce souveraine (Qualcomm Cloud AI 100, AMD/MAX) ;
(2) **cloud souverain SecNumCloud** (NumSpot, Outscale, OVHcloud) pour la juridiction et la
résidence des données. Qualcomm Cloud AI 100 permet en plus une **allocation granulaire**
(par SoC), utile en multi-tenant (cf. étude UCSD).

**La démo publique tourne-t-elle sur le vrai moteur ?**
La démo *publique* (GitHub Pages) est un **précalcul statique** (sûr, pas d'abus de tokens).
Le **moteur souverain live** (Qualcomm Cloud AI 100 + vérif Canutes) tourne **sur scène** via
`make api`. Choix assumé : tokens limités, pas de serveur LLM public.

## Références
- UCSD, *Serving LLMs in HPC Clusters: Qualcomm Cloud AI 100 Ultra vs NVIDIA* — <https://arxiv.org/abs/2507.00418>
- Modular 25.6 (NVIDIA/AMD/Apple) — <https://www.modular.com/blog/modular-25-6-unifying-the-latest-gpus-from-nvidia-amd-and-apple>
- Architecture & accès aux données : [architecture.md](architecture.md) · Roadmap : [roadmap.md](roadmap.md)
