import pytest

import base64

from mqfactory.message.security.rsa import RsaSignature
from mqfactory.message.security.rsa import generate_key_pair, encode
from mqfactory.message.security.rsa import serialize, sign, validate

from .conftest import CollectionMock

def test_own_key_loading():
  private, public = generate_key_pair()
  keys = CollectionMock({
    "tester" : { "private" : encode(private), "public" : encode(public) }
  })
  signer = RsaSignature(keys, me="tester")
  assert encode(signer.key) == encode(private)

def test_signing(message):
  private, public = generate_key_pair()
  keys = CollectionMock({
    "tester" : { "private" : encode(private), "public" : encode(public) }
  })
  signer = RsaSignature(keys, me="tester")
  signer.sign(message, ts="now")
  assert "signature" in message.tags
  assert "origin" in message.tags["signature"]
  assert message.tags["signature"]["origin"] == "tester"
  assert "ts" in message.tags["signature"]
  assert message.tags["signature"]["ts"] == "now"
  assert "hash" in message.tags["signature"]
  hash = base64.b64decode(message.tags["signature"].pop("hash"))
  # must use validation, cannot compare signatures as such
  validate(serialize(message), hash, public)

def test_validation(message):
  private, public = generate_key_pair()
  message.tags["signature"] = {
    "origin": "tester",
    "ts"    : "now"
  }
  message.tags["signature"]["hash"] = base64.b64encode(sign(serialize(message), private))
  keys = CollectionMock({
    "tester" : { "private" : encode(private), "public" : encode(public) }
  })
  signer = RsaSignature(keys, me="tester")
  signer.validate(message)
  