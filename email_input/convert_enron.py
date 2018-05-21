import re
import email
import sys
import os
import logging
from time import asctime
from dateutil.parser import parse # pip install python_dateutil
from datetime import datetime

from util import filter

###################################################################################################
def convert(maildir, outfilename):

    # Create a file handle that we'll be writing into...
    outfile = open(outfilename, 'w')
    msg_count = 0
    filtered_messages = 0
    # Walk the directories and process any folder named 'inbox'
    for (root, dirs, file_names) in os.walk(maildir):

        if root.split(os.sep)[-1].lower() != 'inbox':
            continue

        # Process each message in 'inbox'
        for file_name in file_names:
            file_path = os.path.join(root, file_name)
            message_text = open(file_path).read()

            # Compute fields for the From_ line in a traditional mbox message
            #change from \r to \n
            _from = re.search(r"From: ([^\n]+)", message_text).groups()[0]
            _date = re.search(r"Date: ([^\n]+)", message_text).groups()[0]

            logging.debug("From: %s, Date: %s", _from, _date)
            if not filter.filtermatch(_from.strip()):
                msg_count += 1

                #if (message_text.find("Fournace") >=0):
                #print(message_text)


                message_text = message_text.replace("\nFrom ", "\n>From")
                _date = asctime(parse(_date).timetuple())
                msg = email.message_from_string(message_text)
                msg.set_unixfrom('From %s %s' % (_from, _date))
                outfile.write(msg.as_string(unixfrom=True) + "\n\n")
            else:
                filtered_messages += 1

    logging.info("Conversion stats: %d messages converted, %d messages filtered",
                 msg_count, filtered_messages)
    outfile.close()
    return outfile


#run directly from commandline
#convert()
