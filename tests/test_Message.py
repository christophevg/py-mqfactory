from mqfactory.message import Message

def test_ensure_default_id_generation():
  message = Message("to", "payload")
  assert not message.id is None

def test_ensure_id_property_exposes_tagged_id():
  message = Message("to", "payload", id="some id")
  assert message.id == "some id"

def test_copy_is_correct_and_not_same_object(message):
  dup = message.copy()
  assert not dup is message
  assert dup.to == message.to
  assert dup.payload == message.payload
  assert dup.tags == message.tags

def test_message_as_dictionary(message):
  assert dict(message) == {
    "to"      : message.to,
    "payload" : message.payload,
    "tags"    : message.tags
  }

def test_string_representation(message):
  assert str(message) == str({
    "to"     : message.to,
    "payload": message.payload,
    "tags"   : message.tags
  })

def test_message_comparison(message):
  message2 = Message(message.to, message.payload, message.tags, message.id)
  assert message == message2
  assert not message != message2
