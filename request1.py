import redis
import json

r = redis.Redis()

def get_by_actor_name(first_name, last_name):
  # Get all the actors
  keys = r.keys("actor:*")
  data_actors = r.mget(keys)
  movie_ids = []
  res = []
  for item in data_actors:
    # Unload the JSON object
    obj = json.loads(item.decode('utf-8'))
    if obj["first_name"] == first_name and obj["last_name"] == last_name:
      for role in obj["roles"]:
        # Already add the redis keys instead of the ids alone
        movie_ids.append("movie:"+str(role["movie_id"]))

  # Get the corresponding movies from the keys
  data_movies = r.mget(movie_ids)
  for item in data_movies:
    # Unload the JSON object
    obj = json.loads(item.decode('utf-8'))
    res.append(obj["name"])
  return res

def get_by_director_name(first_name, last_name):
  # Get all the directors
  keys = r.keys("director:*")
  data_directors = r.mget(keys)
  movie_ids = []
  res = []
  for item in data_directors:
    # Unload the JSON object
    obj = json.loads(item.decode('utf-8'))
    if obj["first_name"] == first_name and obj["last_name"] == last_name:
      for movie_id in obj["movies"]:
        # Already add the redis keys instead of the ids alone
        movie_ids.append("movie:"+str(movie_id))

  # Get the corresponding movies from the keys
  data_movies = r.mget(movie_ids)
  for item in data_movies:
    # Unload the JSON object
    obj = json.loads(item.decode('utf-8'))
    res.append(obj["name"])
  return res

print(get_by_actor_name("Sergio", "Dayrell"))
print(get_by_director_name("Basilio", "Zubiaur"))