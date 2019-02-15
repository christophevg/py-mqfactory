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
def mocked_ticks():
  global next_ts
  next_ts += 1000
  return next_ts

def test_two_messages_with_retries_and_acks(transport, collection, ids, ticks):
  mq = JsonFormatting(
         Acknowledging(
           Persisting(
             MessageQueue(transport, ids=ids, ticks=ticks),
             into=collection
           ),
           ticks=mocked_ticks,
           timedout=mocked_to([False, False, True])
         )
       )
  mq.send("to 1", "payload 1")
  mq.send("to 2", "payload 2")
  assert collection.changelog == [
    'load',
    ('add', '1', {'to': 'to 1', 'payload': 'payload 1', 'tags': {
      'id': 1,
      'last': 1
    }}),
    ('add', '2', {'to': 'to 2', 'payload': 'payload 2', 'tags': {
      'id': 2,
      'last': 2
    }})
  ]

  mq.process_outbox() # send 1 and update with sent time
  assert collection.changelog[3::] == [
    ('update', '1', {'to': 'to 1', 'payload': 'payload 1', 'tags': {
      'id': 1,
      'last': 3,
      'ack': '/ack',
      'sent': 1000
    }})
  ]

  transport.deliver()
  assert transport.log == [
    ( 
      "to 1",
      json.dumps({
        "payload": "payload 1",
        "tags": { 
          "id" : 1,
          "last": 1,
          "ack": "/ack"
        }
      }, sort_keys=True)
    )
  ]  
  
  mq.process_outbox() # send 2 and update with sent time
  assert collection.changelog[4::] == [
    ('update', '2', {'to': 'to 2', 'payload': 'payload 2', 'tags': {
      'id': 2,
      'last': 4,
      'sent': 2000,
      'ack': '/ack'
    }})
  ]

  transport.deliver()
  assert transport.log[1::] == [
    ( 
      "to 2",
      json.dumps({
        "payload": "payload 2",
        "tags": {
          "id": 2,
          "last" : 2,
          "ack": "/ack"
        }
      }, sort_keys=True)
    )
  ]  

  mq.process_outbox() # defer 1 due to no timeout
  assert collection.changelog[5::] == [
    ('update', '1', {'to': 'to 1', 'payload': 'payload 1', 'tags': {
      'id': 1,
      'last': 5,
      'sent': 1000,
      'ack': '/ack'
    }})
  ]
  assert len(collection.changelog) == 6

  transport.deliver()
  assert len(transport.log) == 2

  mq.process_outbox() # defer 2
  assert len(collection.changelog) == 7

  transport.deliver()
  assert len(transport.log) == 2

  mq.process_outbox() # timeout 1, send it again, update sent time
  assert collection.changelog[7::] == [
    ('update', '1', {'to': 'to 1', 'payload': 'payload 1', 'tags': {
      "last" : 7,
      'sent': 3000,
      'ack': '/ack',
      'id': 1
    }})
  ]

  transport.deliver()
  assert transport.log[2::] == [
    ( 
      "to 1",
      json.dumps({
        "payload": "payload 1",
        "tags": {
          "id": 1,
          "last": 5,
          "sent": 1000,
          "ack": "/ack"
        },
      }, sort_keys=True)
    )
  ]

  # ack 1
  transport.deliver_direct( "/ack", json.dumps({ "tags" : { "ack": 1 } }) )

  assert collection.changelog[8::] == [
    ('remove', '1')
  ]

  # ack 2
  transport.deliver_direct( "/ack", json.dumps({ "tags" : { "ack": 2 } }) )

  assert collection.changelog[9::] == [
    ('remove', '2')
  ]

  assert len(mq.outbox.messages) == 0
  assert len(collection.items) == 0
  assert len(transport.log) == 3
