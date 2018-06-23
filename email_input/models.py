import logging, re, string, copy
from collections import defaultdict
from util import filter
from nltk.stem import PorterStemmer
from nltk.tokenize import sent_tokenize, word_tokenize

###################################################################################################
class Endpoint():
    def __init__(self, name, address, xfrom):

        self.address = address
        #if name is the same as address that's not helpful
        #try to extract the name from somewhere else
        if name == address and '@' in name:
            if xfrom:
                name = xfrom
            else:
                name = name[:address.find('@')]
                namesplit_index = name.rfind(".")
                if namesplit_index == 0:
                    name = name[1:]
                elif namesplit_index > 0:
                    name = name[:namesplit_index] +" "+name[namesplit_index+1:]

        self.names = [name]
        self.wordcloud = WordCloud()
        self.initials = ("".join([ele[0] for ele in address.split(".")[:-1] if ele])).upper()

    def __str__(self):
        return self.address

    def __eq__(self, other):
        #return (self.name == other.name) and (self.address == other.address)
        return self.address == other.address

    def __hash__(self):
        return hash(self.address)

    def update_wordcloud(self, other):
        self.wordcloud.append(other)
        logging.debug("Wordcloud updated: %s", str(self.wordcloud))

    def update_names(self, *args):
        for name in args:
            if name and name != self.address and name not in self.names:
                self.names.append(name)

    @staticmethod
    def get_or_create(messages_by_endpoint, address, name, xfrom=None):
        
        if address in messages_by_endpoint:
            #messages_by_endpoint is a mapping of email address to (endpoint, [messages])
            sender_tuple = messages_by_endpoint[address]
            sender_tuple[0].update_names(name, xfrom)
        else:
            messages_by_endpoint[address] = (Endpoint(address=address, name=name, xfrom=xfrom), [])
            sender_tuple = messages_by_endpoint[address]

        logging.debug("Endpoint found: %s", address)
        return sender_tuple

###################################################################################################
class Message():
    def __init__(self, id, sender, subject, datetime, body):
        self.id = id
        self.sender = sender
        self.subject = subject
        self.datetime = datetime
        self.body = body
        self.receivers = []

    def __str__(self):
        return str("From: "+str(self.sender)+"; To: "+str([str(r) for r in self.receivers])+"; Subj: "+str(self.subject))

    def addRecipient(self, r):
        self.receivers.append(r)

###################################################################################################
class WordCloud():
    ps = PorterStemmer()

    ###############################################################################################
    def process(self, word):
        if not self.case_sensitive:
            word = word.lower()

        if self.strip_punctuation:
            word = word.strip(string.punctuation)

        if self.stem:
            word = self.ps.stem(word)

        if self.filter and filter.filter(word, "word"):
            word = None

        return word

    ###############################################################################################
    def add_text(self, text):

        if text:
            for word in text.split():
                self.raw_dict[word] += 1
                word = self.process(word)
                if word:
                    self.processed_dict[word] += 1

    ###############################################################################################
    def add_dict(self, d):

        if d:
            for word in d:
                self.raw_dict[word] += 1
                processed_word = self.process(word)
                if word:
                    self.processed_dict[processed_word] += d[word]

    ###############################################################################################
    def __init__(self, text=None, case_sensitive=False, strip_punctuation=True, stem=True,
                 filter=True):
        self.case_sensitive = case_sensitive
        self.strip_punctuation = strip_punctuation
        self.stem = stem
        self.filter = filter

        #store the dict with all flags off so that we can add WCs with different flags
        self.raw_dict = defaultdict(int)
        self.processed_dict = defaultdict(int)

        self.add_text(text)

    ###############################################################################################
    def append(self, other):

        if type(other) is str:
            self.add_text(other)
        elif type(other) is WordCloud:
            self.add_dict(other.raw_dict)
        elif type(other) is dict:
            self.add_dict(other)
        elif type(other) is list:
            for text in other:
                self.add_text(text)
        else:
            logging.warning("Adding something strange to a wordcloud %s %s", type(other), other)

        return self

    ###############################################################################################
    def restem(self):
        new_processed_dict = defaultdict(int)
        for word in self.processed_dict:
            stemmed_word = self.ps.stem(word)
            new_processed_dict[stemmed_word] += self.processed_dict[word]

        self.processed_dict = new_processed_dict
        return self

    ###############################################################################################
    def decase(self):
        new_processed_dict = defaultdict(int)
        for word in self.processed_dict:
            decased_word = word.lower()
            new_processed_dict[decased_word] += self.processed_dict[word]

        self.processed_dict = new_processed_dict
        return self

    ###############################################################################################
    def refilter(self):
        self.processed_dict = {k:v for k,v in self.processed_dict.items() if not filter.filter(k, "word")}

        return self

    ###############################################################################################
    def topX(self, x=10, start=0):
        return sorted(self.processed_dict, key=self.processed_dict.get, reverse=True)[start:start+x]

    ###############################################################################################
    def __add__(self, other):
        new_wc = copy.deepcopy(self)
        new_wc.append(other)
        return new_wc

    ###############################################################################################
    def __str__(self):
        return str(sorted(self.processed_dict.items(), key=lambda x: x[1], reverse=True))

    ###############################################################################################
    def raw(self):
        return str(sorted(self.raw_dict.items(), key=lambda x: x[1], reverse=True))

    ###############################################################################################
    def __len__(self):
        return len(self.processed_dict)

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
    #word_dict = test_create_word_cloud()
    endpoint1.update_wordcloud("Our employees really love working for us.")
    print("e1", endpoint1.wordcloud)
    print(endpoint1.wordcloud.raw())

    #word_dict = test_create_word_cloud()
    endpoint2.update_wordcloud("Frank frank")
    print(endpoint2.wordcloud)
    print(endpoint2.wordcloud.raw())

    '''you can add two wordclouds or append a dict to a wordcloud.  Mostly I think you will want to
    add wordclouds of the groups of enpoints that result from your analysis'''
    #word_dict = test_create_word_cloud()
    endpoint1.update_wordcloud("Are you sure about that employer employ employee?")
    print("--", endpoint1.wordcloud)
    wc = endpoint1.wordcloud+endpoint2.wordcloud
    print("wc", wc)
    print("e1", endpoint1.wordcloud)


if __name__ == "__main__":
    test_wc()
