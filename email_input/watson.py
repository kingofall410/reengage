import csv, re, logging, json, pprint

from util import progress

from watson_developer_cloud import NaturalLanguageUnderstandingV1
from watson_developer_cloud.natural_language_understanding_v1 import Features, EntitiesOptions, KeywordsOptions, SentimentOptions, EmotionOptions
from watson_developer_cloud import watson_service

nlu = None
###################################################################################################
def init_watson():
    global nlu

    edwin_username = '2ba9c82d-4590-4d77-ae45-d3988afb5446'
    edwin_password = 'JWCDPbtBBX1v'
    dan_username = 'd118a5d0-81bd-4577-a17d-30dcdfcbc44b'
    dan_password = '0szZ7vYY3ptT'

    nlu = NaturalLanguageUnderstandingV1(username=dan_username, password=dan_password,
                                         version='2018-03-16')

###################################################################################################
def extract_sender_messages(graph_group, messages):
    group_messages = dict()
    for m in messages:
        if m.sender in graph_group:
            if m.sender in group_messages:
                group_messages[m.sender].append(m)
            else:
                group_messages[m.sender] = [m]
    return group_messages
###################################################################################################
def watson_request(message):

    return_dict = {"sentiment": None,
                   "emotion": None}
    sentiment=SentimentOptions()
    emotion=EmotionOptions()
    features = Features(sentiment=sentiment, emotion=emotion)
    #features = Features(entities=EntitiesOptions(emotion=True, sentiment=True, limit=2))

    try:
        response = nlu.analyze(text=message, features=features)
        #pp = pprint.PrettyPrinter(indent=4)
        #pp.pprint(response)

        if response["sentiment"]:
            return_dict["sentiment"] = response["sentiment"]["document"]

        if response["emotion"]:
            return_dict["emotion"] = response["emotion"]["document"]["emotion"]

    except watson_service.WatsonApiException:
        logging.warning("Couldn't watson message: %s", message)

    return return_dict

###################################################################################################
def run_watson(graph, messages, watson_filename, messages_per_person=10):

    group_messages = extract_sender_messages(graph, messages)
    nr_senders = len(group_messages)

    nlu = init_watson()
    with open(watson_filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, dialect='excel', quoting=csv.QUOTE_ALL)
        writer.writerow(["Sender", "Message Body", "General Sentiment",
                         "Anger", "Disgust", "Fear", "Joy", "Sadness"])

        for (i, sender) in enumerate(group_messages):
            for (j, message) in enumerate(group_messages[sender]):
                progress.write(i, nr_senders, "Watsoning")

                #only passing the first 10 messages per person
                if j >= messages_per_person:
                    break

                logging.debug('Name: %s', message.sender.name)
                #name = re.sub('[\s+]','', message.sender.name)
                body = re.sub('[\s+]','%20',message.body)

                response = watson_request(message.body)
                #pp = pprint.PrettyPrinter(indent=4)
                #pp.pprint(response)
                writer.writerow([message.sender, message.body, response["sentiment"]["score"],
                                 response["emotion"]["anger"],response["emotion"]["disgust"],
                                 response["emotion"]["fear"],response["emotion"]["joy"],
                                 response["emotion"]["sadness"]])

        progress.write(nr_senders, nr_senders, "Watsoning", True)
