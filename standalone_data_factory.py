class Endpoint():
    def __init__(self, name, address):
        self.name = name
        self.address = address

class Message():
    def __init__(self, id, sender, subject, datetime, body, flatmbox):
        self.id = id
        self.sender = sender
        self.subject = subject
        self.datetime = datetime
        self.body = body
        self.flatmbox = flatmbox

    def addRecipient(r):
        receiver.append(r)

class CustomHeader():
    def __init__(self, message, header_key, header_value):
        self.message = message
        self.header_key = header_key
        self.header_value = header_value

def createCustomHeader(message, header_key, header_value):
    #return SCustomHeader(message, header_key, header_value)
    return CustomHeader.objects.create(header_key=header_key, header_value=header_value, message=message)

def createMessage(id, sender, subject, datetime, body, flatmbox):
    #return SMessage(id, sender, receiver, subject, datetime, body, flatmbox)
    return Message.objects.get_or_create(id=id, sender=sender, subject=subject, datetime=datetime, body=body, flatmbox=flatmbox)[0]

def createEndpoint(name, address):
    #return SEndpoint(name, address)
    return Endpoint.objects.get_or_create(address=address, name=name)[0]
