import logging

class Endpoint():
    def __init__(self, name, address):
        self.name = name
        self.address = address
        self.wordcloud = None

    def __str__(self):
        #return self.name+" <"+self.address+">"
        return self.address

    def __eq__(self, other):
        return (self.name == other.name) and (self.address == other.address)

    def __hash__(self):
        return hash((self.name, self.address))

    def update_wordcloud(self, d):
        if self.wordcloud:
            self.wordcloud = self.wordcloud.append(d)
        else:
            self.wordcloud = WordCloud(d)
        '''wc = WordCloud(d)
        if self.wordcloud:
            self.wordcloud = self.wordcloud + wc
        else:
            self.wordcloud = wc'''

    @staticmethod
    def get_or_create(endpoints, address, name):
        ep = Endpoint(address=address, name=name)
        try:
            ep = endpoints[endpoints.index(ep)]
        except(ValueError):#endpoint not in set
            endpoints.append(ep)
        logging.debug("Endpoint found: %s", address)
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

class WordCloud():
    def __init__(self, d=None):
        if d:
            self.word_dict = d
        else:
            self.word_dict = {}

    def append(self, other_dict):
        new_wc = WordCloud()
        for key in self.word_dict:
            if key in other_dict:
                new_wc.word_dict[key] = self.word_dict[key] + other_dict[key]
            else:
                new_wc.word_dict[key] = self.word_dict[key]

        for key in other_dict:
            if key not in self.word_dict:
                new_wc.word_dict[key] = other_dict[key]
        return new_wc

    def __add__(self, other):
        return self.append(other.word_dict)

    def __str__(self):
        return str(sorted(self.word_dict.items(), key=lambda x: x[1], reverse=True))

class CustomHeader():
    def __init__(self, header_key, header_value):
        self.header_key = header_key
        self.header_value = header_value
