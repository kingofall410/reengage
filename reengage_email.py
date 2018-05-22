import sys
import os
import copy
import logging
from datetime import datetime

from email_input import convert_enron, graph, mbox_parser

#defaults
options = {"infile":"",
    "convert":True,
    "conversion_out":"",
    "parse":True,
    "parse_out":"",
    "visualize":False,
    "debug":False}

###################################################################################################
#logging WILL NOT WORK in this function
def parse_commandline(cmdline):
    #remove module name
    cmdline.pop(0)

    #input file is required and must be first
    options['infile'] = cmdline.pop(0)

    #if inputfile ends with mbox, don't convert
    if options['infile'].endswith('.mbox'):
        options['convert'] = False
    elif options['infile'].endswith('.pickle'):
        options['convert'] = False
        options['parse'] = False

    while cmdline:

        #pull the - off the option string
        option = cmdline.pop(0)
        if option.startswith("-"):
            option = option[1:]
        else:
            print("Invalid option: ", option)
            break

        #parse options until one that needs a parameter
        for ch in option:

            if ch == 'c':
                #if this is the last option, look for a parameter
                if option.endswith(ch) and cmdline and not cmdline[0].startswith("-"):
                    options['conversion_out'] = cmdline.pop(0)

            if ch == 'p':
                #if this is the last option, look for a parameter
                if option.endswith(ch) and cmdline and not cmdline[0].startswith("-"):
                    options['parse_out'] = cmdline.pop(0)

            elif ch == 'v':
                options['visualize'] = True

            elif ch == 'd':
                options['debug'] = True

    return options

###################################################################################################
def list_directories(filename):
    print ([name for name in os.listdir(filename)])

###################################################################################################
def init_logging():
    dt = str(datetime.now()).replace(":", "_")
    formatter = '%(asctime)s - %(levelname)s - %(message)s'
    level = logging.DEBUG if options['debug'] else logging.INFO

    logging.basicConfig(filename="logs\\reengage_"+dt+".log", level=level,
                        format=formatter, datefmt='%m/%d/%Y %I:%M:%S %p')

    #logging tests
    logging.debug("debug")
    logging.info("info")
    logging.warning("warning")
    logging.critical("critical")

###################################################################################################
def main():

    #deepcopy commandlin since another module might need it
    cmdline = copy.deepcopy(sys.argv)
    #parse commandline before setting up logging in order to set debug levels
    parse_commandline(cmdline)
    init_logging()

    #see if the input file exists
    #TODO:This all needs refactor
    if os.path.exists(options['infile']):

        #extract name of file without extension
        name = options['infile'][(options['infile'].rfind("\\")+1):]
        name = name[name.rfind(".")+1:]

        if options['convert']:
            if not options['conversion_out']:
                options['conversion_out']="data\\"+name+".mbox"
                logging.info("Created conversion output file: %s", options['conversion_out'])

            convert_enron.convert(options['infile'], options['conversion_out'])

        if options['parse']:
            if not options['parse_out']:
                options['parse_out']="data\\"+name+".pickle"
                logging.info("Created parse output file: %s", options['parse_out'])

            parse_input = options['conversion_out'] if options['convert'] else options['infile']
            messages, eps = mbox_parser.parse(parse_input, options['parse_out'])
        else:
            messages, eps = mbox_parser.load_from_pickle(options['infile'])

        if (messages):
            graph.build_and_analyze(messages, eps, options['visualize'])
        else:
            errorStr = "FATAL: No messages found: "+parse_file
            print(errorStr)
            logging.critical(errorStr)

    else:
        errorStr = "FATAL: File not found: "+options['infile']
        print(errorStr)
        logging.critical(errorStr)
main()
