import sys
import logging
import time
import socket

from mqfactory.tools                import clock

# The core of the factory allows for instantiating a `MessageQueue`. Such an MQ
# has an outbox, which can be processed using the `process_outbox` method. To
# automate this we can apply `Threaded` to the MQ to automate calling this
# method.
from mqfactory                      import Threaded, MessageQueue

# An MQ needs at least a way to send its message, this is a `Transport`. Here we
# select the MQTT implementation.
from mqfactory.transport.mqtt       import MQTTTransport

# One aspect of transporting messages is how much care is taken in making sure
# they are delivered. This is often called quality of service and can take many
# forms. Here we choose to retry sending messages untill they are acknowledged.
from mqfactory.transport.qos        import Acknowledging

# An MQ takes any payload and will pass it as-is. Here we choose to have the 
# payload formatted using JSON, taking care of serializing and deserializing.
from mqfactory.message.format.js    import JsonFormatting

# A standard MQ will hold its messages in an `Queue` in memory. Using a
# `Collection` in a `Store` we can persist these, e.g. to a `MongoStore`.
from mqfactory.store                import Persisting
from mqfactory.store.mongo          import MongoStore

# Beside formatting it using JSON, we also choose to have our payload signed and
# validated using a public/private keypair. Keys for these signatures are also
# storable in a `Collection` in a `Store`, such as the `MongoStore`.
from mqfactory.message.security     import Signing
from mqfactory.message.security.rsa import RsaSignature

# we need to provision a keypair
from mqfactory.message.security.rsa import generate_key_pair, encode
private, public = generate_key_pair()

# We can now assemble all these components into our own specific MQ:

mongo = MongoStore("mongodb://localhost:27017/mqfactory")

HOSTNAME = socket.gethostname()

mongo["keys"].remove(HOSTNAME)
mongo["keys"].add({
  "_id": HOSTNAME,
  "private": encode(private),
  "public" : encode(public)
})

def make_mq(name, mqtt="mqtt://localhost:1883", keys="keys"):
  return JsonFormatting(
           Signing(
             Acknowledging(
               Persisting(
                 Threaded(
                   MessageQueue(
                     MQTTTransport(mqtt),
                     name=name
                   )
                 ),
                 inbox=mongo[name+"-inbox"],
                 outbox=mongo[name+"-outbox"]
               )
             ),
             adding=RsaSignature(mongo[keys])
           )
         )

mq_ping = make_mq("ping")
mq_pong = make_mq("pong")

stats = { "ping": 0, "pong": 0, "start": 0, "stop": False }

def ping(message=None):
  if(stats["stop"]): return
  logging.info("PING")
  stats["ping"] += 1
  mq_ping.send("ping", "ping")

def pong(message=None):
  if(stats["stop"]): return
  logging.info("PONG")
  stats["pong"] += 1
  mq_pong.send("pong", "pong")

mq_ping.on_message("pong", ping)
mq_pong.on_message("ping", pong)

stats["start"] = clock.now()
ping()

try:
  while(True):
    if stats["start"] > 0:
      elapsed = (clock.now() - stats["start"])/1000
      if elapsed > 0:
        speed = int((stats["ping"] + stats["pong"]) * 1.0 / elapsed)
        sys.stdout.write("Speed: {0} msg/s ({1}, {2}, {3}) \r".format(speed, stats["ping"], stats["pong"], elapsed) )
        sys.stdout.flush()
    time.sleep(0.1)
except KeyboardInterrupt:
  logging.info("stopping...")
  stats["stop"] = True
