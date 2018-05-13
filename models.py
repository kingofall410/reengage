class Endpoint():
    def __init__(self, name, address):
        self.name = name
        self.address = address

    def __str__(self):
        #return self.name+" <"+self.address+">"
        return self.address


    def __eq__(self, other):
        return (self.name == other.name) and (self.address == other.address)

    def __hash__(self):
        return hash((self.name, self.address))

    @staticmethod
    def get_or_create(endpoints, address, name):
        ep = Endpoint(address=address, name=name)
        try:
            ep = endpoints[endpoints.index(ep)]
        except(ValueError):#endpoint not in set
            endpoints.append(ep)
        return ep

class Message():
    def __init__(self, id, sender, subject, datetime, body, flatmbox):
        self.id = id
        self.sender = sender
        self.subject = subject
        self.datetime = datetime
        self.body = body
        self.flatmbox = flatmbox
        self.receivers = []
        self.ch = []

    def __str__(self):
        return str(self.id)+"---"+str(self.sender)+"---"+str(self.subject)

    def addRecipient(self, r):
        self.receivers.append(r)

    def addCH(self, ch):
        self.ch.append(ch)

class CustomHeader():
    def __init__(self, header_key, header_value):
        self.header_key = header_key
        self.header_value = header_value
