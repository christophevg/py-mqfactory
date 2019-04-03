import json

from mock import Mock, patch, call

from mqfactory import MessageQueue

from mqfactory.store             import Persisting
from mqfactory.message           import Message
from mqfactory.message.format.js import JsonFormatting
from mqfactory.transport         import Transport
from mqfactory.transport.qos     import Acknowledging

@patch("uuid.uuid4")
@patch("mqfactory.tools.clock.now")
def test_sending_two_messages_with_retries_and_acks(mocked_time, mocked_uuid,
                                                    inbox, outbox):
  mocked_time.side_effect = range(1, 11)
  mocked_uuid.side_effect = range(1, 5)

  transport             = Transport()
  transport.connect     = Mock()
  transport.disconnect  = Mock()
  transport._send       = Mock()
  transport._on_message = Mock()

  mq = JsonFormatting(
         Acknowledging(
           Persisting( MessageQueue(transport), inbox=inbox, outbox=outbox )
         )
       )

  mq.send("to 1", "payload 1")
  assert outbox.mock_calls[0] == call.load()
  outbox.add.assert_called_with({
    "to"     : "to 1",
    "payload": "payload 1",
    "tags" : { "id" : "1" }
  })

  mq.send("to 2", "payload 2")
  outbox.add.assert_called_with({
    "to"     : "to 2",
    "payload": "payload 2",
    "tags" : { "id" : "2" }
  })
  
  mq.process_outbox() # send 1 and update with sent time
  outbox.update.assert_called_with( 1, {
    "to": "to 1",
    "payload": "payload 1",
    "tags": {
      "id": "1",
      "ack": mq.name + "/ack",
      "sent": 3
    }
  })
  transport._send.assert_called_once()
  message, = transport._send.call_args[0]
  assert message.to      == "to 1"
  assert message.payload == json.dumps({
    "payload": "payload 1",
    "tags": {
      "id" : "1",
      "ack": mq.name + "/ack"
    }
  }, sort_keys=True)
  transport._send.reset_mock()

  mq.process_outbox() # send 2 and update with sent time
  outbox.update.assert_called_with( 2, {
    "to": "to 2",
    "payload": "payload 2",
    "tags": {
      "id": "2",
      "ack": mq.name + "/ack",
      "sent": 5
    }
  })
  transport._send.assert_called_once()
  message, = transport._send.call_args[0]
  assert message.to      == "to 2"
  assert message.payload == json.dumps({
    "payload": "payload 2",
    "tags": {
      "id" : "2",
      "ack": mq.name + "/ack"
    }
  }, sort_keys=True)
  transport._send.reset_mock()
  
  mq.process_outbox() # defer 1 due to no timeout
  outbox.update.assert_called_with( 1, {
    "to": "to 1",
    "payload": "payload 1",
    "tags": {
      "id": "1",
      "ack": mq.name + "/ack",
      "sent": 3
    }
  })
  transport._send.assert_not_called()

  mq.process_outbox() # defer 2
  outbox.update.assert_called_with( 2, {
    "to": "to 2",
    "payload": "payload 2",
    "tags": {
      "id": "2",
      "ack": mq.name + "/ack",
      "sent": 5
    }
  })
  transport._send.assert_not_called()

  # move time forward to trigger timeouts
  mocked_time.side_effect = range(5011, 5022)

  mq.process_outbox() # timeout 1, send it again, update sent time
  outbox.update.assert_called_with( 1, {
    "to": "to 1",
    "payload": "payload 1",
    "tags": {
      "id": "1",
      "ack": mq.name + "/ack",
      "sent": 5012
    }
  })
  transport._send.assert_called_once()
  message, = transport._send.call_args[0]
  assert message.to      == "to 1"
  assert message.payload == json.dumps({
    "payload": "payload 1",
    "tags": {
      "id" : "1",
      "ack": mq.name + "/ack",
      "sent": 3
    }
  }, sort_keys=True)
  transport._send.reset_mock()  

  # simulate "ack 1" from other party (aka "to 1")
  transport._on_message.assert_called_once()
  to, handler = transport._on_message.call_args[0]
  assert to == mq.name + "/ack"
  handler(Message(to, json.dumps({ "tags" : { "id": "x", "confirm": "1" }})))
  inbox.add.assert_called_with({
    "to"     : mq.name + "/ack",
    "payload": "",
    "tags": {
      "id": "x",
      "confirm": "1"
    }})

  mq.process_inbox()
  outbox.remove.assert_called_with(1)

  # simulate "ack 2" from other party (aka "to 2")
  handler(Message(to, json.dumps({ "tags" : { "id": "y", "confirm": "2" }})))
  inbox.add.assert_called_with({
    "to"     : mq.name + "/ack",
    "payload": "",
    "tags": {
      "id": "y",
      "confirm": "2"
    }})

  mq.process_inbox()
  outbox.remove.assert_called_with(2)

@patch("uuid.uuid4")
@patch("mqfactory.tools.clock.now")
def test_receiving_message_requiring_acks(mocked_time, mocked_uuid,
                                          inbox, outbox, message):
  mocked_time.side_effect = range(1, 11)
  mocked_uuid.side_effect = range(1, 5)

  transport             = Transport()
  transport.connect     = Mock()
  transport.disconnect  = Mock()
  transport._send       = Mock()
  transport._on_message = Mock()

  mq = JsonFormatting(
         Acknowledging(
           Persisting( MessageQueue(transport), inbox=inbox, outbox=outbox )
         )
       )

  transport._on_message.assert_called_once()
  to, incoming_ack_handler = transport._on_message.call_args[0]
  assert to == mq.name + "/ack"
  transport._on_message.reset_mock()

  # setup subscription on "incoming"
  delivered = []
  def accept(msg):
    delivered.append(msg)
  mq.on_message(message.to, accept)

  # simulate incoming message by getting the handler and calling it
  transport._on_message.assert_called_once()
  to, incoming_handler = transport._on_message.call_args[0]
  assert to == message.to
 
  message.tags["ack"] = "origin/ack"
  incoming_handler(Message(message.to, json.dumps(dict(message))))

  inbox.add.assert_called_once()
  incoming_message = inbox.add.call_args[0][0]
  assert incoming_message == dict(message)

  mq.process_inbox()
  
  # is message delivered locally ?
  assert len(delivered) == 1
  assert delivered[0].payload == message.payload
  assert delivered[0].tags    == message.tags
  
  # has ack been put into the outbox ?
  outbox.add.assert_called_once()
  outgoing_message = outbox.add.call_args[0][0]
  assert outgoing_message["to"] == "origin/ack"

  mq.process_outbox()

  # has the ack been sent ?
  transport._send.assert_called_once()
  
  # has the ack been removed from the outbox ? (because we dont' resend acks)
  outbox.remove.assert_called_once()
