import redis
import json
from collections import defaultdict

from helpers import get_movies_ids_from_genre

r = redis.Redis()

def get_couple(genre):
  movies_ids = get_movies_ids_from_genre(genre)

  actors_keys = r.keys("actor:*")
  actors_data = r.mget(actors_keys)
  # Get list of actors for each movie
  actors_by_movie = defaultdict(list)
  for i in range(len(actors_data)):
    data = json.loads(actors_data[i].decode('utf-8'))
    for role in data["roles"]:
      if str(role["movie_id"]) in movies_ids:
        actors_by_movie[role["movie_id"]].append(actors_keys[i][6:])

  # Get the amount of movies for each couple of actors
  couples = defaultdict(int)
  for movie in actors_by_movie.keys():
    for actor1 in actors_by_movie[movie]:
      for actor2 in actors_by_movie[movie]:
        if actor1 != actor2:
          couples[(actor1.decode('utf-8'), actor2.decode('utf-8'))] += 1

  # Get the maximum
  max = 0
  res = ()
  for couple in couples.keys():
    if couples[couple] > max:
      max = couples[couple]
      res = couple
  return res

print(get_couple('Film-Noir'))