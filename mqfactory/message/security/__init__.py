class Signature(object):
  def sign(self, payload):
    raise NotImplementedError("implement signing of payload")

  def validate(self, payload):
    raise NotImplementedError("implement validation of payload")

def Signing(mq, adding=Signature()):
  mq.before_sending.append(adding.sign)
  mq.before_handling.append(adding.validate)
  return mq
