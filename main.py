from elasticsearch import Elasticsearch
es = Elasticsearch("http://localhost:9200/")

# print(es)

INDEX_NAME = "megacorp"

# # create/update
res = es.index(index=INDEX_NAME, id=5, document={
    "first_name": "王望明同學",
    "last_name": "panwar",
    "age": 37,
    "about": "Love and Peace",
    "interests": ['drama', 'music'],
})
# # print(res)

e4 = {
    "first_name":  "希望明天會更好",
    "last_name":   "Smith",
    "age":         32,
    "about":       "I like to collect rock albums",
    "interests":  ["music"]
}
res = es.index(index='megacorp', id=4, document=e4)

# # delete
# # res = es.delete(index='megacorp', id="Pgy__IsBgtVnwoNrFTPT")
# # print(res['result'])

# # create
# res = es.index(index='megacorp', id=2, document=e2)
# # print(res)
# # print(res['result'])

# # read
# res = es.get(index=INDEX_NAME, id=1)
# # print(res)

# res = es.search(index='megacorp', query={"match_all": {}})
# print(res['hits'])

# res = es.search(index='megacorp', query={'match': {'first_name': 'nitin'}})
# # print(res['hits']['hits'])

# res = es.search(index='megacorp', query={
#     "bool": {
#         "must": [
#             {
#                 "match": {
#                       "first_name": "nitin"
#                 }
#             }
#         ],
#         "should": [
#             {
#                 "range": {
#                     "age": {
#                         "gte": 10
#                     }
#                 }
#             }
#         ]
#     }
# })


res = es.search(index='megacorp', query={
    "match": {
                      "first_name": "望明"
    }
})
print(res['hits']['hits'])


# doc = {
#     'author': 'kimchy',
#     'text': 'Elasticsearch: cool. bonsai cool.',
#     'timestamp': datetime.now(),
# }
# resp = es.index(index="test-index", id=1, document=doc)
# # print(resp['result'])

# resp = es.get(index="test-index", id=1)
# # print(resp['_source'])

# es.indices.refresh(index="test-index")

# resp = es.search(index="test-index", query={"match_all": {}})
# # print("Got %d Hits:" % resp['hits']['total']['value'])
# for hit in resp['hits']['hits']:
#     print("%(timestamp)s %(author)s: %(text)s" % hit["_source"])
