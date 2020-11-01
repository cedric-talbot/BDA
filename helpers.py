import redis
import json

r = redis.Redis()

def get_movies_keys_by_actor_id(actor_id):
  item = r.get("actor:"+str(actor_id))
  # Unload the JSON object
  data = json.loads(item.decode('utf-8'))
  movies = []
  for role in data["roles"]:
    movies.append("movie:"+str(role["movie_id"]))
  return movies

def get_movies_keys_by_director_id(director_id):
  item = r.get("director:"+str(director_id))
  # Unload the JSON object
  data = json.loads(item.decode('utf-8'))
  movies = []
  for movie in data["movies"]:
    movies.append("movie:"+str(movie))
  return movies