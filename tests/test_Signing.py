from mqfactory.message.security import Signing

def test_signing_setup(mq, transport, signature):
  Signing( mq, adding=signature )

  mq.before_sending.append.assert_called_with(signature.sign)
  mq.before_handling.append.assert_called_with(signature.validate)
