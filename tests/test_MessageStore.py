import pytest

from mqfactory import MessageQueue

from mqfactory.store import Persisting

def test_store_actions(collection, transport, ids, ticks):
  mq = Persisting(
         MessageQueue(transport, ids=ids, ticks=ticks),
         into=collection
       )
  mq.send("to 1", "load 1")
  mq.send("to 2", "load 2")
  mq.process_entire_outbox()

  assert len(collection.changelog) == 5
  assert collection.changelog == [
    "load",
    ("add",    "1", {"to": "to 1", "payload" : "load 1", "tags" : { "id" : 1, "last": 1 }}),
    ("add",    "2", {"to": "to 2", "payload" : "load 2", "tags" : { "id" : 2, "last": 2 }}),
    ("remove", "1"),
    ("remove", "2")
  ]

def test_loading_of_stored_messages_before_append(collection, transport, message):
  mq = Persisting(
         MessageQueue(transport),
         into=collection
       )
  mq.outbox.add(message)
  assert len(collection.changelog) == 2
  assert collection.changelog[0] == "load"

def test_loading_of_stored_messages_before_pop(collection, transport, message):
  mq = Persisting(
         MessageQueue(transport),
         into=collection
       )
  with pytest.raises(KeyError):
    mq.outbox.remove(message)
  assert len(collection.changelog) == 1
  assert collection.changelog[0] == "load"

def test_loading_of_stored_messages_before_next(collection, transport):
  mq = Persisting(
         MessageQueue(transport),
         into=collection
       )
  with pytest.raises(StopIteration):
    next(mq.outbox)
  assert len(collection.changelog) == 1
  assert collection.changelog[0] == "load"
