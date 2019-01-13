from mqfactory import MessageQueue

from mqfactory.store import Persisting

from . import TransportMock, StoreMock

def test_store_actions():
  store = StoreMock({"collection": [] })
  mq = Persisting(
         MessageQueue(TransportMock()),
         into=store["collection"]
       )
  mq.send("to 1", "payload 1")
  mq.send("to 2", "payload 2")
  mq.process_outbox()

  assert store["collection"].changelog == [
    "load",
    ("add",    ("to 1", "payload 1")),
    ("add",    ("to 2", "payload 2")),
    ("remove", ("to 1", "payload 1")),
    ("remove", ("to 2", "payload 2"))    
  ]

# TODO test without actual MessageQueue
# TODO test update
