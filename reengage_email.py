import sys, os
import convert_enron
import mbox_parser
import graph
import copy

from models import Endpoint, CustomHeader, Message

def parse_commandline(cmdline):
    #remove module name
    cmdline.pop(0)

    #defaults
    options = {"infile":"",
        "convert":False,
        "conversion_out":"",
        "visualize":False,
        "parse":False,
        "parse_out":""}

    #input file is required and must be first
    options['infile'] = cmdline.pop(0)

    while cmdline:
        print(cmdline)
        #pull the - off the option string
        option = cmdline.pop(0)
        if option.startswith("-"):
            option = option[1:]
        else:
            print("Invalid option: ", option)
            break

        #parse options until one that needs a parameter
        for ch in option:
            print(option)
            if ch == 'c':
                options['convert'] = True

                #if this is the last option, look for a parameter
                if option.endswith(ch) and cmdline and not cmdline[0].startswith("-"):
                    options['conversion_out'] = cmdline.pop(0)

            elif ch == 'v':
                options['visualize'] = True

            elif ch == 'p':
                options['parse'] = True

                #if this is the last option, look for a parameter
                if option.endswith(ch) and cmdline and not cmdline[0].startswith("-"):
                    options['parse_out'] = cmdline.pop(0)

    print(options)
    return options

def list_directories(filename):
    print ([name for name in os.listdir(filename)])

#deepcopy commandlin since another module might need it
cmdline = copy.deepcopy(sys.argv)
options = parse_commandline(cmdline)

if options['convert']:
    convert_enron.convert(options['infile'], options['conversion_out'])
if options['parse']:
    messages, eps = mbox_parser.parse(options['conversion_out'] if options['convert'] else options['infile'])
    graph.build_and_analyze(messages, eps, options['visualize'])
