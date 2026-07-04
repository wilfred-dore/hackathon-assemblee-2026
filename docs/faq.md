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

> 🧱 Contexte utile avant ces questions : **la stack complète d'un LLM**, étage par
> étage (modèle, moteur, langage GPU, silicium, cloud) → [stack.md](stack.md).

**Pourquoi Modular MAX / Mojo plutôt que ROCm / vLLM ?**
Attention, ce ne sont pas les mêmes couches :
- **ROCm** = la couche **bas-niveau** d'AMD (l'équivalent de CUDA chez NVIDIA). Ce n'est **pas**
  un concurrent de MAX : c'est *sur* ROCm que vLLM s'exécute côté AMD.
- **vLLM** et **MAX** sont deux **moteurs de service** OpenAI-compatibles (l'étage au-dessus).
- **Mojo** est un **langage de kernels** qui génère le code pour **ROCm (AMD), CUDA (NVIDIA) et
  Metal (Apple) depuis une seule source**.

La vraie comparaison, c'est donc **vLLM vs MAX** :
- **vLLM** : mature, énorme écosystème, PagedAttention. Mais structuré autour de **CUDA** (NVIDIA),
  avec un portage **ROCm** (AMD) souvent en retrait. C'est lui qui sert notre backend Qualcomm.
- **MAX / Mojo** : pensé **vendeur-neutre dès le départ** → un seul code pour AMD/NVIDIA/Apple,
  sans réécriture ; perfs annoncées en tête (non re-vérifiées par nous).

**Notre position** : le pipeline est **agnostique** (interface OpenAI-compatible), donc il tourne
aussi bien sur vLLM que sur MAX. On met **MAX/Mojo** en avant car c'est le plus cohérent avec la
**souveraineté matérielle** (pas de verrou d'écosystème CUDA) ; mais **vLLM (+ROCm sur AMD) reste
un choix pragmatique tout aussi valable**. C'est justement le point : on n'est enfermés dans aucun
des deux.
> *Validation académique de la portabilité Mojo* : une étude (arXiv 2509.21039) montre Mojo à
> **87 % de CUDA** (NVIDIA H100) et **à parité avec HIP** (AMD MI300A), depuis **une source unique**.
> À cadrer honnêtement : ce sont des **kernels HPC**, pas de l'inférence LLM.

**Nuance importante (à ne pas survendre) : HIP fait DÉJÀ AMD + NVIDIA.** `hipcc` compile pour AMD
(ROCm) *et* pour NVIDIA (backend CUDA). Donc la portabilité cross-vendor **n'est pas propre à Mojo**.
Le vrai plus de Mojo : il **ajoute Apple Silicon** (Metal), vit dans l'**écosystème Python** (pas du
C++ bas-niveau), et s'intègre à un **moteur d'inférence (MAX)** — stack unifiée. On n'oppose donc pas
Mojo à HIP dogmatiquement : on choisit Mojo/MAX pour l'intégration et l'étendue des cibles, pas parce
que « HIP ne saurait pas ».

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
- UCSD, *Serving LLMs in HPC Clusters: Qualcomm Cloud AI 100 Ultra vs NVIDIA* — <https://arxiv.org/abs/2507.00418> (frugalité)
- *Mojo: MLIR-Based Performance-Portable HPC Science Kernels on GPUs* — <https://arxiv.org/abs/2509.21039> (portabilité Mojo NVIDIA/AMD)
- Modular 25.6 (NVIDIA/AMD/Apple) — <https://www.modular.com/blog/modular-25-6-unifying-the-latest-gpus-from-nvidia-amd-and-apple>
- Architecture & accès aux données : [architecture.md](architecture.md) · Roadmap : [roadmap.md](roadmap.md)
