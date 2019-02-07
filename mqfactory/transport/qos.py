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
  def __init__(self, mq, timedout=check_timeout, ack_channel="/ack"):
    self.mq = mq
    self.timedout = timedout
    self.ack_channel = ack_channel
    self.mq.on_message(self.ack, self.handle)
    
  def request(self, message):
    if not "ack" in message.tags:
      message.tags["ack"] = self.ack_channel
    else:
      if self.timedout(message): raise DeferException

  def wait(self, message):
    message.tags["sent"] = millis()
    self.mq.outbox.append(message)

  def give(self, message):
    if "ack" in message.tags:
      self.mq.send(message.tags["ack"], { "id" : message.tags["id"] } )

  def handle(self, message):
    self.mq.outbox.pop(lambda m: m.tags["id"] == message.payload["id"])

def Acknowledging(mq):
  acknowledgement = Acknowledgement(mq)
  mq.before_sending.append(acknowledgement.request)
  mq.after_sending.append(acknowledgement.wait)
  mq.after_handling.append(acknowledgement.give)
  return mq
