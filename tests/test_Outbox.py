from mqfactory.Outbox import Outbox

def test_append_and_pop():
  tracker = []
  def track_append(outbox, item):
    tracker.append(item)
    return item

  def track_pop(outbox, index, item):
    tracked_item = tracker.pop(index)
    assert item == tracked_item
    return (index, item)

  outbox = Outbox()
  outbox.after_append.append(track_append)
  outbox.after_pop.append(track_pop)
  
  outbox.append("1")
  outbox.append("2")
  outbox.append("3")
  assert tracker == ["1", "2", "3"]

  item = outbox.pop()
  assert item == "1"
  assert tracker == ["2", "3"]

  item = outbox.pop(1)
  assert item == "3"
  assert tracker == ["2"]

def test_setitem():
  sets = []
  def track_setitem(outbox, index, old, new):
    sets.append((index, old, new))
    return (index, old, new)
  
  outbox = Outbox()
  outbox.after_setitem.append(track_setitem)

  outbox.append("1")
  outbox.append("2")
  outbox.append("3")
  outbox[1] = "B"
  outbox[0] = "A"
  assert sets == [(1, "2", "B"), (0, "1", "A")]

def test_getitem():
  gets = []
  def track_getitem(outbox, index):
    gets.append(index)
    return index

  outbox = Outbox()
  outbox.before_getitem.append(track_getitem)
  
  outbox.append("1")
  outbox.append("2")
  outbox.append("3")

  assert outbox[1] == "2"
  assert outbox[0] == "1"
  assert outbox[2] == "3"
  
  assert gets == [1, 0, 2]
