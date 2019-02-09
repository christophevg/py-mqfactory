import json

from mqfactory.message import Message

def serialize(msg):
  msg.payload = json.dumps({
    "tags"   : msg.tags,
    "payload": msg.payload
  }, sort_keys=True)

def unserialize(msg):
  raw = json.loads(msg.payload)
  msg.tags    = raw["tags"]    if "tags" in raw else {}
  msg.payload = raw["payload"] if "payload" in raw else ""

def JsonFormatting(mq):
  mq.transport.before_sending.append(serialize)
  mq.transport.after_receiving.append(unserialize)
  return mq
