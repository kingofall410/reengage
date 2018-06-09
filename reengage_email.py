import sys
import os
import copy
import logging
from datetime import datetime

from email_input import convert_enron, graph, mbox_parser, models


#defaults
options = {"infile":"",
    "convert":True,
    "conversion_out":"",
    "parse":True,
    "parse_out":"",
    "visualize":False,
    "debug":False,
    "inbox_only":False,
    "watsoning":False}

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

            elif ch == 'i':
                options['inbox_only'] = True

            elif ch == 'w':
                options['watsoning'] = True

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
def init_file_structure():
    if not os.path.exists("data"):
        os.makedirs("data")

    if not os.path.exists("logs"):
        os.makedirs("logs")

###################################################################################################
def extract_dataset_name():
    #extract name of file without extension
    name = options['infile'][(options['infile'].rfind("\\")+1):]
    dot_index = name.rfind(".")
    if dot_index >= 0:
        name = name[:dot_index]
    logging.info("Using dataset name: %s", name)
    return name

###################################################################################################
def convert(dataset_name, convert_input):

    convert_output = ""

    #if we actually need to convert
    if options['convert']:
        logging.info("Starting conversion")
        #if the user has not specified a specific output filename
        if options['conversion_out']:
            convert_output = options['conversion_out']
            logging.info("Using conversion output file: %s", convert_output)
        else:
            convert_output = "data\\"+dataset_name+".mbox"
            logging.info("Created conversion output file: %s", convert_output)

        convert_enron.convert(convert_input, convert_output, not options['inbox_only'])
    else:
        logging.info("Skipping conversion")
        convert_output = convert_input

    return convert_output

###################################################################################################
def parse(dataset_name, parse_input):

    parse_output = ""

    #if we actually need to parse
    if options['parse']:
        logging.info("Starting parse")
        #if the user has not specified a specific output filename
        if options['parse_out']:
            parse_output = options['parse_out']
            logging.info("Using parse output file: %s", parse_output)
        else:
            parse_output = "data\\"+dataset_name+".pickle"
            logging.info("Created parse output file: %s", parse_output)

        messages, eps = mbox_parser.parse(parse_input, parse_output)
    else:
        logging.info("Loading from pickle")
        messages, eps = mbox_parser.load_from_pickle(parse_input)

    return messages, eps

###################################################################################################
def analyze(messages, dataset_name, eps, is_vis, watsoning):

    if (messages):
        watson_filename = None
        if watsoning:
            watson_filename = 'data\\'+dataset_name+'_watson.csv'

        graph.build_and_analyze(messages, eps, is_vis, watson_filename)
    else:
        errorStr = "FATAL: No messages found: "+parse_file
        print(errorStr)
        logging.critical(errorStr)

###################################################################################################
def main():
    #deepcopy commandlin since another module might need it
    cmdline = copy.deepcopy(sys.argv)

    init_file_structure()
    #parse commandline before setting up logging in order to set debug levels
    parse_commandline(cmdline)
    init_logging()

    #see if the input file exists
    if os.path.exists(options['infile']):

        dataset_name = extract_dataset_name()

        convert_filename = options['infile']
        parse_filename = convert(dataset_name, convert_filename)
        messages, eps = parse(dataset_name, parse_filename)

        analyze(messages, dataset_name, eps, options['visualize'], options['watsoning'])

    else:
        errorStr = "FATAL: File not found: "+options['infile']
        print(errorStr)
        logging.critical(errorStr)

def test():
    models.test_wc()
    
main()
#test()
