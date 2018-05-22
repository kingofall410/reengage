import mailbox
import re
import random
import logging
import pickle
from util import filter
import dateutil.parser

from email_input.models import Endpoint, CustomHeader, Message

################################################################################
def parse_endpoints(endpoint_string):
    if (endpoint_string):
        #split the individual recipients based on commas not inside quotes
        endpoint_strings = re.split(',(?=(?:[^"]*"[^"]*")*[^"]*$)', endpoint_string)

        #match each recipient's email address and name
        #TODO:these fail if there's no email address, needs fixed
        try:
            endpoint_addresses = [re.search("[\w\.'-]+@[\w\.-]+\.\w+", str).group().strip()
                                  for str in endpoint_strings]
            endpoint_names = [re.match('([^<]+)', str).group(0).strip('" \n\t')
                              for str in endpoint_strings]
        except(AttributeError):
            return None,None

        logging.debug("Parsed Addresses: %s", endpoint_addresses)
        logging.debug("Parsed Names: %s", endpoint_names)

        return endpoint_addresses, endpoint_names
    else:
        return None, None

###################################################################################################
def parse(infile, outfile):

    messages = []
    endpoints = []
    bad_message_count = 0
    filtered_message_count = 0
    input = mailbox.mbox(infile)
    output = open(outfile, 'wb')

    logging.info("Parser stats: %d Input Messages", len(input))
    for message in input:

        #see if it has a From, if not it's a bad mbox, just skip for now
        if (message['From']):

            id = message['Message-ID']
            if (id):
                logging.debug("------Found message: %s", id)
            else:
                logging.warning("------No message ID found: %s", str(message))

            sender_add, sender_name = parse_endpoints(message['From'])
            recipients_add, recipients_name = parse_endpoints(message['To'])

            #filter out based on from/to
            filtered_senders = filter.filter_list(sender_add)
            filtered_recipients = filter.filter_list(recipients_add)

            if filtered_senders and filtered_recipients:

                #create sender endpoint
                sender = Endpoint.get_or_create(endpoints, sender_add[0], sender_name[0])

                #Create Message object
                subject = message['Subject']
                date = dateutil.parser.parse(message['Date'])
                body = message.get_payload()
                mess = Message(id=id, sender=sender, subject=subject, datetime=date, body=body,
                               flatmbox=str(message))

                #create and add receiver Endpoints
                if (recipients_add and recipients_name):
                    for (recipient_add, recipient_name) in zip(recipients_add, recipients_name):
                        if recipient_add in filtered_recipients:
                            receiver = Endpoint.get_or_create(endpoints, recipient_add, recipient_name)
                            mess.addRecipient(receiver)

                #get all custom headers and save as strings
                headers = message.items()
                for header in headers:
                    if (header[0].startswith('X') or header[0].startswith('x')):
                        ch = CustomHeader(header_key=header[0], header_value=header[1])
                        mess.addCH(ch)

                #add to the list
                messages.append(mess)
                logging.debug("------Message objects added")
            else:
                filtered_message_count += 1
                logging.debug("------Message objects not created")
        else:
            bad_message_count +=1

    logging.info("Parser stats: %d Message objects created, %d bad messages, %d filtered messages",
                 len(messages), bad_message_count, filtered_message_count)

    pickle.dump((messages, endpoints), output)
    output.close()

    return messages, endpoints

def load_from_pickle(filename):
    input = open(filename, 'rb')
    return pickle.load(input)
