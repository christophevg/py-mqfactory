from mqfactory                  import Message
from mqfactory.message.security import Signing, Signature
from mqfactory.tools            import Policy, Rule

def test_signing_setup(mq, transport, signature):
  Signing( mq, adding=signature )

  mq.before_sending.append.assert_called_with(signature.sign)
  mq.before_handling.append.assert_called_with(signature.validate)

class MockSignature(Signature):
  def _sign(self, message):
    return True

  def _validate(self, message):
    return True

def test_signing_policy():
  signature = MockSignature(Policy([
    Rule({"to": "unencrypted"}, False)
  ]))
  encrypted = Message("encrypted", "message")
  not_encrypted = Message("unencrypted", "message")
  assert signature.sign(encrypted)
  assert signature.sign(not_encrypted) == False
  assert signature.validate(encrypted)
  assert signature.validate(not_encrypted) == False
