from mqfactory import MessageQueue, MessageStore

from . import TransportMock, StoreMock

def test_store_actions():
  mq = MessageQueue(TransportMock())
  store = StoreMock()
  ms = MessageStore(store)
  ms.persist(mq)

  mq.send("to 1", "payload 1")
  mq.send("to 2", "payload 2")
  mq.process_outbox()

  assert store.changelog == [
    "load",
    ("add",    ("to 1", "payload 1")),
    ("add",    ("to 2", "payload 2")),
    ("remove", ("to 1", "payload 1")),
    ("remove", ("to 2", "payload 2"))    
  ]
