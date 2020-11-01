import redis
import json
from collections import defaultdict

from helpers import get_movies_keys_by_actor_id

r = redis.Redis()

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
