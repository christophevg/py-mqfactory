import logging
import uuid

from mqfactory import DeferException, millis
from mqfactory.message import Message

'''
Acknowledgment works in several phases:
- when used, a subscription on an ack channel is made
- when sending a message, an "ack" header is added, containing the ack channel
- after sending the message, the send message is added back to the outbox with
  a timestamp
- if the message is ready to be send again, but the time since sending it hasn't
  surpassed a timeout, sending is defered
- if the message is ready to be send again, and the the timeout has passed, it
  is just send again
- if an acknowledgement is received, the corresponding message is removed
'''

def check_timeout(message):
  return millis() - message.tags["sent"] >= 5000

class Acknowledgement(object):
  def __init__(self, mq, timedout=check_timeout, ack_channel="/ack", uid=uuid.uuid4, clock=millis):
    self.mq = mq
    self.timedout = timedout
    self.ack_channel = ack_channel
    self.uid = uid
    self.clock = clock
    self.mq.on_message(self.ack_channel, self.handle)
    
  def request(self, message):
    if not "ack" in message.tags:
      message.tags["ack"] = { "id": str(self.uid()), "to" : self.ack_channel }
    else:
      if "sent" in message.tags:
        if not self.timedout(message):
          raise DeferException

  def wait(self, message):
    # don't add retry for acknowledgements themnselves
    if "ack" in message.tags and "to" in message.tags["ack"]:
      retry = message.copy()
      retry.tags["sent"] = self.clock()
      self.mq.outbox.append(retry)

  def give(self, message):
    if "ack" in message.tags and "to" in message.tags["ack"]:
      self.mq.send(
        message.tags["ack"]["to"], {},
        { "ack" : { "id" : message.tags["ack"]["id"] } }
      )

  def handle(self, message):
    def acked_message(m):
      try:
        return m.tags["ack"]["id"] == message.tags["ack"]["id"]
      except KeyError:
        return False

    try:
      self.mq.outbox.pop(self.mq.outbox.index(acked_message))
    except ValueError:
      logging.warn("unknown message ack")

def Acknowledging(mq, ack=None, uid=uuid.uuid4, clock=millis, timedout=check_timeout):
  acknowledgement = ack or Acknowledgement(mq, uid=uid, clock=clock, timedout=timedout)
  mq.before_sending.append(acknowledgement.request)
  mq.after_sending.append(acknowledgement.wait)
  mq.after_handling.append(acknowledgement.give)
  return mq
