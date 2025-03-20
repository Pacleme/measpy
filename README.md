# Mes modifications
## signal.py
Ajout du type de signal
## ni.py
Ajout de sortie digital

# A regarder
## Tests (testing.py)
### Algo MatchResults
- Version 1 `matchResults()` : 
    - Fonctionnel mais très lent sur un grand nombre de données
    - Idée générale : parcours toutes les valeurs, crééer et remplies une liste petit a petit pour lier les vals d'une même adresse chronologiquement.
- Version 2 `matchResultsSpeedUp()` : 
    - Pas encore très bien testé
    - à priori fonctionnel et très rapide sur une grande différence entre FS et FB.
    - Très lent lorsque FS et FB sont proches
    - Idée générale : parcours les valeurs par adresse, regroupe d'un coup toutes les valeurs mesurées sur une même adresse.
- Version 3 `matchResultsSpeedUpV2()` :
    - Pas encore très bien testé
    - à priori fonctionnel et très rapide dans tous les cas.
    - Idée générale : utilisation des fonctions de numpy le plus possible.
- 
### Algo ScaleAddresses
- Version 1 `scaleAddresses()` :
    - Fonctionnel