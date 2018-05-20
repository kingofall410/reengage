import sys, os, copy, logging
from datetime import datetime

import convert_enron, graph, mbox_parser
from models import Endpoint, CustomHeader, Message

#defaults
options = {"infile":"",
    "convert":True,
    "conversion_out":"",
    "visualize":False,
    "parse":False,
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

            if ch == 'o':
                #if this is the last option, look for a parameter
                if option.endswith(ch) and cmdline and not cmdline[0].startswith("-"):
                    options['conversion_out'] = cmdline.pop(0)

            elif ch == 'v':
                options['visualize'] = True

            elif ch == 'p':
                options['parse'] = True

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

    if options['convert']:
        if not options['conversion_out']:
            name = options['infile'][(options['infile'].rfind("\\")+1):]
            options['conversion_out']="mbox\\"+name+".mbox"
            logging.info("Created output file: %s", options['conversion_out'])

        convert_enron.convert(options['infile'], options['conversion_out'])

    if options['parse']:
        parse_file = options['conversion_out'] if options['convert'] else options['infile']
        messages, eps = mbox_parser.parse(parse_file)
        print(len(messages))
        graph.build_and_analyze(messages, eps, options['visualize'])

main()
