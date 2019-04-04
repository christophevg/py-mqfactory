import copy
import mongomock
import timeout_decorator

from mqfactory.message     import Message
from mqfactory.Queue       import Queue
from mqfactory.store       import MessageStore
from mqfactory.store.mongo import MongoCollection

@timeout_decorator.timeout(2, use_signals=False)
def test_reentrant_access_of_add_due_to_lazy_loading():
  queue = Queue()
  mongo = mongomock.MongoClient().db
  docs = [
    { "to": "someone", "payload" : "test 1", "tags" : {} },
  ]
  mongo.col.insert_many(copy.deepcopy(docs))
  collection = MongoCollection(mongo["col"])

  ms = MessageStore(queue, collection)
  
  queue.add(Message("to",  "payload"))
