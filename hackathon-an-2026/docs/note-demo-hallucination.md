
🎯 Moment de démo en or : le Llama souverain a répondu « article L. 3132-2 du Code du travail » — c'est FAUX (le bon est L. 3121-27 ; L. 3132-2 concerne le repos hebdomadaire). Donc le LLM souverain hallucine un numéro d'article plausible mais faux, en live — et c'est exactement ce que notre couche de vérification attrape (L.3132-2 non vérifiable → refus). C'est ta démonstration la plus percutante : vrai modèle souverain + vraie hallucination + garde-fou qui la bloque.

Confirmations :

Notre LLMClient marche en live sur Qualcomm/Cirrascale (live=True).
MODE=demo reste déterministe : BDD 3/3.
Je mets à jour docs/gpu.md (backend #2 confirmé) et je commit le code (pas le .env).
