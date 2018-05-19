import mailbox, re, random, logging
import dateutil.parser
from models import Endpoint, CustomHeader, Message

################################################################################
def parse_endpoints(endpoint_string):
    if (endpoint_string):
        #split the individual recipients based on commas not inside quotes
        endpoint_strings = re.split(',(?=(?:[^"]*"[^"]*")*[^"]*$)', endpoint_string)

        #match each recipient's email address and name
        #TODO:these fail if there's no email address, needs fixed
        try:
            endpoint_addresses = [re.search("[\w\.'-]+@[\w\.-]+\.\w+", str).group().strip() for str in endpoint_strings]
            endpoint_names = [re.match('([^<]+)', str).group(0).strip('" \n\t') for str in endpoint_strings]
        except(AttributeError):
            return None,None
        #print("----------------------------------")
        #print(endpoint_strings)
        #print("Parsed Addresses:", endpoint_addresses)
        #print("Parsed Names:", endpoint_names)
        return endpoint_addresses, endpoint_names
    else:
        return None, None

################################################################################
def parse(filename='..\\data\\enron\\processed\\small.mbox'):

    messages = []
    endpoints = []

    input = mailbox.mbox(filename)
    for message in input:

        #see if it has a From, if not it's a bad mbox, just skip for now
        if (message['From']):

            #Create Sender Endpoint
            sender_add, sender_name = parse_endpoints(  message['From'])
            if (sender_add and sender_name):

                sender = Endpoint.get_or_create(endpoints, sender_add[0], sender_name[0])

            #Create Message object
            id = message['Message-ID']
            if (id):
                logging.debug("********* "+id)
            else:
                logging.debug("********* "+str(message))

            subject = message['Subject']
            date = dateutil.parser.parse(message['Date'])
            body = message.get_payload()
            mess = Message(id=id, sender=sender, subject=subject, datetime=date, body=body, flatmbox=str(message))

            #Add receiver Endpoints
            recipients_add, recipients_name = parse_endpoints(message['To'])
            if (recipients_add and recipients_name):
                for (recipient_add, recipient_name) in zip(recipients_add, recipients_name):

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

    return messages, endpoints
