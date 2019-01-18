import json

from mqfactory                   import MessageQueue
from mqfactory.message.format.js import serialize, unserialize, JsonFormatting

from . import TransportMock

def test_serialize(message):
  initial_payload = message.payload
  serialize(message)
  assert message.payload == json.dumps({
    "tags" : {},
    "payload" : initial_payload
  })

def test_unserialize(message):
  initial_payload = message.payload
  message.payload = json.dumps({
    "tags": {},
    "payload" : initial_payload
  })
  unserialize(message)
  assert message.payload == initial_payload
  assert message.tags    == {}

def test_json_formatting_installer():
  mq = MessageQueue(TransportMock())
  JsonFormatting(mq)
  assert len(mq.before_sending) == 1
  assert mq.before_sending[0] == serialize
  assert len(mq.after_receiving) == 1
  assert mq.after_receiving[0] == unserialize
