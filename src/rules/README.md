# rules/ — moteur de règles juridiques (à brancher)

Dossier réservé aux calculs de droit « exécutable ». Rien ici pour l'instant :
on branche selon le défi choisi.

## Pistes

- **OpenFisca** (Python / API web) : simulateur socio-fiscal. Deux options
  - appeler l'API web publique en HTTP (simple, pas d'install lourde) ;
  - importer un package `openfisca-france` si on doit modifier des paramètres.
  Utile pour « quantifier » l'effet d'une réforme (défi « La loi après la loi »).

- **Catala** : langage dédié à l'encodage exécutable du droit. Plutôt pour
  démontrer une règle précise vérifiable. Nécessite le toolchain Catala.

## Convention suggérée

Exposer une fonction `evaluate(case: dict) -> dict` par moteur, pour que
`pipeline.py` puisse l'appeler de façon uniforme.
