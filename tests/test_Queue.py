import pytest
from mock import patch

from time import time

from mqfactory.message import Message
from mqfactory.Queue   import Queue

@patch("mqfactory.tools.clock.now")
def test_adding_messages_with_last_timestamp(mocked_time):
  mocked_time.side_effect = range(1, 4)

  queue = Queue()
  messages = [
    Message("1", "1", id=1),
    Message("2", "2", id=2),
    Message("3", "3", id=3)
  ]
  queue.add(messages[0])
  queue.add(messages[1])
  queue.add(messages[2])
  
  assert messages[0].private["last"] == 1
  assert messages[1].private["last"] == 2
  assert messages[2].private["last"] == 3

@patch("mqfactory.tools.clock.now")
def test_removing_messages(mocked_time):
  mocked_time.side_effect = range(1, 4)

  queue = Queue()
  messages = [
    Message("1", "1", id=1),
    Message("2", "2", id=2),
    Message("3", "3", id=3)
  ]
  queue.add(messages[0])
  queue.add(messages[1])
  queue.add(messages[2])

  queue.remove(messages[0])
  with pytest.raises(KeyError):
    queue.remove(messages[0])

  queue.remove(messages[1])
  with pytest.raises(KeyError):
    queue.remove(messages[1])

  queue.remove(messages[2])
  with pytest.raises(KeyError):
    queue.remove(messages[2])

@patch("mqfactory.tools.clock.now")
def test_deferring_messages(mocked_time):
  mocked_time.side_effect = range(1, 6)

  queue = Queue()
  messages = [
    Message("1", "1", id=1),
    Message("2", "2", id=2),
    Message("3", "3", id=3)
  ]
  queue.add(messages[0])
  queue.add(messages[1])
  queue.add(messages[2])

  queue.defer(messages[1])
  queue.defer(messages[0])

  assert messages[0].private["last"] == 5
  assert messages[1].private["last"] == 4
  assert messages[2].private["last"] == 3

def test_len():
  queue = Queue()
  messages = [
    Message("1", "1", id=1),
    Message("2", "2", id=2),
    Message("3", "3", id=3),
    Message("4", "4", id=4)
  ]
  queue.add(messages[0])
  queue.add(messages[1])
  queue.add(messages[2])
  assert len(queue) == 3

  queue.add(messages[3])
  assert len(queue) == 4

  queue.remove(messages[1])
  queue.remove(messages[2])
  assert len(queue) == 2

def test_getitem():
  queue = Queue()
  messages = [
    Message("1", "1", id=1),
    Message("2", "2", id=2),
    Message("3", "3", id=3),
    Message("4", "4", id=4)
  ]
  queue.add(messages[0])
  queue.add(messages[1])
  queue.add(messages[2])

  assert queue[1] == messages[0]
  with pytest.raises(KeyError):
    queue["abc"]

@patch("mqfactory.tools.clock.now")
def test_next(mocked_time):
  mocked_time.side_effect = range(1, 7)

  queue = Queue()
  messages = [
    Message("1", "1", id=1),
    Message("2", "2", id=2),
    Message("3", "3", id=3)
  ]

  with pytest.raises(StopIteration):
    next(queue)

  queue.add(messages[0])
  queue.add(messages[1])
  queue.add(messages[2])

  assert next(queue) == messages[0]

  queue.defer(messages[0])
  assert next(queue) == messages[1]

  queue.defer(messages[2])
  queue.defer(messages[1])
  assert next(queue) == messages[0]


def test_aspects():
  tracked = []
  def track(aspect):
    def tracker(message=None):
      tracked.append( (aspect, message) )
    return tracker

  queue = Queue()
  queue.before_add.append(track("before_add"))
  queue.after_add.append(track("after_add"))
  queue.before_remove.append(track("before_remove"))
  queue.after_remove.append(track("after_remove"))
  queue.before_defer.append(track("before_defer"))
  queue.after_defer.append(track("after_defer"))
  queue.before_get.append(track("before_get"))

  messages = [
    Message("1", "1", id=1),
    Message("2", "2", id=2),
    Message("3", "3", id=3)
  ]

  queue.add(messages[0])
  assert tracked == [
    ("before_add",    messages[0]),
    ("after_add",     messages[0])
  ]

  queue.add(messages[1])
  assert tracked[2:] == [
    ("before_add",    messages[1]),
    ("after_add",     messages[1])
  ]

  queue.remove(messages[0])
  assert tracked[4:] == [
    ("before_remove", messages[0]),
    ("after_remove",  messages[0])
  ]

  queue[2]
  assert tracked[6:] == [
    ("before_get",    messages[1])
  ]

  queue.add(messages[2])
  assert tracked[7:] == [
    ("before_add",    messages[2]),
    ("after_add",     messages[2])
  ]

  queue.defer(messages[1])
  assert tracked[9:] == [
    ("before_defer",  messages[1]),
    ("after_defer",   messages[1])
  ]

  queue.remove(messages[2])
  assert tracked[11:] == [
    ("before_remove", messages[2]),
    ("after_remove",  messages[2])
  ]

  next(queue)
  assert tracked[13:] == [
    ("before_get",    None)
  ]
