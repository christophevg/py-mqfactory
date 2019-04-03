import pytest

from mock import Mock, MagicMock, create_autospec

import random
import string
import copy
import logging

from mqfactory                      import MessageQueue, Queue
from mqfactory.message              import Message
from mqfactory.transport            import Transport
from mqfactory.store                import Collection
from mqfactory.message.security     import Signature
from mqfactory.message.security.rsa import generate_key_pair, encode

def generate_random_string(length=10):
  return ''.join(random.choice(string.ascii_lowercase) for _ in range(length))

@pytest.fixture
def message():
  to      = generate_random_string()
  payload = generate_random_string()
  tags    = {}
  id      = generate_random_string()
  return Message(to, payload, tags, id)

@pytest.fixture
def transport():
   transport = create_autospec(Transport)()
   attrs = { "before_sending" : Mock(), "after_receiving" : Mock() }
   transport.configure_mock(**attrs)
   return transport

def make_queue_mock():
  queue = create_autospec(Queue)()
  attrs = {
    "messages" : MagicMock(),
    "before_add" : Mock(),
    "after_add" : Mock(),
    "before_remove" : Mock(),
    "after_remove": Mock(),
    "before_defer"  : Mock(),
    "after_defer" : Mock(),
    "before_get"  : Mock(),
    "after_get" : Mock()   
  }
  queue.configure_mock(**attrs)
  return queue

@pytest.fixture
def queue():
  return make_queue_mock()

@pytest.fixture
def queue_builder():
  return make_queue_mock

@pytest.fixture
def mq(transport, queue_builder):
  mq = create_autospec(MessageQueue)
  attrs = {
    "name" : "test",
    "transport" : transport,
    "inbox": queue_builder(),
    "outbox": queue_builder(),
    "before_sending": Mock(),
    "after_sending": Mock(),
    "before_handling": Mock(),
    "after_handling": Mock()
  }
  mq.configure_mock(**attrs)
  return mq

def make_collection_mock():
  collection = create_autospec(Collection)
  add_method = Mock()
  add_method.side_effect = range(1, 10000)
  attrs = { "add" : add_method }
  collection.configure_mock(**attrs)
  return collection

@pytest.fixture
def collection():
  return make_collection_mock()

@pytest.fixture
def inbox():
  return make_collection_mock()

@pytest.fixture
def outbox():
  return make_collection_mock()

@pytest.fixture
def signature():
  s = create_autospec(Signature)
  return s

@pytest.fixture
def me():
  return generate_random_string()

@pytest.fixture
def keys(me, collection):
  private, public = generate_key_pair()
  return {
    me : { "private" : encode(private), "public" : encode(public) }
  }

@pytest.fixture
def paho():
  return Mock()

@pytest.fixture
def paho_message(message):
  msg = Mock()
  attrs = { "topic" : message.to, "payload": message.payload }
  msg.configure_mock(**attrs)
  return msg
