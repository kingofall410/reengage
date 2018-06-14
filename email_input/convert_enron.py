import re
import email
import sys
import os
import logging
from time import asctime
from dateutil.parser import parse
from datetime import datetime

from util import filter, progress

###################################################################################################
def find_stupid_index(message, start):
    stupid_index = -1
    is_fb = None

    fbindex = message.find("-- Forwarded by", start)
    omindex = message.find("--Original Message", start)
    if fbindex > -1 and omindex > -1:
        if fbindex < omindex:
            stupid_index = fbindex
            is_fb = True
        else:
            stupid_index = fbindex
            is_fb = False
        stupid_index = min(fbindex, omindex)
    elif fbindex > -1:
        stupid_index = fbindex
        is_fb = True
    elif omindex > -1:
        stupid_index = omindex
        is_fb = False

    return is_fb, stupid_index

###################################################################################################
def find_embedded_messages(message):
    messages = []
    start = 0

    is_fb, theindex = find_stupid_index(message, start)
    while theindex > -1:
        #find the following blank line
        if is_fb:
            stop = message.find("\n\n", theindex)
        else:
            stop = message.find("\n", theindex)

        #capture the message text
        if stop > -1:
            messages.append(message[start:stop])
            start = stop+1
        else:
            messages.append(message[start:])
            start = len(message)

        is_fb, theindex = find_stupid_index(message, start)

    #capture the final message
    if not start == len(message):
        messages.append(message[start:len(message)])


    logging.debug("Message: (%s), %s", len(messages), messages)
        
    return messages

###################################################################################################
def process_root_message(message_text, outfile):
    success = False
    # Compute fields for the From_ line in a traditional mbox message
    #change from \r to \n
    _from = re.search(r"From: ([^\n]+)", message_text).groups()[0]
    _date = re.search(r"Date: ([^\n]+)", message_text).groups()[0]

    logging.debug("From: %s, Date: %s", _from, _date)
    if not filter.filter(_from.strip(), "mail"):
        success = True

        message_text = message_text.replace("\nFrom ", "\n>From ")
        _date = asctime(parse(_date).timetuple())
        msg = email.message_from_string(message_text)

        msg.set_unixfrom('From %s %s' % (_from, _date))
        outfile.write(msg.as_string(unixfrom=True) + "\n\n")

    return success

###################################################################################################
def process_sub_message(message_text, outfile):
    return False

###################################################################################################
def convert(maildir, outfilename, is_full):

    # Create a file handle that we'll be writing into...
    outfile = open(outfilename, 'w')
    msg_count = 0
    filtered_messages = 0

    # Walk the directories and process any folder named 'inbox'
    for (root, dirs, file_names) in os.walk(maildir):

        progress.write(msg_count+filtered_messages, 0, "Convert enron")
        if (not is_full) and (root.split(os.sep)[-1].lower() != 'inbox'):
            continue

        # Process each message in 'inbox'
        for file_name in file_names:
            file_path = os.path.join(root, file_name)
            message_text = open(file_path).read()

            messages = find_embedded_messages(message_text)
            #message 0 will always be the root message
            #don't rely on presence of headers because some responses also have full headers
            if process_root_message(messages[0], outfile):
                msg_count += 1
            else:
                filtered_messages += 1

            #now process sub-messages where header info may be incomplete
            for message in messages[1:]:
                if process_sub_message(message, outfile):
                    msg_count += 1
                else:
                    filtered_messages += 1


    progress.write(msg_count+filtered_messages, msg_count+filtered_messages, "Convert enron", True)
    statstring = "Conversion stats: "+str(msg_count)+" messages converted, "+str(filtered_messages)+" messages filtered"
    logging.info(statstring)
    print(statstring)
    outfile.close()
    return outfile


#run directly from commandline
#convert()
