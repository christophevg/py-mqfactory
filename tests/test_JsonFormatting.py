import json

from mqfactory                   import MessageQueue
from mqfactory.message.format.js import serialize, unserialize, JsonFormatting

from . import TransportMock

def test_serialize(message):
  message.payload = { "data" : message.payload }
  initial_payload = message.payload
  serialize(message)
  assert message.payload == json.dumps({
    "tags" : {},
    "payload" : initial_payload
  }, sort_keys=True)

def test_unserialize(message):
  initial_payload = message.payload
  message.payload = json.dumps({
    "tags": {},
    "payload" : initial_payload
  }, sort_keys=True)
  unserialize(message)
  assert message.payload == initial_payload
  assert message.tags    == {}

def test_json_formatting_installer(transport, message):
  mq = MessageQueue(transport)
  JsonFormatting(mq)
  mq.send(message.to, message.payload)
  mq.process_outbox()
  assert len(transport.items) == 1
  assert transport.items[0].to == message.to
  assert transport.items[0].payload == json.dumps({
    "tags"   : message.tags,
    "payload": message.payload
  }, sort_keys=True)
