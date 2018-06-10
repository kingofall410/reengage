import logging
import re
import string
from util import filter
from nltk.stem import PorterStemmer
from nltk.tokenize import sent_tokenize, word_tokenize

###################################################################################################
class Endpoint():
    def __init__(self, name, address):
        self.name = name
        self.address = address
        self.is_sender = False
        self.wordcloud = WordCloud()

    def __str__(self):
        return self.address

    def __eq__(self, other):
        return (self.name == other.name) and (self.address == other.address)

    def __hash__(self):
        return hash((self.name, self.address))

    def update_wordcloud(self, d):
        self.wordcloud = self.wordcloud.append(d)
        logging.debug("Wordcloud updated: %s", str(self.wordcloud))

    @staticmethod
    def get_or_create(endpoints, address, name):
        ep = Endpoint(address=address, name=name)
        try:
            ep = endpoints[endpoints.index(ep)]
        except(ValueError):#endpoint not in set
            endpoints.append(ep)
        logging.debug("Endpoint found: %s", address)
        return ep

    def set_sender(self, message=None):
        self.is_sender = True

###################################################################################################
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

###################################################################################################
class CustomHeader():
    def __init__(self, header_key, header_value):
        self.header_key = header_key
        self.header_value = header_value

###################################################################################################
class WordCloud():
    def __init__(self, d=None, case_sensitive=False, strip_punctuation=True):
        self.case_sensitive = case_sensitive
        self.strip_punctuation = strip_punctuation

        if d:

            #TODO:this strips similar words incorrectly - "The" vs "the"
            if case_sensitive and strip_punctuation:
                self.word_dict = {k.strip(string.punctuation):v for k,v in d.items()}

            elif not case_sensitive and strip_punctuation:
                self.word_dict = {k.lower().strip(string.punctuation):v for k,v in d.items()}

            elif case_sensitive and not strip_punctuation:
                self.word_dict = {k:v for k,v in d.items()}

            elif not case_sensitive and not strip_punctuation:
                self.word_dict = {k.lower():v for k,v in d.items()}

            #I'm filtering at the end since I don't want to have to call lower() and strip() twice for each key
            self.word_dict = {k:v for k,v in self.word_dict.items() if not filter.filter(k, "word")}
        else:
            self.word_dict = {}

    ###############################################################################################
    def append(self, other_dict):
        new_wc = WordCloud(d=other_dict)

        if (self.word_dict):
            for key in self.word_dict:
                if key in new_wc.word_dict:
                    new_wc.word_dict[key] = self.word_dict[key] + new_wc.word_dict[key]
                else:
                    new_wc.word_dict[key] = self.word_dict[key]
        return new_wc

    ###############################################################################################
    def stem(self):
        ps = PorterStemmer()
        for word in self.word_dict:
            stemmed_word = ps.stem(word)
            if stemmed_word in self.word_dict:
                self.word_dict[stemmed_word] += 1
            else:
                self.word_dict[stemmed_word] = 1

    ###############################################################################################
    def refilter(self):
        self.word_dict = {k:v for k,v in self.word_dict.items() if not filter.filter(k, "word")}

    ###############################################################################################
    def topX(self, x=10, start=0):
        return sorted(self.word_dict, key=self.word_dict.get, reverse=True)[start:start+x]

    ###############################################################################################
    def __add__(self, other):
        return self.append(other.word_dict)

    ###############################################################################################
    def __str__(self):
        return str(sorted(self.word_dict.items(), key=lambda x: x[1], reverse=True))

    ###############################################################################################
    def __len__(self):
        return len(self.word_dict)

'''don't use me
def test_create_word_cloud(message_body,is_stem = True):
    ps = PorterStemmer()
    cloud = {}
    for word in message_body.split():
        if is_stem: word = ps.stem(word)
        value = cloud.get(word, 0)
        cloud[word] = value+1
    return cloud'''

'''wordclouds are just dictionaries.  I haven't built much functionality into the class itself just yet.
endpoints will have wordclouds after the parse step (the same step that the endpoint is created in).
You can access a wordcloud by using <endpoint>.wordcloud - just another attribute.'''
def test_wc():
    endpoint1 = Endpoint("Test", "test@test.com")
    endpoint2 = Endpoint("Test2", "test2@test.com")
    endpoint3 = Endpoint("Test3", "test3@test.com")
    print("Endpoints:", endpoint1, endpoint2)

    '''wordclouds are case insensitive by default, and strip out all punctuation outside of words
    ("one-time-fee" will stay in, "Done." will be changed to "done")'''
    word_dict = test_create_word_cloud("Our employees really love working for us.", is_stem = True)
    endpoint1.update_wordcloud(word_dict)
    print(endpoint1.wordcloud)

    word_dict = test_create_word_cloud("I need to buy a new car ASAP!")
    endpoint2.update_wordcloud(word_dict)
    print(endpoint2.wordcloud)

    '''you can add two wordclouds or append a dict to a wordcloud.  Mostly I think you will want to
    add wordclouds of the groups of enpoints that result from your analysis'''
    word_dict = test_create_word_cloud("Are you sure about that?")
    endpoint1.update_wordcloud(word_dict)
    print(endpoint1.wordcloud)
    wc = endpoint1.wordcloud+endpoint2.wordcloud
    print(wc)
