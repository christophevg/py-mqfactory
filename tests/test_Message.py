from mqfactory.message import Message

def test_message_as_dictionary(message):
  assert dict(message) == {
    "to"      : message.to,
    "payload" : message.payload,
    "tags"    : message.tags
  }

def test_ensure_default_id_generation():
  message = Message("to", "payload")
  assert not message.id is None

def test_ensure_id_is_available(message):
  assert "id" in message.tags
  assert message.id == message.tags["id"]

def test_copy_is_correct_and_not_same_object(message):
  dup = message.copy()
  assert dup != message
  assert dict(dup) == dict(message)

def test_string_representation(message):
  assert str(message) == str({
    "to"     : message.to,
    "payload": message.payload,
    "tags"   : message.tags
  })