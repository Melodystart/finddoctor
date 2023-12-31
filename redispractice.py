import redis
import json
pool = redis.BlockingConnectionPool(timeout=10,host='localhost', port=6379, max_connections=40, decode_responses=True)
r = redis.Redis(connection_pool=pool)

# for elem in r.keys():
#   r.delete(elem)

# r.set('food', 'beef', ex=10)
# print(r.get('food'))

my_dict = {"name": "Micky"}
dict_str = json.dumps(my_dict)
r.lpush("list",dict_str)

py_dict = {"name": "Pika"}
dict_str = json.dumps(py_dict)
r.lpush("list",dict_str)
# r.expire("list", time=10)

print(r.lrange('list',0,-1))
# dict_str = r.lrange('list', 0,-1)[0]
# my_dict = json.loads(dict_str)
# print(my_dict['name'])

# lst = [{"name": "Micky"},{"name": "Pika"}]
# r.hmset("hash", {"key":lst})
# print(r.hmget("hash", "key"))