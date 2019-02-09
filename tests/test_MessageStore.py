import pytest

from mqfactory import MessageQueue

from mqfactory.store import Persisting

def test_store_actions(collection, transport):
  mq = Persisting(
         MessageQueue(transport),
         into=collection
       )
  mq.send("to 1", "payload 1")
  mq.send("to 2", "payload 2")
  mq.process_entire_outbox()

  assert len(collection.changelog) == 5
  assert collection.changelog == [
    "load",
    ("add",    "1", {"to": "to 1", "payload" : "payload 1"}),
    ("add",    "2", {"to": "to 2", "payload" : "payload 2"}),
    ("remove", "1"),
    ("remove", "2")
  ]

def test_loading_of_stored_messages_before_append(collection, transport, message):
  mq = Persisting(
         MessageQueue(transport),
         into=collection
       )
  mq.outbox.append(message)
  assert len(collection.changelog) == 2
  assert collection.changelog[0] == "load"

def test_loading_of_stored_messages_before_pop(collection, transport, message):
  mq = Persisting(
         MessageQueue(transport),
         into=collection
       )
  with pytest.raises(IndexError):
    mq.outbox.pop(0)
  assert len(collection.changelog) == 1
  assert collection.changelog[0] == "load"

def test_loading_of_stored_messages_before_next(collection, transport, message):
  mq = Persisting(
         MessageQueue(transport),
         into=collection
       )
  with pytest.raises(StopIteration):
    next(mq.outbox)
  assert len(collection.changelog) == 1
  assert collection.changelog[0] == "load"
