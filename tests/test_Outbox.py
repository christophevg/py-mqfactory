import pytest

from mqfactory.message import Message
from mqfactory.Outbox import Outbox

def test_adding_messages_with_last_timestamp(clock):
  outbox = Outbox(clock=clock)
  messages = [
    Message("1", "1", id=1),
    Message("2", "2", id=2),
    Message("3", "3", id=3)
  ]
  outbox.add(messages[0])
  outbox.add(messages[1])
  outbox.add(messages[2])
  
  assert messages[0].tags["last"] == 1
  assert messages[1].tags["last"] == 2
  assert messages[2].tags["last"] == 3

def test_removing_messages(clock):
  outbox = Outbox(clock=clock)
  messages = [
    Message("1", "1", id=1),
    Message("2", "2", id=2),
    Message("3", "3", id=3)
  ]
  outbox.add(messages[0])
  outbox.add(messages[1])
  outbox.add(messages[2])
  
  assert outbox.remove(messages[1]) == messages[1]
  with pytest.raises(KeyError):
    outbox.remove(messages[1])

def test_deferring_messages(clock):
  outbox = Outbox(clock=clock)
  messages = [
    Message("1", "1", id=1),
    Message("2", "2", id=2),
    Message("3", "3", id=3)
  ]
  outbox.add(messages[0])
  outbox.add(messages[1])
  outbox.add(messages[2])

  outbox.defer(messages[1])
  outbox.defer(messages[0])

  assert messages[0].tags["last"] == 5
  assert messages[1].tags["last"] == 4
  assert messages[2].tags["last"] == 3

def test_len():
  outbox = Outbox()
  messages = [
    Message("1", "1", id=1),
    Message("2", "2", id=2),
    Message("3", "3", id=3),
    Message("4", "4", id=4)
  ]
  outbox.add(messages[0])
  outbox.add(messages[1])
  outbox.add(messages[2])
  assert len(outbox) == 3

  outbox.add(messages[3])
  assert len(outbox) == 4

  outbox.remove(messages[1])
  outbox.remove(messages[2])
  assert len(outbox) == 2

def test_getitem():
  outbox = Outbox()
  messages = [
    Message("1", "1", id=1),
    Message("2", "2", id=2),
    Message("3", "3", id=3),
    Message("4", "4", id=4)
  ]
  outbox.add(messages[0])
  outbox.add(messages[1])
  outbox.add(messages[2])

  assert outbox[1] == messages[0]
  with pytest.raises(KeyError):
    outbox["abc"]

def test_next(clock):
  outbox = Outbox(clock=clock)
  messages = [
    Message("1", "1", id=1),
    Message("2", "2", id=2),
    Message("3", "3", id=3)
  ]
  
  with pytest.raises(StopIteration):
    next(outbox)
  
  outbox.add(messages[0])
  outbox.add(messages[1])
  outbox.add(messages[2])
  
  assert next(outbox) == messages[0]

  outbox.defer(messages[0])
  assert next(outbox) == messages[1]

  outbox.defer(messages[2])
  outbox.defer(messages[1])
  assert next(outbox) == messages[0]


def test_aspects():
  tracked = []
  def track(aspect):
    def tracker(_, message=None):
      tracked.append( (aspect, message) )
    return tracker

  outbox = Outbox()
  outbox.before_add.append(track("before_add"))
  outbox.after_add.append(track("after_add"))
  outbox.before_remove.append(track("before_remove"))
  outbox.after_remove.append(track("after_remove"))
  outbox.before_defer.append(track("before_defer"))
  outbox.after_defer.append(track("after_defer"))
  outbox.before_get.append(track("before_get"))
  
  messages = [
    Message("1", "1", id=1),
    Message("2", "2", id=2),
    Message("3", "3", id=3)
  ]
  outbox.add(messages[0])
  outbox.add(messages[1])
  outbox.remove(messages[0])
  outbox[2]
  outbox.add(messages[2])
  outbox.defer(messages[1])
  outbox.remove(messages[2])
  next(outbox)

  assert tracked == [
    ("before_add",    messages[0]),
    ("after_add",     messages[0]),
    ("before_add",    messages[1]),
    ("after_add",     messages[1]),
    ("before_remove", messages[0]),
    ("after_remove",  messages[0]),
    ("before_get",    messages[1]),
    ("before_add",    messages[2]),
    ("after_add",     messages[2]),
    ("before_defer",  messages[1]),
    ("after_defer",   messages[1]),
    ("before_remove", messages[2]),
    ("after_remove",  messages[2]),    
    ("before_get",    None)
  ]
