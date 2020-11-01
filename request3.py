import redis
import json

from helpers import get_movies_keys_by_actor_id, get_movies_keys_by_director_id

r = redis.Redis()

def get_by_actor_and_director_ids(actor_id, director_id):
  actor_movies_keys = get_movies_keys_by_actor_id(actor_id)
  director_movies_keys = get_movies_keys_by_director_id(director_id)
  movies_keys = []
  res = []
  
  for key in director_movies_keys:
    if key in actor_movies_keys:
      movies_keys.append(key)

  data_items = r.mget(movies_keys)
  
  for item in data_items:
    # Unload the JSON object
    data = json.loads(item.decode('utf-8'))
    item_set = False
    # Order by rank
    if data["rank"] != None:
      for i in range(len(res)):
        if res[i][1] and data["rank"] > res[i][1]:
          res = res[:i] + [(data["name"], data["rank"])] + res[i:]
          item_set = True
          break
    if not item_set:
      res.append((data["name"], data["rank"]))
  for (name, rank) in res:
    print(name, rank)


get_by_actor_and_director_ids(86164, 85162)