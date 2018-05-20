import logging

FILTER_FILENAME="filters.cfg"
filters = {'negative': [], 'positive':[]}
initialized = False
###################################################################################################
def parse_filter_config():
    global initialized, filters

    filter_file = open(FILTER_FILENAME)

    for line in filter_file:
        if not line.startswith('#'):

            line = line.strip("\n\r ")
            if line.startswith('+'):
                filters['positive'].append(line.strip("+"))
            elif line:
                filters['negative'].append(line)

    filter_file.close()

    logging.debug("Filters: %s", str(filters))

    initialized = True

    return filters

###################################################################################################
def filtermatch(source):
    global initialized, filters

    if not initialized:
        parse_filter_config()

    #TODO: this is slow
    for filter in filters['negative']:
        if source.endswith(filter):
            logging.debug("Negative match filtered out: %s (%s)", source, filter)
            return True

    for filter in filters['positive']:
        if not source.endswith(filter):
            logging.debug("Positive match failure filtered out: %s (+%s)", source, filter)
            return True

    return False
