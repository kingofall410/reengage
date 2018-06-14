import logging

class FilterSet():
    def __init__(self, filename=""):
        self.filename = filename
        self.initialized = False
        self.filters = {'negative': [], 'positive': []}

    def parse_filter_config(self):
        filter_file = open(self.filename)

        for line in filter_file:
            if not line.startswith('#'):

                line = line.strip("\n\r ")
                if line.startswith('+'):
                    self.filters['positive'].append(line.strip("+"))
                elif line:
                    self.filters['negative'].append(line)

        filter_file.close()

        logging.debug("%s Filters: %s", id, str(self.filters))

        self.initialized = True

###################################################################################################
    def filter(self, source):

        if not self.initialized:
            self.parse_filter_config()

        #TODO: this is slow
        for filter in self.filters['negative']:
            if (filter.startswith('*') and source.endswith(filter[1:])) \
               or source == filter:
                #logging.debug("Negative match filtered out: %s (%s)", source, filter)
                return True

        for filter in self.filters['positive']:
            if not (filter.startswith('*') and source.endswith(filter[1:])) \
               and not source == filter:
                #logging.debug("Positive match failure filtered out: %s (+%s)", source, filter)
                return True

        return False


filter_dict = {}
MAIL_FITLER = "mail"
WORD_FITLER = "word"
filter_dict[MAIL_FITLER] = FilterSet("config\\email_filters.cfg")
filter_dict[WORD_FITLER] = FilterSet("config\\wordcloud_filters.cfg")

###################################################################################################
def filter(source, id):
    if id in filter_dict:
        return filter_dict[id].filter(source)
    else:
        logging.warning("Filter ID not found: %s", id)
        return False

###################################################################################################
def filter_list(sources, id):
    return_sources = []
    if sources:
        if id in filter_dict:
            return_sources = [source for source in sources if not filter_dict[id].filter(source)]
        else:
            logging.warning("Filter ID not found: %s", id)
            return_sources = sources

    return return_sources
