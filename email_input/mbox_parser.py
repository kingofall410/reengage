import mailbox
import re
import random
import logging
import operator
import pickle
from util import filter, progress
import dateutil.parser

from email_input.models import Endpoint, Message

################################################################################
def parse_xfrom(xfrom_string):
    endpoint_name = None

    if xfrom_string:
        try:
            endpoint_name = re.match('([^<]+)', xfrom_string).group(0).strip('" \n\t')
            logging.debug("Parsed X-From: %s", endpoint_name)
        except AttributeError:
            logging.warning("Couldn't parse X-From: %s", xfrom_string)

    return endpoint_name

################################################################################
def parse_xto(xto_string):
    endpoint_names = None

    if xto_string:
        #if it has an @, I don't care, it's either outside the company or an email address I presumably already have
        if xto_string.find('@') < 0:
            #otherwise it's a list of names separated by commas or
            #a list of "Name <gobbledygook>" separated by commas
            xto_strings = None

            if xto_string.find("<") >= 0:
                xto_strings = re.split('>,', xto_string)
            else:
                xto_strings = re.split(',', xto_string)

            endpoint_names = [re.match('([^<]+)', str).group(0).strip('" \n\t')
                              for str in xto_strings]

        logging.debug("Parsed X-To: %s", endpoint_names)

    return endpoint_names

################################################################################
def parse_endpoints(endpoint_string, split_commas=True):
    endpoint_addresses = None
    endpoint_names = None
    if not split_commas:
        logging.debug("xfrom %s", endpoint_string)

    if endpoint_string:
        if split_commas:
            #split the individual recipients based on commas not inside quotes
            endpoint_strings = re.split(',(?=(?:[^"]*"[^"]*")*[^"]*$)', endpoint_string)
        else:
            endpoint_strings = [endpoint_string]

        #match each recipient's email address and name
        #TODO:these fail if there's no email address, needs fixed
        try:
            endpoint_addresses = [re.search("[\w\.'-]+@[\w\.-]+\.\w+", str).group().strip()
                                  for str in endpoint_strings]
        except(AttributeError):
            pass

        try:
            endpoint_names = [re.match('([^<]+)', str).group(0).strip('" \n\t')
                              for str in endpoint_strings]
        except(AttributeError):
            pass

        logging.debug("Parsed Addresses: %s", endpoint_addresses)
        logging.debug("Parsed Names: %s", endpoint_names)

        return endpoint_addresses, endpoint_names
    else:
        return None, None

###################################################################################################
def parse(infile, outfile):
    
    #messages_by_endpoint is a mapping of email address to (endpoint, [messages])
    messages_by_endpoint = dict()
    bad_message_count = 0
    filtered_message_count = 0
    input = mailbox.mbox(infile)
    output = open(outfile, 'wb')
    counter = 0
    logging.info("Parser stats: %d Input Messages", len(input))
    for message in input:

        counter = counter+1
        progress.write(counter, len(input), "Parse mbox")

        #see if it has a From, if not it's a bad mbox, just skip for now
        if (message['From']):

            id = message['Message-ID']
            if not id:
                logging.warning("------No message ID found: %s", str(message))

            sender_add, sender_name = parse_endpoints(message['From'])
            recipients_add, recipients_name = parse_endpoints(message['To'])
            xfrom_name = parse_xfrom(message['X-From'])
            xto_names = parse_xto(message['X-To'])

            #filter out based on from/to
            #TODO: why doesn't my constant work here?
            filtered_senders = filter.filter_list(sender_add, "mail")
            filtered_recipients = filter.filter_list(recipients_add, "mail")

            if filtered_senders and filtered_recipients:
                name = sender_name[0] if sender_name else None
                try:
                    sender_tuple = Endpoint.get_or_create(messages_by_endpoint, sender_add[0], 
                                                          name, xfrom_name)
                except (TypeError):
                    print(message)
                    exit()

                #Create Message object
                subject = message['Subject']
                date = dateutil.parser.parse(message['Date'])
                #right now I don't even care about message body
                body = ""
                '''body = message.get_payload()
                print("Body type:", type(body), "message is mp", message.is_multipart())
                if message.is_multipart():
                    print(message)
                    for (i, part) in enumerate(body):
                        print("******************part", i, "type", type(part), "payload type:", type(part.get_payload()))
                        print(part)
                    body = body[0].get_payload()
                    
                sender_tuple[0].update_wordcloud(body)'''

                mess = Message(id=id, sender=sender_tuple[0], subject=subject, datetime=date, 
                               body=body)

                #create and add receiver Endpoints
                if (recipients_add and recipients_name):
                    for (i, (recipient_add, recipient_name)) in enumerate(zip(recipients_add, recipients_name)):
                        if recipient_add in filtered_recipients:
                            xto_name = None
                            if xto_names and len(xto_names) > i:
                                xto_name = xto_names[i]

                            receiver_tuple = Endpoint.get_or_create(messages_by_endpoint, recipient_add, 
                                                                    recipient_name, xto_name)
                            mess.addRecipient(receiver_tuple[0])                

                #add to the list
                sender_tuple[1].append(mess)

                logging.debug("------Message objects added")
            else:
                filtered_message_count += 1
                logging.debug("------Message objects not created")
        else:
            bad_message_count +=1
    progress.write(counter, len(input), "Parse mbox", True)
    logging.info("Parser stats: %d Message objects created, %d bad messages, %d filtered messages",
                 counter-bad_message_count-filtered_message_count, bad_message_count, filtered_message_count)

    pickle.dump(messages_by_endpoint, output)
    output.close()

    return messages_by_endpoint

def load_from_pickle(filename):
    input = open(filename, 'rb')
    return pickle.load(input)
