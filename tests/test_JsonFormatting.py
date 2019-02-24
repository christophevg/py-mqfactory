import json

from mqfactory                   import MessageQueue
from mqfactory.message.format.js import serialize, unserialize, JsonFormatting

def test_serialize(message):
  message.payload = { "data" : message.payload }
  initial_payload = message.payload
  serialize(message)
  assert message.payload == json.dumps({
    "tags" : { "id" : message.id },
    "payload" : initial_payload
  }, sort_keys=True)

def test_unserialize(message):
  initial_payload = message.payload
  message.payload = json.dumps({
    "tags": { "id" : message.id },
    "payload" : initial_payload
  }, sort_keys=True)
  unserialize(message)
  assert message.payload == initial_payload
  assert message.tags    == { "id": message.id }

def test_json_formatting_installer(mq):
  JsonFormatting(mq)
  mq.transport.before_sending.append.assert_called()
  mq.transport.after_receiving.append.assert_called()
