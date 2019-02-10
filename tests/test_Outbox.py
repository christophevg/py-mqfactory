from mqfactory.Outbox import Outbox

def test_append_and_pop():
  tracker = []
  def track_append(outbox):
    tracker.append(outbox.messages[-1])

  def track_pop(outbox, index, item):
    tracked_item = tracker.pop(index)
    assert item == tracked_item

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
