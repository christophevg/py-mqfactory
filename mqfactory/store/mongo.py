from pymongo import MongoClient

from mqfactory.store import Store, Collection

class MongoStore(Store):
  def __init__(self, uri=None, client=None, database=None, timeout=None):
    assert not uri is None or (not client is None and not database is None),\
           "Please provide a uri or client and database."
    self.client = client or self.create_client(uri, timeout=timeout)
    database = database or uri.split("/")[-1]
    self.database = self.client[database]

  def create_client(self, uri=None, timeout=None):
    mongo = MongoClient(uri, serverSelectionTimeoutMS=timeout)
    mongo.admin.command("ismaster")
    return mongo
  
  def __getitem__(self, collection):
    return MongoCollection(self.database[collection])


class MongoCollection(Collection):
  def __init__(self, collection):
    self.collection = collection

  def load(self):
    return [ doc for doc in self.collection.find() ]
  
  def add(self, doc):
    self.collection.insert_one(doc)

  def remove(self, doc):
    self.collection.delete_one({"_id" : doc["_id"]})

  def update(self, doc):
    self.collection.replace_one({"_id" : doc["_id"]}, doc)
