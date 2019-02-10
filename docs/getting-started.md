# Getting Started

The following example shows the capabilities I needed when I started implementing this. I needed: 

- MongoDB-based persistency
- for an MQTT message broker
- (with RSA-based public/private-key-based signatures)
- (and acknowledgment with retries after a fixed timeout.)

The following steps allow you to see these requirements in action:

Install a local instance of MongoDB and the Mosquitto MQTT broker. On macOS with brew installed, your minimal survival commands are:

```bash
$ brew install mongodb
$ brew services start mongodb
$ brew install mosquitto
$ brew services start mosquitto
```

Create a folder with a virtual Python environment:

```bash
$ mkdir demo
$ cd demo
$ virtualenv venv
$ . venv/bin/activate
(venv) $ pip install mqfactory
```

> TIP: if you want to work from the repository you can also use pip to install mqfactory: `pip install /path/to/cloned/repository/mqfactory`

Create a file `demo.py` containing:

```python
import time
import socket

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

# A standard MQ will hold its messages in an `Outbox` in memory. Using a
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

mq = JsonFormatting(
       Signing(
         Acknowledging(
           Persisting(
             Threaded(
               MessageQueue(
                 MQTTTransport("mqtt://localhost:1883")
               )
             ),
             into=mongo["messages"]
           )
         ),
         adding=RsaSignature(mongo["keys"])
       )
     )

# and use it to send and receive messages

def show(msg):
  print "received {0} from {1}, tagged with {2}".format(
    msg.payload, msg.to, msg.tags
  )

mq.on_message("myself", show)

mq.send("myself", "a message")

time.sleep(3) # to make sure we receive the answer
```

Now in a separate terminal setup a mosquitto subscription:

```bash
$ mosquitto_sub -v -t '#'
```

Optionally, you can also monitor your MongoDB using [mongotail](https://github.com/mrsarm/mongotail):

```bash
$ pip install mongotail
$ mongotail mqfactory -l 2
Profiling level set to level 2
$ mongotail mqfactory -f
```

And run the demo script:

```bash
(venv) $ LOG_LEVEL=INFO python demo.py 
received a message from myself, tagged with {u'ack': u'/ack', u'id': u'abe527c6-14fd-414e-a43b-166ed2e84a34'}
```

The mosquitto subscription shows the messages as they passes through the broker:

- the actual message, with acknowledge request and signature
- the acknowledgement, referring to the original message and also with a signature

```bash
myself {"payload": "a message", "tags": {"ack": "/ack", "id": "abe527c6-14fd-414e-a43b-166ed2e84a34", "signature": {"hash": "MCRNn/SNXYK4yRxjms0qNZUpwDCEn0ad9wlvBZhyecmx+TI+IM6CaaGbjwE7usPpnbY2iALKrqksrNRWuIREgtxHlJ9fq6Sd4AvanEXwW1+exzKdPg7wMMNNSTmCgAfILFBsthho1NYrAFqt0AAphfLkgUy5Q4ybxv67ducHLYCZ0aOy5pqk/kqxfPWTBpi63ULqrT9ulMQLxraP29oj/nip60D7of4ff/bmLK5aTGInfdKXd/gnjM45zJCtU6RxkNKIP9UWLQFBEFFCn9CLVRW4DkSMpGNWaaktAD6fW641xH87IG1CdMWoeS9rLwHkeVGm+sbeV0yEeAinOFVuoA==", "origin": "kibo.local", "ts": "2019-02-10 16:49:01.208667"}}}
/ack {"payload": {}, "tags": {"ack": "abe527c6-14fd-414e-a43b-166ed2e84a34", "id": "246c19fa-7755-4fed-b4d4-c48af1513faf", "signature": {"hash": "FjLJLE5RCN5O3qyOYRT7twgjprZdLvnusgxsGU+sWkz4hlqASftSkxezkvvY6tREDT7yi437Q/lB5TQcA6A6KJumvCsZoaRHbE/9sQNTXe0aYSqKt9rZLusdCwuny6ghnhpXg3IT06RQBlxwxNonjhMyb+OOecvG5nTr9o7zhs8bsHDOZhiDVs/RH8CfY9bJGuIGYkUg3bZ10Bou7A8Q3TDHMsnQV+jAYKGIt54cnmGFwW+Ep1t7Cf3gBehLT7b7EaCJLZufNpwTzDiUByAcyP6GPpn+DGDBX7gIzFxBXfzDE2QSerVjvA6eI+ejSmbogEr9uI/kV0YLNPuaRMWwbg==", "origin": "kibo.local", "ts": "2019-02-10 16:49:01.704390"}}}
```

The MongoDB logging will show the following activity:

```bash
2019-02-10 16:49:01.200 REMOVE    [keys] : {"_id": "kibo.local"}. 0 deleted.
2019-02-10 16:49:01.201 INSERT    [keys] : 1 inserted.
2019-02-10 16:49:01.206 QUERY     [keys] : {"_id": "kibo.local"}. 1 returned.
2019-02-10 16:49:01.207 QUERY     [messages] : {}. 0 returned.

2019-02-10 16:49:01.208 INSERT    [messages] : 1 inserted.
2019-02-10 16:49:01.211 INSERT    [messages] : 1 inserted.
2019-02-10 16:49:01.213 REMOVE    [messages] : {"_id": ObjectId("5c6055fde4e2ade0a8d8bd44")}. 1 deleted.

2019-02-10 16:49:01.339 QUERY     [keys] : {"_id": "kibo.local"}. 1 returned.
2019-02-10 16:49:01.704 INSERT    [messages] : 1 inserted.
2019-02-10 16:49:01.706 REMOVE    [messages] : {"_id": ObjectId("5c6055fde4e2ade0a8d8bd46")}. 1 deleted.

2019-02-10 16:49:01.707 QUERY     [keys] : {"_id": "kibo.local"}. 1 returned.
2019-02-10 16:49:01.763 REMOVE    [messages] : {"_id": ObjectId("5c6055fde4e2ade0a8d8bd45")}. 1 deleted.
```

First some setup:

- the removal of optional previous keys and the provisioning of a fresh key pair
- the retrieval of the key pair to fetch the private key to sign with
- a query to load any previous messages (0 in this case)

Then the actual sending of the message:

- an insertion for the message we want to send
- an insertion for a retry
- a removal of the sent message

The message arrives and...

- a query to fetch the public key is performed to validate the signature
- an acknowledging message is created
- the sent acknowledgement is removed

Finally the acknowledgement arrives and...

- a query to fetch the public key is performed to validate the signature
- the pending retry message is now also removed

Every aspect (almost technically literally) is an implementation of an interface, so adding a different store, transport, signing procedure, retry strategy, requires a rather small implementation of such an interface.
