from mqfactory import Message

def test_message_as_dictionary(message):
  msg = Message(message.to, message.payload)
  assert dict(msg) == { "to" : message.to, "payload" : message.payload }
