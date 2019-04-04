import copy
import logging

from pymongo import MongoClient
from bson.objectid import ObjectId 

from mqfactory.store import Store, Collection

class MongoStore(Store):
  def __init__(self, uri=None, client=None, database=None, timeout=5000):
    assert not uri is None or (not client is None and not database is None),\
           "Please provide a uri or client and database."
    self.client = client
    if self.client is None: self.create_client(uri, timeout=timeout)
    database = database or uri.split("/")[-1]
    self.database = self.client[database]

  def create_client(self, uri=None, timeout=5000):
    self.client = MongoClient(uri, serverSelectionTimeoutMS=timeout)
    self.client.admin.command("ismaster")
  
  def __getitem__(self, collection):
    return MongoCollection(self.database[collection])


class MongoCollection(Collection):
  def __init__(self, collection):
    self.collection = collection

  def load(self):
    docs = []
    for doc in self.collection.find():
      doc["_id"] = str(doc["_id"])
      docs.append(doc)
    return docs

  def __getitem__(self, id):
    try:
      id = ObjectId(id)
    except:
      pass
    return self.collection.find_one({"_id": id})
  
  def add(self, doc):
    logging.debug("adding to collection...")
    id = str(self.collection.insert_one(doc).inserted_id)
    logging.debug("added as {0}".format(id))
    return id

  def remove(self, id):
    try:
      id = ObjectId(id)
    except:
      pass
    self.collection.delete_one({"_id" : id})

  def update(self, id, doc):
    updated_doc = copy.deepcopy(doc)
    try:
      id = ObjectId(id)
      updated_doc["_id"] = ObjectId(updated_doc["_id"])
    except:
      pass
    self.collection.update_one({"_id" : id}, {"$set" : updated_doc})
