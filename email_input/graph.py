import logging
import subprocess as sp
import networkx as nx
import re, json
from collections import defaultdict

from . import watson
from email_input import models

import matplotlib.pyplot as plt

data = {"nodes": [], "edges": []}

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
        logging.debug("%s", sender.address)
        #find the sender's entry in m_b_e
        sender_tuple = messages_by_ep[sender.address]

        #find all sender's messages that include a recipient in this group
        senders_intra_group_messages = [m for m in sender_tuple[1] 
                                        if not set(graph_group).isdisjoint(set(m.receivers))]
        
        #add to dict
        group_messages[sender] = senders_intra_group_messages

        for message in senders_intra_group_messages:
            logging.debug("   %s", message)

    return group_messages

###################################################################################################
def out_to_json(filename):
    global data
    if filename:
        with open(filename, 'w') as outfile:
            json.dump(data, outfile)

###################################################################################################
def jsonify(graph):
    global data

    #TODO:This creates tons of edges to nowhere
    for (i, node) in enumerate(graph):
        #random limit
        if (i >= 1000):
            break

        node_dict = {"id": node.address, "label": node.address}
        if node_dict not in data["nodes"]:
            data["nodes"].append(node_dict)
        for succ in graph.successors(node):
            data["edges"].append({"from":node.address, "to":succ.address})

###################################################################################################
def build_and_analyze(messages, visualize=False, watson_filename=None, json_filename=None):
    print('Progress | Start analyze')
    logging.info("Messages: %s", str(len(messages)))
    full_graph = build_graph(messages, False)
    basic_graph_stats(full_graph)
    top_communicators(full_graph)

    threshold = 100
    reg_graph = build_unidir_graph(full_graph, threshold)

	#find distinct cliques
    cliques = nx.find_cliques(reg_graph)

    logging.debug('Cliques: ')
    for clique in cliques:
        if len(clique) > 1:
            logging.debug('Size of clique is %s. Members are: %s', len(clique), 
                          ([x.address for x in clique]))

            jsonify(full_graph.subgraph(clique))
    out_to_json(json_filename)

    logging.debug('Connected components: ')
    biggest_clique = max(nx.find_cliques(reg_graph), key= len)

    logging.info('Size of biggest clique is %s. Members are: %s', len(biggest_clique), 
                 ([x.address for x in biggest_clique]))

    if visualize:
        #gof = sorted(comps, key=lambda x: len(x), reverse=True )
        #most_dense_group = gof[0]
        logging.info('Members are: %s', str([x.address for x in biggest_clique]))
        subgraph = reg_graph.subgraph(biggest_clique)
        pos=nx.spring_layout(subgraph)
        nx.draw(subgraph, pos, with_labels=True)
        labels=dict([((u,v,),d['weight']) for u,v,d in subgraph.edges(data=True)])
        nx.draw_networkx_edge_labels(subgraph,pos,edge_labels=labels)
        plt.show()

    group_messages = extract_sender_messages(biggest_clique, messages)

    if watson_filename:
        watson.run_watson(group_messages, watson_filename, 1)
    else:
        print("No watsoning")

    #word clouding
    #create a dict that maps sender to their wordcloud of messages sent to this group
    group_wordcloud = defaultdict(models.WordCloud)
    for (i, sender) in enumerate(group_messages):

        #create a list of message bodies for this sender
        message_bodies = [m.body for m in group_messages[sender]]
        group_wordcloud[sender].append(message_bodies)
        
        nr = 10
        logging.info('Cloud for sender %s has length %s', sender.address, len(group_wordcloud[sender]))
        logging.info('Cloud top %s for sender %s: %s', nr, sender.address, group_wordcloud[sender].topX(nr))
