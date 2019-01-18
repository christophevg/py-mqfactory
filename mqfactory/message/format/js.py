import json

def serialize(msg):
  msg.payload = json.dumps({
    "tags"   : msg.tags,
    "payload": msg.payload
  })

def unserialize(msg):
  raw = json.loads(msg.payload)
  msg.tags    = raw["tags"]
  msg.payload = raw["payload"]


def JsonFormatting(mq):
  mq.before_sending.append(serialize)
  mq.after_receiving.append(unserialize)
  return mq
