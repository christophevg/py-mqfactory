import json

from mqfactory import MessageQueue

from mqfactory.store             import Persisting
from mqfactory.message           import Message
from mqfactory.message.format.js import JsonFormatting
from mqfactory.transport.qos     import Acknowledging

from .test_Acknowledging import mocked_to

next_uid = 0
def mocked_uid():
  global next_uid
  next_uid += 1
  return "uuid-{0}".format(next_uid)

next_ts = 0
def mocked_clock():
  global next_ts
  next_ts += 1000
  return next_ts

def test_two_messages_with_retries_and_acks(transport, collection):
  mq = JsonFormatting(
         Acknowledging(
           Persisting(
             MessageQueue(transport),
             into=collection
           ),
           uid=mocked_uid, clock=mocked_clock,
           timedout=mocked_to([False, False, True])
         )
       )
  mq.send("to 1", "payload 1")
  mq.send("to 2", "payload 2")

  mq.process_outbox() # send 1, schedule retry 3
  assert collection.changelog == [
    'load',
    ('add', '1', {'to': 'to 1', 'payload': 'payload 1', 'tags': {}}),
    ('add', '2', {'to': 'to 2', 'payload': 'payload 2', 'tags': {}}),
    ('add', '3', {'to': 'to 1', 'payload': 'payload 1', 'tags': {
      'sent': 1000,
      'ack': {'to': '/ack', 'id': 'uuid-1'}
    }}),
    ('remove', '1'),
  ]

  transport.deliver()
  assert transport.log == [
    ( 
      "to 1",
      json.dumps({
        "payload": "payload 1",
        "tags": { 
          "ack": { "id": "uuid-1", "to": "/ack" },
        }
      }, sort_keys=True)
    )
  ]  
  
  mq.process_outbox() # send 2  schedule retry 5
  assert collection.changelog[5::] == [
    ('add', '5', {'to': 'to 2', 'payload': 'payload 2', 'tags': {
      'sent': 2000,
      'ack': {'to': '/ack', 'id': 'uuid-2'}}}),
    ('remove', '2')
  ]

  transport.deliver()
  assert transport.log[1::] == [
    ( 
      "to 2",
      json.dumps({
        "payload": "payload 2",
        "tags": { 
          "ack": { "id": "uuid-2", "to": "/ack" },
        }
      }, sort_keys=True)
    )
  ]  

  mq.process_outbox() # defer 1
  assert len(collection.changelog) == 7

  transport.deliver()
  assert len(transport.log) == 2

  mq.process_outbox() # defer 2
  assert len(collection.changelog) == 7

  transport.deliver()
  assert len(transport.log) == 2

  mq.process_outbox() # timeout 1, send 3, schedule retry 7
  assert collection.changelog[7::] == [
    ('add', '7', {'to': 'to 1', 'payload': 'payload 1', 'tags': {
      'sent': 3000,
      'ack': {'to': '/ack', 'id': 'uuid-1'}}}),
    ('remove', '3')
  ]

  transport.deliver()
  assert transport.log[2::] == [
    ( 
      "to 1",
      json.dumps({
        "payload": "payload 1",
        "tags": {
          "sent": 1000,
          "ack": { "id": "uuid-1", "to": "/ack" },
        }
      }, sort_keys=True)
    )
  ]

  transport.deliver_direct(
    "/ack",
    json.dumps({ "tags" : { "ack" : { "id" : "uuid-1" } }})
  ) # ack 1

  assert collection.changelog[9::] == [
    ('remove', '7')
  ]
  
  transport.deliver_direct(
    "/ack",
    json.dumps({ "tags" : { "ack" : { "id" : "uuid-2" } }})
  ) # ack 2

  assert collection.changelog[10::] == [
    ('remove', '5')
  ]

  assert len(mq.outbox.messages) == 0
  assert len(collection.items) == 0
  assert len(transport.log) == 3
