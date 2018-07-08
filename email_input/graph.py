import logging, random
import subprocess as sp
import networkx as nx
import re, json, numpy as np
from collections import defaultdict
from email_input.models import WordCloud
from . import watson
from email_input import models
import nltk
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt


data = {"nodes": [], "edges": [], "groups": {}, "cliqueDefinitions": []}

###################################################################################################
def build_graph(messages_by_ep, is_show_graph):
    G = nx.DiGraph()

    for (endpoint, messages) in messages_by_ep.values():
        G.add_node(endpoint)

        for message in messages:
            for receiver in message.receivers:
                if not G.has_edge(message.sender, receiver):
                    G.add_edge(message.sender, receiver, weight = 0)
                G[message.sender][receiver]['weight'] += 1

    if is_show_graph:
        nx.draw(G, with_labels=True)
        plt.show()
    return G

###################################################################################################
#TODO: Probably a more pythonic way to do this when I'm thinking clearly
def total_edge_weight(graph, from_node, to_nodes):
    result = 0
    for node in to_nodes:
        if graph.has_edge(from_node, node):
            result += graph[from_node][node]['weight']
        if graph.has_edge(node, from_node):
            result += graph[node][from_node]['weight']
    return result

###################################################################################################
#TODO: Probably a more pythonic way to do this when I'm thinking clearly
def connectedness_kpi(graph, from_node, to_nodes):
    #this method determines the criteria for adding nodes to a group
    #for each distinct subgraph, what do we consider a 'group of friends'?
    #1) you need to be sending and receiving email to/from the group members at a significant volume
    #2) you can't just get that volume from/to a small subset of the group

    #Suppose to_nodes has 10 people, and percentile is set to .3
    #Then I'm looking at the amount of email I'm sending to the person in the group I send the 3rd most email to.
    #Same story for the email I'm receiving.
    #Then KPI is the minimum of those 2 numbers.
    #So increasing the percentile influences how many people you need to be communicating with in the group
    #then in the main method below, there is a cutoff for how high this KPI needs to be before I add the person.
    percentile = 0.5
    send_results = []
    receive_results = []
    send_result = 0
    receive_result = 0
    measure_level = int(percentile * len(to_nodes))
    for node in to_nodes:
        if graph.has_edge(from_node, node):
            send_results.append(graph[from_node][node]['weight'])
        if graph.has_edge(node, from_node):
            receive_results.append(graph[node][from_node]['weight'])
    if measure_level < len(send_results):
        send_result = send_results[measure_level]
    if measure_level < len(receive_results):
        receive_result = receive_results[measure_level]
    result = min(send_result, receive_result)
    return result

###################################################################################################
def find_candidate(graph, group, candidates, is_remove):
    #this method determines who the best candidate to add/remove is
    #if is_remove, candidates needs to be subset of group
    if not is_remove:
        #edwincheckwinner = sorted(candidates, key=lambda x: (connectedness_kpi(graph, x, group), x.name), reverse= not is_remove)[0]
        winner = sorted(candidates, key=lambda x: (connectedness_kpi(graph, x, group), x.address), reverse= not is_remove)[0]
        score = connectedness_kpi(graph, winner, group)
    else:
        #edwincheckwinner = sorted(candidates, key=lambda x: (connectedness_kpi(graph, x, group - {x}), x.name), reverse= not is_remove)[0]
        winner = sorted(candidates, key=lambda x: (connectedness_kpi(graph, x, group - {x}), x.address), reverse= not is_remove)[0]
        score = connectedness_kpi(graph, winner, group - {winner})
    return winner, score

###################################################################################################
def top_communicators(graph):
#how connected is this graph really. Is there 2 way communication, what are reasonable amounts.
    values = list()
    for node in graph.nodes:
        for nb_node in set(nx.all_neighbors(graph, node)):

            #edwincheckif nb_node.name > node.name:
            if nb_node.address > node.address:
                from_value = 0
                if(graph.has_edge(node, nb_node)):
                    from_value += graph[node][nb_node]['weight']
                to_value = 0
                if(graph.has_edge(nb_node, node)):
                    to_value += graph[nb_node][node]['weight']
                value = min(from_value, to_value)
                if value > 0:
                    values.append(value)
    top_values = sorted(filter( lambda x: x > 100, values), reverse = True)
    logging.info('Top communicators: ')
    logging.info(top_values)

###################################################################################################
def basic_graph_stats(graph):
    #goal is to explain the total amount of emails with as simple a structure as possible.
    #so first assess how many emails we have in total
    total_edges_weight = graph.size(weight = 'weight')
    total_number_edges = graph.size()
    logging.info("Total number of edges is %s with a total weight of %s", str(total_number_edges), 
                 str(total_edges_weight))
    #let's see what the heaviest edges are
    edge_list = sorted(list(graph.edges), key=lambda x: graph[x[0]][x[1]]['weight'], reverse=True)
    for i in range(0,100):
        edge = edge_list[i]
        logging.debug("Edge from %s to %s has weight %s", edge[0], edge[1], 
                      graph[edge[0]][edge[1]]['weight'])

###################################################################################################
def build_unidir_graph(full_graph, two_way_email_threshold):
    #To find groups, adjust the bidirectional graph into a unidirectional graph, weight on the edge is minimum of both directions
    #then find subgraphs that are fully connected, or even just weakly connected components
    reg_graph = nx.Graph()
    for node in full_graph.nodes:
        reg_graph.add_node(node)
        for nb_node in nx.all_neighbors(full_graph, node):
            #edwincheckif node != nb_node and nb_node.name > node.name:edwincheck
            if node != nb_node and nb_node.address > node.address:
                if full_graph.has_edge(node, nb_node) and full_graph.has_edge(nb_node, node):
                    value = min(full_graph[node][nb_node]['weight'],full_graph[nb_node][node]['weight'])
                    if value >= two_way_email_threshold:
                        reg_graph.add_edge(node, nb_node, weight = value)

    logging.debug('Built undirected graph with %s nodes and %s edges', len(reg_graph.nodes), 
                  len(reg_graph.edges))
    for element in reg_graph.edges:
        logging.debug('Edge from %s to %s', element[0].address, element[1].address)

    return reg_graph

###################################################################################################
def extract_sender_messages(graph_group, messages_by_ep):
    group_messages = dict()

    for sender in graph_group:
        receivers = set(graph_group)
        receivers.remove(sender)
        logging.debug("%s", sender.address)
        #find the sender's entry in m_b_e
        sender_tuple = messages_by_ep[sender.address]

        #find all sender's messages that include a recipient in this group
        senders_intra_group_messages = [m for m in sender_tuple[1] 
                                        if receivers == set(m.receivers)]
        
        #add to dict
        group_messages[sender] = senders_intra_group_messages

        for message in senders_intra_group_messages:
            logging.debug("   %s", message.body)

    return group_messages
###################################################################################################   
def find_cliques(full_graph, threshhold = 100):
    reg_graph = build_unidir_graph(full_graph, threshhold)
    #find distinct cliques
    cliques = list(nx.find_cliques(reg_graph))
    logging.debug('Cliques: ')
    for i,clique in enumerate(cliques):
    	if len(clique) > 1:logging.debug('Size of clique %s is %s. Members are: %s', str(i), len(clique),([x.address for x in clique]))
    biggest_clique = max(nx.find_cliques(reg_graph), key= len)
    logging.info('Size of biggest clique is %s. Members are: %s', len(biggest_clique), 
                 ([x.address for x in biggest_clique]))
    
    return cliques, biggest_clique
###################################################################################################   
def find_cliques_replies_to_all(messages_by_ep, graph_clique_creation_filter = {'min_clique_bidirectional_comm': 1}):
    #['eric.bass@enron.com', 'brian.hoskins@enron.com', 'lenine.jeganathan@enron.com', 'hector.campos@enron.com'] => weight 6
    #['leslie.hansen@enron.com', 'tana.jones@enron.com'] => weight 132
    min_clique_bidirectional_comm = graph_clique_creation_filter.get('min_clique_bidirectional_comm', 1)
    cliquedict = {}
    for (endpoint, messages) in messages_by_ep.values():
        logging.debug('Endpoint %s', endpoint.address)
        for message in messages:
            groupset = set(message.receivers)
            groupset.add(message.sender)
            allpeople = frozenset(groupset)
            if not allpeople in cliquedict:
                cliquedict[allpeople] = {}
            if not message.sender in cliquedict[allpeople].keys():
                cliquedict[allpeople][message.sender] = 1
            else:
                cliquedict[allpeople][message.sender] = cliquedict[allpeople][message.sender] + 1
                           
    group_comm_dict = {}
    for (group, senders) in cliquedict.items():
        if (len(senders) == len(group)) and len(group) > 1:
            group_comm_dict[group] = dict()
            group_comm_dict[group]['value'] = min([value for value in senders.values()])
            group_comm_dict[group]['information_text'] = "\n".join([mem.address for mem in senders])
            logging.debug('Dict has values of %s for members %s',[cliquedict[group].values()], [mem.address for mem in senders])
    
    return group_comm_dict
###################################################################################################
def word_cloud(group_messages):
    #word clouding
    # #create a dict that maps sender to their wordcloud of messages sent to this group
    group_wordcloud = defaultdict(models.WordCloud)
    for (i, sender) in enumerate(group_messages):
        #create a list of message bodies for this sender
        print('wordclouding messages: ' + str(len(group_messages[sender])))
        message_bodies = [m.body for m in group_messages[sender]]
        group_wordcloud[sender].append(message_bodies)
        nr = 10
        logging.info('Cloud for sender %s has length %s', sender.address, len(group_wordcloud[sender]))
        logging.info('Cloud top %s for sender %s: %s', nr, sender.address, group_wordcloud[sender].topX(nr))
    return group_wordcloud
###################################################################################################
def out_to_json(filename):
    global data
    if filename:
        with open(filename, 'w') as outfile:
            json.dump(data, outfile)
    
###################################################################################################
def prepare_graph_for_visualization(personal_graph, focal_endpoint, focal_cliques, graph_visual_filter):
    logging.debug('Preparing the visualization building blocks for a graph with %s nodes', len(personal_graph[focal_endpoint]))
    #read filterset
    draw_edges_to_self = graph_visual_filter.get('draw_edges_to_self', False)
    max_nodes = graph_visual_filter.get('max_nodes', 100)
    is_display_fringe_edges = graph_visual_filter.get('is_display_fringe_edges', False)

    vis_graph = nx.DiGraph()
    vis_graph.add_node(focal_endpoint, node_tooltip = 'node-tooltip')
    #NODES
    #select the top max_nodes nodes to display
    node_list = [node for node in personal_graph[focal_endpoint] if node != focal_endpoint]
    sorted_filtered_node_list = sorted(node_list, key = lambda x: personal_graph.get_edge_data(x, focal_endpoint, default={'weight': 0})['weight'] + personal_graph.get_edge_data(focal_endpoint, x, default={'weight': 0})['weight'], reverse = True)[:max_nodes]
    for node in sorted_filtered_node_list:
        if focal_endpoint in personal_graph[node]:
            emails_to_focal = personal_graph[node][focal_endpoint]['weight']
        else:
            emails_to_focal = 0
        try:
            node_weight = sum([personal_graph[node][neighb]['weight'] for neighb in personal_graph[node] if neighb != node])
            node_tooltip = "<br>".join([node.names[0], "Email: " + node.address, "Total sent emails: " + str(node_weight),
                                        "   Emails from focal: " + str(personal_graph[focal_endpoint][node]['weight']),
                                        "   Emails to focal: " + str(emails_to_focal)])
            logging.debug('Creating node with tooltip %s', node_tooltip)
        except TypeError:   
            logging.error("Can't create tooltip for node %s", node.address)    
            node_tooltip = 'Type Error in creation'
        vis_graph.add_node(node, node_tooltip = node_tooltip)       
    
    #EDGES
    weight_list = [personal_graph[focal_endpoint][neighb]['weight'] for neighb in personal_graph[focal_endpoint] if neighb != focal_endpoint]
    focal_node_weight = sum(weight_list)
    #making sure that we scale the edge weights correctly
    min_focal_node_weight = min(weight_list)
    max_focal_node_weight = max(weight_list)
    min_edge_weight = 1
    max_edge_weight = 5
    try:
        edge_weight_coef = (max_edge_weight - min_edge_weight) / (max_focal_node_weight - min_focal_node_weight)
    except ZeroDivisionError:
        edge_weight_coef = 1
    logging.debug('Edge scaling weights: total weight = %s, minimum = %s, max weight= %s',
                    str(focal_node_weight), str(min_focal_node_weight), str(max_focal_node_weight))
    for node in sorted_filtered_node_list:
        node_edge_weight = edge_weight_coef * (personal_graph[focal_endpoint][node]['weight'] - min_focal_node_weight) + min_edge_weight
        vis_graph.add_edge(focal_endpoint, node, vis_weight = node_edge_weight, weight = personal_graph[focal_endpoint][node]['weight'])
        if is_display_fringe_edges:
            for nb_node in vis_graph[node]:
                if draw_edges_to_self or nb_node != node:
                    vis_graph.add_edge(node, nb_node, vis_weight = min_edge_weight, weight = personal_graph[node][nb_node]['weight'])
    

    #CLIQUES
    sorted_filtered_cliques = sorted([clique for clique in focal_cliques if clique < set(vis_graph.nodes())], key=lambda x: focal_cliques[x]['value'], reverse = True)
    unsorted_dicts = {k: v for k,v in focal_cliques.items() if k < vis_graph.nodes()}
    return vis_graph, sorted_filtered_cliques, unsorted_dicts

###################################################################################################
def jsonify(vis_graph, focal_endpoint, filtered_cliques, unsorted_clique_dicts):
    global data
    logging.debug('JSONing a graph with %s nodes', len(vis_graph.nodes()))
    #create groups
    data["groups"] = {
                      "defaultGroup": {"color": {"background": "#97C2FCFF", "border":"97C2FCFF"}, "borderWidth":0},
                      "inactiveGroup": {"color": {"background": "#97C2FC88", "border":"97C2FC88"}, "borderWidth":0}
                     }
    #clique names, put anything you want in here, begin the string with an underscore, make sure they're unique
    #filter cliques to only use nodes in the top max_nodes of nodes (the nodes that are displayed)
    sorted_cliques = sorted(list(unsorted_clique_dicts.keys()), key=lambda x: unsorted_clique_dicts[x]['value'], reverse = True)
    data["cliqueDefinitions"] = [{
                "name": "_Clique "+str(i),
                "description": "Sentiment: " + str(unsorted_clique_dicts[sorted_cliques[i]]['sentiment']) + "|"
                                    + unsorted_clique_dicts[sorted_cliques[i]]['information_text'] + "\n "
                                    + unsorted_clique_dicts[sorted_cliques[i]]['wordcloud']
            } for i in range(len(sorted_cliques))]
    
    group_name_list = []
    for (i, clique_iter) in enumerate(sorted_cliques):
        #put anything you want in here, begin the string with an underscore, make sure they're unique
        group_name_list.append("_Clique "+ str(i) + ": " + " ;".join([node.address for node in clique_iter]))
        
    #draw other nodes
    for i,node in enumerate(vis_graph.nodes()):
            node_dict = {"id": node.address, "label": node.initials, "shape": "circle", 
                        "color":"#97C2FC", "title": vis_graph.node[node]['node_tooltip'], "group": "defaultGroup" }

            for i, clique_def in enumerate(data["cliqueDefinitions"]):
                node_dict[clique_def["name"]] = node in filtered_cliques[i]
            
            if node_dict not in data["nodes"]:
                data["nodes"].append(node_dict)
    
    #create edges, only the ones from the focal
    for (i,edge) in enumerate(vis_graph.edges()):
        #random limit
        from_node, to_node = edge[0], edge[1]
        if (i >= 1000):
            break
        logging.debug('Drawing edge from %s to %s with width %s', from_node.address, to_node.address, vis_graph[from_node][to_node]['vis_weight'])
        data["edges"].append({"from":from_node.address, "to":to_node.address, "color": {"color": "#97C2FC", "inherit": 'false'}, "arrows": "to",
                        "length": 100, "width": vis_graph[from_node][to_node]['vis_weight'],
                        "title": "Total emails: " + str(vis_graph[from_node][to_node]['weight']) + ". "})

###################################################################################################
def build_and_analyze(messages, visualize=False, watson_filename=None, json_filename=None):
    print('Progress | Start analyze')
    logging.info("Messages: %s", str(len(messages)))
    #filtersets that I'll use everywhere to filter stuff out to consolidate all filtering
    graph_clique_creation_filter = {'min_clique_bidirectional_comm': 1}
    graph_visual_filter = {'max_nodes': 100 , 'is_display_fringe_edges': True, 'draw_edges_to_self': False}
    
    full_graph = build_graph(messages, False)
    for node in full_graph:
        logging.debug('%s has %s neighbors', node.address, len(full_graph[node]))
    
    basic_graph_stats(full_graph)
    top_communicators(full_graph)
    cliques = find_cliques_replies_to_all(messages, graph_clique_creation_filter)
    #sorted_cliques is a list of just the keys sorted by value.
    sorted_cliques = sorted(list(cliques.keys()), key= lambda x: cliques[x]['value'], reverse = True)
    for cliq_item in sorted_cliques:
        logging.debug("Cliq members: %s, with value %s", ",".join([x.address for x in cliq_item]), cliques[cliq_item]['value'])

    #for testing purposes, the following people are interesting:
    #keith.holst@enron.com has 22 neighbors
    #celeste.roberts@enron.com has 489 neighbors
    #william.kelly@enron.com has 9 neighbors
    person_email = 'keith.holst@enron.com'
    focal_endpoint = [node for node in full_graph.nodes if node.address == person_email][0]
    personal_graph = build_personal_graph(full_graph, focal_endpoint)
    focal_cliques = {k: v for k, v in cliques.items() if focal_endpoint in k}    
    vis_graph, filtered_cliques, clique_dicts = prepare_graph_for_visualization(personal_graph, focal_endpoint, focal_cliques, graph_visual_filter)
    add_wordcloud_to_cliques(messages, clique_dicts, word_count = 5, filter_tags = {"NOUN", "ADJ", "ADV"})
    jsonify(vis_graph, focal_endpoint, filtered_cliques, clique_dicts)
    out_to_json(json_filename)

###################################################################################################
def add_wordcloud_to_cliques(messages, cliques, word_count = 10, filter_tags = {"ADJ", "ADP", "ADV", "CONJ", "DET", "NOUN", "NUM", "PRT", "PRON", "VERB", "X"}):
    for clique in cliques:
        print("Analyzing clique " + ",".join([w.address for w in clique]))
        group_messages = extract_sender_messages(clique, messages)
        messagestring = ".".join([".".join([preprocess_message_body(i.body) for i in m]) for m in group_messages.values()])
        tagged_list = nltk.tag.pos_tag(nltk.tokenize.word_tokenize(messagestring), tagset = "universal", lang = "eng")
        filtered_tagged_list = [(w,t) for (w,t) in tagged_list if t in filter_tags and w.isalpha()
                        #TODO: this probably isn't the right place to filter out thesese items.
                        #filtering out first names/last names (using the email address) and filtering out common words
                        and not any([w.lower() in person.address.lower() for person in clique])
                        and not any([w.lower() in word for word in {"https", "test", "am", "pm", "google", "jabber", "xmlns"}])]
        cliques[clique]['sentiment'] = sentiment(filtered_tagged_list)
        tag_fd = nltk.FreqDist(filtered_tagged_list)
        most_common = tag_fd.most_common(10)
        cliques[clique]['wordcloud'] = ", ".join([w[0] for (w,t) in most_common])
        

###################################################################################################
def build_personal_graph(full_graph, person):
    #takes an endpoint and creates the graph around him.
    neighb = list(nx.all_neighbors(full_graph, person))
    neighb.append(person)
    personal_graph = full_graph.subgraph(neighb)
    return personal_graph

###################################################################################################
def preprocess_message_body(message):
    #Strip out html
    #Strip out common words
    logging.debug('Preprocessing raw message: %s', message)
    common_words = nltk.corpus.stopwords.words('english')
    processed_message = [word for word in nltk.word_tokenize(BeautifulSoup(message, "lxml").get_text()) if (not word in common_words)]
    logging.debug('Preprocessing results in message: %s', processed_message)
    #for now putting it back together as a string.
    return " ".join(processed_message)

def get_wordnet_pos(treebank_tag):
    if treebank_tag == 'ADJ':
        return nltk.corpus.wordnet.ADJ
    elif treebank_tag =='VERB':
        return nltk.corpus.wordnet.VERB
    elif treebank_tag == 'NOUN':
        return nltk.corpus.wordnet.NOUN
    elif treebank_tag == 'ADV':
        return nltk.corpus.wordnet.ADV
    else:
        return ''

def sentiment(tagged_words):
    lemmatizer = nltk.stem.WordNetLemmatizer()
    sentiment = 0.0
    nr_sentiment = 0
    for word, tag in tagged_words:
            wn_tag = get_wordnet_pos(tag)
            if wn_tag in (nltk.corpus.wordnet.NOUN, nltk.corpus.wordnet.ADJ, nltk.corpus.wordnet.ADV):
                lemma = lemmatizer.lemmatize(word, pos=wn_tag)
                if lemma:    
                    synsets = nltk.corpus.wordnet.synsets(lemma, pos=wn_tag)
                    if synsets:
                        #Take the most common meaning of the word, and determine the sentiment of it.
                        swn_synset = nltk.corpus.sentiwordnet.senti_synset(synsets[0].name())
                        logging.debug("pos/neg score of %s: %s & %s", synsets[0].name(), swn_synset.pos_score(), swn_synset.neg_score() )
                        sentiment += swn_synset.pos_score() - swn_synset.neg_score()
                        #Count number of items that have sentiment to get to an average score
                        nr_sentiment = nr_sentiment + 1
    return (sentiment / nr_sentiment)