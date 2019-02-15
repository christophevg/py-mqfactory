from mqfactory.message.security import Signing

from mqfactory import MessageQueue

from mqfactory.store import Persisting

from .conftest import TransportMock, SignatureMock

def test_signing():
  transport = TransportMock()
  signature = SignatureMock()
  mq = Signing( MessageQueue(transport), adding=signature )
  mq.send("to 1", "payload 1")
  mq.process_outbox()

  assert len(transport.items) == 1
  assert transport.items[0].tags["signature"] == signature.signature
