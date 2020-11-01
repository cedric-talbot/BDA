import mysql.connector
import redis
import json

# Open connection to mysql DB
mydb = mysql.connector.connect(
  host="relational.fit.cvut.cz",
  port=3306,
  user="guest",
  password="relational",
  database="imdb_ijs",
)
mycursor = mydb.cursor()

# Open connection to local Redis DB (requires you to run a local redis server)
r = redis.Redis()

# A pipeline allows us to only call the server once instead of calling it with every request
with r.pipeline() as pipe:
  obj = {}
  # Adding actors to obj
  mycursor.execute("SELECT * FROM actors")
  for x in mycursor:
    obj["actor:"+str(x[0])] = {
      "first_name": x[1],
      "last_name": x[2],
      "genre": x[3],
      "roles":[]
    }

  mycursor.execute("SELECT * FROM roles")
  for x in mycursor:
    obj["actor:"+str(x[0])]["roles"].append({
      "movie_id": x[1],
      "role": x[2]
    })

  # Adding directors to obj
  mycursor.execute("SELECT * FROM directors")
  for x in mycursor:
    obj["director:"+str(x[0])] = {
      "first_name": x[1],
      "last_name": x[2],
      "genres": [],
      "movies": []
    }
  
  mycursor.execute("SELECT * FROM directors_genres")
  for x in mycursor:
    obj["director:"+str(x[0])]["genres"].append({
      "genre": x[1],
      "prob": x[2]
    })

  mycursor.execute("SELECT * FROM movies_directors")
  for x in mycursor:
    obj["director:"+str(x[0])]["movies"].append(x[1])

  # Adding movies to obj
  mycursor.execute("SELECT * FROM movies")
  for x in mycursor:
    obj["movie:"+str(x[0])] = {
      "name": x[1],
      "year": x[2],
      "rank": x[3],
      "genres": []
    }

  mycursor.execute("SELECT * FROM movies_genres")
  for x in mycursor:
    obj["movie:"+str(x[0])]["genres"].append(x[1])

  for key in obj.keys():
    # Redis doesn't support complex objects, so they will be stored as JSON strings
    json_obj = json.dumps(obj[key])
    pipe.set(key, json_obj)

  pipe.execute()
r.bgsave()
