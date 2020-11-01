# Rapport de Bases de Données Avancées

## Fonctionnement de la base de données NoSQL Redis

La base de données NoSQL choisie dans le cadre de ce projet est la base de données Redis. Son fonctionnement suit le principe Key-Value, c'est à dire que chaque enregistrement stocké est associé à une clé unique, qui est le seul moyen d'accéder à cet enregistrement. Redis stocke les enregistrements sous 4 formats principaux: chaînes de caractères, listes, ensembles et dictionnaires string-string.
La principale spécifité de Redis est que toutes les données sont stockées en mémoire RAM et non sur des serveurs, ce qui accélère grandement toutes les transactions puisqu'il n'y a plus besoin de faire de lecture/écriture sur disque, opération qui prend un temps conséquent notamment pour les bases de données relationnelles, qui se doivent de stocker leurs enregistrements sur des disques.

## Importation des données dans la solution

Les données originales sont des données SQL, qui ne sont pas adaptées à un stockage NoSQL sous le format Key-Value. J'ai donc décidé de réorganiser les données pour suivre le schéma suivant:
```
{
    "actor:<actor-id>": {
        "first_name",
        "last_name",
        "genre",
        "roles": [{
            "role",
            "movie_id"
        }]
    },
    "director:<director-id>": {
        "first_name",
        "last_name",
        "genres": [{
            "genre",
            "prob",
        }],
        "movies": [<movie-id1>,...]
    },
    "movie:<movie-id>": {
        "name",
        "year",
        "rank",
        "genres": [<genre1>,...]
    }
}
```
Les clés utilisées par Redis seront donc de trois formes différentes, selon que l'enregistrement soit un acteur, un réalisateur ou un film.
Il est important de noter que Redis ne supporte pas un format complexe de cette forme, ainsi les enregistrements ne seront pas stockés en tant qu'objets mais en tant que chaînes de caractère, après avoir été convertis en JSON.
L'importation des données est faite dans le fichier `init_db.py`.
Pour créer la DB Redis, il faut tout d'abord installer redis-server pour lancer un serveur Redis local
```
wget http://download.redis.io/redis-stable.tar.gz
tar xvzf redis-stable.tar.gz
cd redis-stable
make
sudo make install
redis-server
```
Vous pouvez désormais lancer `init_db.py` pour importer les données
```
pip3 install redis
python3 init_db.py
```

## Traduction des requêtes

### 1. Titre de films d’un acteur/réalisateur donné
Les requêtes SQL sont les suivantes:
```
SELECT name FROM movies WHERE id IN (
    SELECT movie_id FROM roles WHERE actor_id IN (
        SELECT id FROM actors WHERE first_name=<actor_first_name> AND last_name=<actor_last_name>
    )
);

SELECT name FROM movies WHERE id IN (
    SELECT movie_id FROM movies_directors WHERE director_id IN (
        SELECT id FROM directors WHERE first_name=<director_first_name> AND last_name=<director_last_name>
    )
);
```
La version Redis de ces requêtes se trouve dans le fichier `request1.py`.
Voici ci-dessous les résultats retournés pour l'acteur Sergio Dayrell puis le réalisateur Basilio Zubiaur.
![](https://i.imgur.com/LABjxTX.png)

Cette requête ne présente pas de réelle difficulté, mis à part le fait qu'il faut traiter l'ensemble des acteurs/réalisateurs puisque l'on cherche un nom et non un id. 

### 2. Genres (proportions) de film d’un acteur/réalisateur donné
J'ai choisi ici de considérer que l'on part d'un id d'acteur/réalisateur et non d'un nom. Si l'on part d'un nom, il suffit de refaire la même étape que précédemment pour récupérer les id à partir du nom: 
```
SELECT id FROM actors WHERE first_name=<actor_first_name> AND last_name=<actor_last_name>
```
La requête SQL pour les acteurs est la suivante:
```
SELECT diff.genre AS genre,
       diff.N / total.N AS prop
FROM ( SELECT genre, COUNT(*) AS N
       FROM movies_genres
       WHERE movie_id IN (SELECT movie_id FROM roles WHERE actor_id=<actor-id>)
       GROUP BY genre
     ) diff
JOIN ( SELECT COUNT(DISTINCT movie_id) AS N
       FROM roles WHERE actor_id=<actor-id>
     ) total;
```
La requête pour les réalisateurs est extrêmement similaire, puisqu'il suffit simplement de prendre la correspondance réalisateur/film dans `movies_directors` au lieu de `roles`, de la même manière que pour la requête 1.
La version Redis de cette requête se trouve dans le fichier `request2.py`.
Voilà ci-dessous le résultat pour l'acteur d'ID 86164, ainsi que le résultat obtenu via la requête SQL dans la BDD MySQL.

![](https://i.imgur.com/SKOhwts.png)

![](https://i.imgur.com/X1ZtBhk.png)

Cette requête est bien plus complexe que la première, car elle demande une jointure pour avoir en même temps le nombre de films pour chaque genre et le nombre total de films (avec la spécificité que certains films n'ont pas de genre et sont pris en compte dans le calcul). On se rend également compte qu'en cherchant les acteurs par ID, on n'a besoin que de récupérer très peu d'enregistrements de la BDD Redis, ce qui fait que la requête totale est extrêmement rapide.

### 3. Films les plus populaires (rang) pour un couple acteur - réalisateur

On se place une nouvelle fois dans le cas où l'on recherche un couple acteur-réalisateur en connaissant leurs IDs.
La requête SQL est la suivante:
```
SELECT name, rank FROM movies WHERE id IN (
    SELECT movie_id FROM movies_directors WHERE movie_id IN (
        SELECT movie_id FROM roles WHERE actor_id=<actor-id>
    ) AND director_id=<director-id>
) ORDER BY rank;
```
La version Redis de cette requête se trouve dans le fichier `request3.py`.
Voici les résultats pour l'acteur d'id 86164 et le réalisateur d'id 85162, ainsi que le résultat obtenu via la requête SQL dans la BDD MySQL. Ici, le rank est à NULL pour tous les films, je n'ai pas réussi à trouver de couple (acteur, réalisateur) avec plusieurs films ayant un rang.

![](https://i.imgur.com/4Dku8eA.png)

![](https://i.imgur.com/MzW7E4G.png)

Cette requête a été plus simple à écrire que la précédente, ne nécessitant pas de jointure, et est également très rapide en NoSQL puisqu'on n'a besoin de récupérer que très peu d'enregistrements (un acteur, un réalisateur et ici 3 films).

### 4. Couples d’acteurs qui ont joués le plus ensemble pour un genre de film donné.

Pour simplifier la requête, on cherche ici les id des acteurs et non leur nom complet (facilement obtensibles à partir des ids).
La requête SQL est la suivante:
```
SELECT COUNT(act1.movie_id) AS counter, act1.actor_id, act2.actor_id FROM (
    SELECT actor_id, movie_id FROM roles WHERE movie_id IN (
        SELECT movie_id FROM movies_genres WHERE genre=<genre>
    )
) act1
JOIN (
    SELECT actor_id, movie_id FROM roles WHERE movie_id IN (
        SELECT movie_id FROM movies_genres WHERE genre=<genre>
    )
) act2 
ON act1.movie_id=act2.movie_id AND act1.actor_id<>act2.actor_id
GROUP BY act1.actor_id, act2.actor_id
ORDER BY counter ASC;
```
Cette requête a cependant un défaut que je n'ai pas réussi à corriger, elle affiche tous les couples d'acteurs ainsi que le nombre de films de chaque couple, au lieu d'afficher seulement le(s) couple(s) ayant le plus joué ensemble. Cependant, puisque l'order est fait de manière ascendante, les derniers enregistrements affichés sont ceux que l'on recherche.
La version Redis de cette requête se trouve dans le fichier `request4.py`.
Voici les résultats pour le genre 'Film-Noir', ainsi que le résultat obtenu via la requête SQL dans la BDD MySQL.

![](https://i.imgur.com/K1tASOI.png)

![](https://i.imgur.com/5ENhYLF.png)

Cependant, étant donné le format de données que je me suis fixé au début, cette requête est extrêmement complexe à calculer et demande un temps beaucoup trop long. Ainsi, la version Redis ne termine pas en temps raisonnable pour la plupart des genres.

Cette requête est de loin la plus complexe de toutes, et la plus longue car elle demande de croiser des valeurs pour des couples d'acteurs, ce qui nous donne donc un temps de calcul quadratique en le nombre d'acteurs. Le format Redis choisi au début de ce rapport n'est de plus pas adapté à ce genre de requête.