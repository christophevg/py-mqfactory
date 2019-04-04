import copy
import mongomock
import pytest
import pymongo
from bson.objectid import ObjectId 

from mqfactory.store.mongo import MongoStore, MongoCollection

def test_invalid_setup_parameters():
  with pytest.raises(AssertionError):
    mongo = MongoStore(timeout=100)
  with pytest.raises(AssertionError):
    mongo = MongoStore(client=True, timeout=100)

def test_unavailable_mongo_database():
  with pytest.raises(pymongo.errors.ServerSelectionTimeoutError):
    mongo = MongoStore("mongodb://dummy:27017/blah", timeout=100)

def test_get_collection():
  mongo = mongomock.MongoClient()
  store = MongoStore(client=mongo, database="db")
  assert store["col"].collection == mongo["db"]["col"]

def test_adding_documents():
  mongo = mongomock.MongoClient().db
  col = MongoCollection(mongo["col"])

  col.add({ "doc" : "test 1" })
  col.add({ "doc" : "test 2" })
  assert mongo.col.count_documents({}) == 2
  doc = mongo.col.find_one({"doc" : "test 1"}, {"_id": False})
  assert doc == {"doc" : "test 1"}
  doc = mongo.col.find_one({"doc" : "test 2"}, {"_id": False})
  assert doc == {"doc" : "test 2"}

def test_loading_documents():
  mongo = mongomock.MongoClient().db
  docs = [
    { "doc" : "test 1" },
    { "doc" : "test 2" }
  ]
  mongo.col.insert_many(copy.deepcopy(docs))
  col = MongoCollection(mongo["col"])

  loaded_docs = col.load()
  assert len(loaded_docs) == 2
  for doc in loaded_docs:
    del doc["_id"]
  assert loaded_docs == docs

def test_getting_documents():
  mongo = mongomock.MongoClient().db
  docs = [
    { "doc" : "test 1" },
    { "doc" : "test 2" },
    { "doc" : "test 3", "_id" : "id3" }
  ]
  mongo.col.insert_many(copy.deepcopy(docs))
  col = MongoCollection(mongo["col"])
  doc = mongo.col.find_one({"doc": "test 2"})
  assert col[doc["_id"]]["doc"] == "test 2"
  assert col[str(doc["_id"])]["doc"] == "test 2"
  assert col["id3"]["doc"] == "test 3"

def test_removing_documents():
  mongo = mongomock.MongoClient().db
  docs = [
    { "doc" : "test 1" },
    { "doc" : "test 2" },
    { "doc" : "test 3", "_id" : "id3" }
  ]
  mongo.col.insert_many(copy.deepcopy(docs))
  col = MongoCollection(mongo["col"])

  loaded_docs = col.load()
  col.remove(loaded_docs[1]["_id"])

  assert mongo.col.count_documents({}) == 2
  doc = mongo.col.find_one({"doc" : "test 1"}, {"_id": False})
  assert doc == {"doc" : "test 1"}
  doc = mongo.col.find_one({"doc" : "test 3"}, {"_id": False})
  assert doc == {"doc" : "test 3"}

  col.remove("id3")
  assert mongo.col.count_documents({}) == 1

def test_updating_documents():
  mongo = mongomock.MongoClient().db
  docs = [
    { "doc" : "test 1" },
    { "doc" : "test 2" },
    { "doc" : "test 3", "_id" : "id3" }
  ]
  mongo.col.insert_many(copy.deepcopy(docs))
  col = MongoCollection(mongo["col"])

  loaded_docs = col.load()
  doc = loaded_docs[1]
  doc["more"] = True
  col.update(doc["_id"], doc)

  assert mongo.col.count_documents({}) == 3
  doc = mongo.col.find_one({"doc" : "test 1"}, {"_id": False})
  assert doc == {"doc" : "test 1"}
  doc = mongo.col.find_one({"doc" : "test 2"}, {"_id": False})
  assert doc == {"doc" : "test 2", "more" : True}
  doc = mongo.col.find_one({"doc" : "test 3"}, {"_id": False})
  assert doc == {"doc" : "test 3"}

  col.update("id3", {"doc" : "something else"})
  doc = mongo.col.find_one({"_id" : "id3"}, {"_id": False})
  assert doc == {"doc" : "something else"}
