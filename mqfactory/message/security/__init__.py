class Signature(object):
  def sign(self, message):
    raise NotImplementedError("implement signing of message")

  def validate(self, message):
    raise NotImplementedError("implement validation of message")

def Signing(mq, adding=Signature()):
  mq.before_sending.append(adding.sign)
  mq.before_handling.append(adding.validate)
  return mq
