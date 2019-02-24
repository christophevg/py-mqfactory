import time
import socket

# The core of the factory allows for instantiating a `MessageQueue`. Such an MQ
# has an inbox and an outbox, which can be processed using the `process_inbox`
# and `process_outbox` methods (or the `send_and_receive` method). To automate
# this we can apply `Threaded` to the MQ to automate calling these methods.
from mqfactory                      import Threaded, MessageQueue

# An MQ needs at least a way to send its message, this is a `Transport`. Here we
# use an MQTT implementation.
from mqfactory.transport.mqtt       import MQTTTransport

# One aspect of transporting messages is how much care is taken in making sure
# they are delivered. This is often called quality of service and can take many
# forms. Here we choose to retry sending messages untill they are acknowledged.
from mqfactory.transport.qos        import Acknowledging

# An MQ takes any payload and will pass it as-is. Here we choose to have the 
# payload formatted using JSON, taking care of serializing and deserializing.
from mqfactory.message.format.js    import JsonFormatting

# A standard MQ will hold its messages in a `Queue` in memory. Using a
# `Collection` in a `Store` we can persist these, e.g. to a `MongoStore`.
from mqfactory.store                import Persisting
from mqfactory.store.mongo          import MongoStore

# Let's use a localy running MongoDB instance:
mongo = MongoStore("mongodb://localhost:27017/mqfactory")

# Beside formatting it using JSON, we also choose to have our payload signed and
# validated using a public/private keypair. Keys for these signatures are also
# storable in a `Collection` in a `Store`, such as the `MongoStore`.
from mqfactory.message.security     import Signing
from mqfactory.message.security.rsa import RsaSignature

# Since we want to sign our messages, we need to provision a keypair.
from mqfactory.message.security.rsa import generate_key_pair, encode
private, public = generate_key_pair()

# We store the keypair in a MongoDB collection(keys) and identify the pair by
# our hostname, which is the default used by MQFactory.
HOSTNAME = socket.gethostname()
mongo["keys"].remove(HOSTNAME)
mongo["keys"].add({
  "_id": HOSTNAME,
  "private": encode(private),
  "public" : encode(public)
})

# Now we can finally assemble all these components into our own specific MQ,
# adding layer after layer:

mq = JsonFormatting(
       Signing(
         Acknowledging(
           Persisting(
             Threaded(
               MessageQueue(
                 MQTTTransport("mqtt://localhost:1883")
               )
             ),
             inbox=mongo["inbox"],
             outbox=mongo["outbox"]
           )
         ),
         adding=RsaSignature(mongo["keys"])
       )
     )

# When receiving a message, just print it to the console...

def show(msg):
  print "received {0} from {1}, tagged with {2}".format(
    msg.payload, msg.to, msg.tags
  )

# Subscribe to incoming messages addressed to myself and handle them with show.

mq.on_message("myself", show)

# Finally, send a message ... to myself.

mq.send("myself", "a message")

time.sleep(1) # to make sure we receive the answer ;-)
