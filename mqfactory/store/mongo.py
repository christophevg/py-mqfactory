from pymongo import MongoClient

from mqfactory.store import Store, Collection

class MongoStore(Store):
  def __init__(self, uri=None, client=None, database=None, timeout=5000):
    assert not uri is None or (not client is None and not database is None),\
           "Please provide a uri or client and database."
    self.client = client or self.create_client(uri, timeout=timeout)
    database = database or uri.split("/")[-1]
    self.database = self.client[database]

  def create_client(self, uri=None, timeout=5000):
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
    return self.collection.insert_one(doc).inserted_id

  def remove(self, id):
    self.collection.delete_one({"_id" : id})

  def update(self, id, doc):
    self.collection.replace_one({"_id" : id}, doc)
