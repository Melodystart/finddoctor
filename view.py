import redis
import json
from py_test import *
from model import *

pool = redis.BlockingConnectionPool(timeout=10,host='localhost', port=6379, max_connections=40, decode_responses=True)
r = redis.Redis(connection_pool=pool)

def view_redis_review(data,inputtext, result):
    for d in data:
      item = {}
      item["name"] = d[0]
      item["star"] = d[1]
      try:
          item["when"] = untilNow(float(d[2]))
      except:
          pass
      item["review"] = d[3]
      item["link"] = d[4]
      item["location"] = d[5]
      result["data"].append(item)
      r.rpush("Review-"+inputtext,json.dumps(item))
    r.expire("Review-"+inputtext, time=60*60*24*7)
    return result

def view_redis_business(data,inputtext, result):
    for d in data:
      item = {}
      item["name"] = d[0]
      item["posttime"] = untilNow(float(d[1]))
      item["comment"] = d[2]
      item["createdAt"] = d[3]
      item["link"] = d[4]
      item["location"] = d[5]
      result["data"].append(item)
      r.rpush("Business-"+inputtext,json.dumps(item, default=str))
    r.expire("Business-"+inputtext, time=60*60*24*7)
    return result

def view_redis_judgment(data,inputtext, result):
    for d in data:
      item = {}
      item["url"] = d[0]
      item["title"] = d[1]
      result["data"].append(item)
      r.rpush("Judgment-"+inputtext,json.dumps(item, default=str))
    r.expire("Judgment-"+inputtext, time=60*60*24*7)
    return result

def view_redis_ptt(data, inputtext, result):
    for d in data:
      item = {}
      item["url"] = d[0]
      item["title"] = d[1]
      item["text"] = d[2]
      result["data"].append(item)
      r.rpush("Ptt-"+inputtext,json.dumps(item))
    r.expire("Ptt-"+inputtext, time=60*60*24*7)
    return result

def view_redis_search(data, inputtext, result):
    for d in data:
      item = {}
      item["url"] = d[0]
      item["title"] = d[1]
      item["text"] = d[2]
      result["data"].append(item)
      r.rpush("Search-"+inputtext,json.dumps(item))
    r.expire("Search-"+inputtext, time=60*60*24*7)
    return result

def view_redis_dcard(data, inputtext, result):
    for d in data:
      item = {}
      item["url"] = d[0]
      item["title"] = d[1]
      item["text"] = d[2]
      result["data"].append(item)
      r.rpush("Dcard-"+inputtext,json.dumps(item))
    r.expire("Dcard-"+inputtext, time=60*60*24*7)
    return result

def view_redis_blog(data, inputtext, result):
    for d in data:
      item = {}
      item["url"] = d[0]
      item["title"] = d[1]
      item["text"] = d[2]
      result["data"].append(item)
      r.rpush("Blog-"+inputtext,json.dumps(item))
    r.expire("Blog-"+inputtext, time=60*60*24*7)
    return result

def view_redis_thank(data,inputtext):
    result = {}
    result["data"] = []
    for d in data:
        res = es.search(index='thankurl', query={
            "match_phrase": {
                "month": d['_source']['month']
            }
        })

        item = {}
        item["url"] = res['hits']['hits'][0]['_source']['url']
        item["title"] = d['_source']['target']
        item["text"] = d['_source']['content']
        item["when"] = d['_source']['month']
        result["data"].append(item)
        r.rpush("Thank-"+inputtext,json.dumps(item))
    r.expire("Thank-"+inputtext, time=60*60*24*7)
    return result

def view_setitem_review(location,author,review_rating,review_until,review,review_link):
    item = {}
    item["location"] = location
    item["name"] = author
    item["star"] = review_rating
    item["when"] = review_until
    item["review"] = review
    item["link"] = review_link
    return item

def view_setitem_business(author,timestamp,comment,link,location):
    item = {}
    item["name"] = author
    item["posttime"] = untilNow(timestamp)
    item["comment"] = comment
    item["link"] = link
    item["location"] = location
    return item

def view_setitem_judgment(link, title):
    item = {}
    item["url"] = link
    item["title"] = title
    return item

def view_setitem_ptt(link,title,text):
    item = {}
    item["url"] = link
    item["title"] = title
    item["text"] = text
    return item

def view_setitem_search(link, title, text):
    item = {}
    item["url"] = link
    item["title"] = title
    item["text"] = text
    return item

def view_setitem_dcard(link,title,text):
    item = {}
    item["url"] = link
    item["title"] = title
    item["text"] = text
    return item

def view_setitem_blog(link,title,text):
    item = {}
    item["url"] = link
    item["title"] = title
    item["text"] = text
    return item

def view_redis_doctor(data):
    result = {}
    for d in data:
        if d[0] not in result:
            result[d[0]] = []
        result[d[0]].append(d[1])
    r.set("doctorlist", json.dumps(result))
    return result