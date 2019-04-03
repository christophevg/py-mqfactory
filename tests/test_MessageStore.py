import pytest
from mock import patch, call

import time
import uuid

from mqfactory         import MessageQueue
from mqfactory.message import Message

from mqfactory.store   import MessageStore
from mqfactory.store   import Persisting

@patch("uuid.uuid4")
@patch("mqfactory.tools.clock.now")
def test_store_actions(mocked_time, mocked_uuid, transport, collection):
  mocked_time.side_effect = range(1, 5)
  mocked_uuid.side_effect = range(1, 3)

  mq = Persisting( MessageQueue(transport), outbox=collection )
  mq.send("to 1", "load 1")

  assert collection.mock_calls[0] == call.load()
  collection.add.assert_called_with({
    "to": "to 1", "payload" : "load 1", "tags" : { "id" : "1" }
  })
  
  mq.send("to 2", "load 2")
  collection.add.assert_called_with({
    "to": "to 2", "payload" : "load 2", "tags" : { "id" : "2" }
  })
  
  mq.process_outbox()
  collection.remove.assert_called_with(1)
  
  mq.process_outbox()
  collection.remove.assert_called_with(2)

def test_loading_of_stored_messages_before_append(collection, transport, message):
  mq = Persisting( MessageQueue(transport), outbox=collection )
  mq.outbox.add(message)
  assert collection.mock_calls[0] == call.load()

def test_loading_of_stored_messages_before_pop(collection, transport, message):
  mq = Persisting( MessageQueue(transport), outbox=collection )
  with pytest.raises(KeyError):
    mq.outbox.remove(message)
  assert collection.mock_calls[0] == call.load()

def test_loading_of_stored_messages_before_next(collection, transport):
  mq = Persisting( MessageQueue(transport), outbox=collection )
  with pytest.raises(StopIteration):
    next(mq.outbox)
  assert collection.mock_calls[0] == call.load()

@patch("uuid.uuid4")
def test_loading_of_messages(mocked_uuid, queue, collection):
  mocked_uuid.side_effect = range(1, 3)

  ms = MessageStore(queue, collection)
  collection.load.return_value = [
    { "_id" : 1, "to" : "to 1", "payload": "load 1", "tags": { "tag" : "value"}}
  ]
  ms.load_messages()
  expected = Message("to 1", "load 1", { "tag" : "value" }, id="1")
  expected.private["store-id"] = 1
  queue.add.assert_called_with(expected, wrapping=False)

def test_defer(queue, collection, message):
  ms = MessageStore(queue, collection)
  message.private["store-id"] = 1
  ms.after_defer(message)
  collection.update.assert_called_with(1, dict(message))

# TODO test all aspects in the same way, with less dependencies on MQ

@patch("mqfactory.store.logging")
def test_defer_exception_logging(mocked_logging, queue, collection, message):
  ms = MessageStore(queue, collection)
  ms.after_defer(message)
  collection.update.assert_not_called()
  assert mocked_logging.error.called
