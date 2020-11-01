import redis
import json
from collections import defaultdict

r = redis.Redis()

def get_movies_keys_by_actor_id(actor_id):
  item = r.get("actor:"+str(actor_id))
  # Unload the JSON object
  data = json.loads(item.decode('utf-8'))
  movies = []
  for role in data["roles"]:
    movies.append("movie:"+str(role["movie_id"]))
  return movies



def get_by_actor_id(actor_id):
  # Get the movies
  movies_keys = get_movies_keys_by_actor_id(actor_id)
  data_items = r.mget(movies_keys)
  genres = defaultdict(int)
  for item in data_items:
    # Unload the JSON object
    data = json.loads(item.decode('utf-8'))
    for genre in data["genres"]:
      genres[genre] += 1
  for genre in genres.keys():
    print(genre, genres[genre]/len(movies_keys))

get_by_actor_id(86164)
