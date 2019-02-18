import json

from mqfactory import MessageQueue

from mqfactory.message.security     import Signing
from mqfactory.message.security.rsa import RsaSignature

def test_ensire_sent_messages_are_signed(transport, message, keys, me):
  mq = Signing(
         MessageQueue(transport),
         adding=RsaSignature(
           keys=keys, me=me
         )
       )
  mq.send(message.to, message.payload)
  mq.process_outbox()
  
  assert len(transport.items) == 1
