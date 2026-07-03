# language: fr
Fonctionnalité: IA de confiance — réponses sourcées, pas d'hallucination
  En tant qu'assistant juridique, je ne réponds qu'à partir de sources
  vérifiables et je refuse plutôt que d'inventer.

  Scénario: Refus quand aucune source n'est disponible
    Étant donné une question juridique sans source disponible
    Quand je pose la question à l'assistant
    Alors l'assistant refuse de répondre
    Et la réponse ne contient aucune citation inventée

  Scénario: Aucune citation inventée quand des sources existent
    Étant donné une question juridique avec des sources disponibles
    Quand je pose la question à l'assistant
    Alors chaque citation de la réponse correspond à une source fournie
