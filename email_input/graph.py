import logging
import subprocess as sp
import networkx as nx
import re, json

from . import watson
from email_input.models import Endpoint, CustomHeader, Message

import matplotlib.pyplot as plt

################################################################################
def build_graph(messages, endpoints, is_show_graph):
    G = nx.DiGraph()

    for endpoint in endpoints:
        G.add_node(endpoint)

    for message in messages:
        for receiver in message.receivers:
            if not G.has_edge(message.sender, receiver):
                G.add_edge(message.sender, receiver, weight = 0)
            G[message.sender][receiver]['weight'] += 1
            #G.add_edge(message.sender, receiver, weight=G.number_of_edges(message.sender, receiver)+1)

    if is_show_graph:
        nx.draw(G, with_labels=True)
        plt.show()
    return G

################################################################################
#TODO: Probably a more pythonic way to do this when I'm thinking clearly
def total_edge_weight(graph, from_node, to_nodes):
    result = 0
    for node in to_nodes:
        if graph.has_edge(from_node, node):
            result += graph[from_node][node]['weight']
        if graph.has_edge(node, from_node):
            result += graph[node][from_node]['weight']
    return result

################################################################################

################################################################################
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

################################################################################

################################################################################
def find_candidate(graph, group, candidates, is_remove):
    #this method determines who the best candidate to add/remove is
    #if is_remove, candidates needs to be subset of group
    if not is_remove:
        winner = sorted(candidates, key=lambda x: (connectedness_kpi(graph, x, group), x.name), reverse= not is_remove)[0]
        score = connectedness_kpi(graph, winner, group)
    else:
        winner = sorted(candidates, key=lambda x: (connectedness_kpi(graph, x, group - {x}), x.name), reverse= not is_remove)[0]
        score = connectedness_kpi(graph, winner, group - {winner})
    return winner, score

################################################################################

##################################

def top_communicators(full_graph):
#how connected is this graph really. Is there 2 way communication, what are reasonable amounts.
    values = list()
    for node in full_graph.nodes:
       for nb_node in set(nx.all_neighbors(full_graph, node)):
            if nb_node.name > node.name:
                from_value = 0
                if(full_graph.has_edge(node, nb_node)):
                    from_value += full_graph[node][nb_node]['weight']
                to_value = 0
                if(full_graph.has_edge(nb_node, node)):
                    to_value += full_graph[nb_node][node]['weight']
                value = min(from_value, to_value)
                if value > 0:
                    values.append(value)
    top_values = sorted(filter( lambda x: x > 10, values), reverse = True)
    logging.info('Top communicators: ')
    logging.info(top_values)
######################################################################

#######################################################################
def basic_graph_stats(full_graph):
    #goal is to explain the total amount of emails with as simple a structure as possible.
    #so first assess how many emails we have in total
    total_edges_weight = full_graph.size(weight = 'weight')
    total_number_edges = full_graph.size()
    logging.info("Total number of edges is %s with a total weight of %s", str(total_number_edges), str(total_edges_weight))
    #let's see what the heaviest edges are
    edge_list = sorted(list(full_graph.edges), key=lambda x: full_graph[x[0]][x[1]]['weight'], reverse=True)
    for i in range(0,100):
        edge = edge_list[i]
        logging.debug("Edge from %s to %s has weight %s", edge[0], edge[1], full_graph[edge[0]][edge[1]]['weight'])
#####################################################################

def build_and_analyze(messages, eps, visualize=False, watson_filename=None):
    print('Progress | Start analyze')
    logging.info("Messages: %s", str(len(messages)))
    full_graph = build_graph(messages, eps, False)

    basic_graph_stats(full_graph)

    top_communicators(full_graph)

    #To find groups, adjust the bidirectional graph into a unidirectional graph, weight on the edge is minimum of both directions
    #then find subgraphs that are fully connected, or even just weakly connected components
    two_way_email_threshold = 20
    reg_graph = nx.Graph()
    for node in full_graph.nodes:
        reg_graph.add_node(node)
        for nb_node in nx.all_neighbors(full_graph, node):
            if node != nb_node and nb_node.name > node.name:
                if full_graph.has_edge(node, nb_node) and full_graph.has_edge(nb_node, node):
                    value = min(full_graph[node][nb_node]['weight'],full_graph[nb_node][node]['weight'])
                    if value >= two_way_email_threshold:
                        reg_graph.add_edge(node, nb_node, weight = value)
    logging.debug('Built undirected graph with %s nodes and %s edges', len(reg_graph.nodes), len(reg_graph.edges))
    for element in reg_graph.edges:
        logging.debug('Edge from %s to %s', element[0].name, element[1].name)
    #find distinct subgraphs
    cliques = nx.find_cliques(reg_graph)

    logging.debug('Cliques: ')
    for clique in cliques:
        if len(clique) > 1:
            logging.debug('Size of clique is %s. Members are: %s', len(clique), ([x.name for x in clique]))
    logging.debug('Connected components: ')
    comps = nx.connected_components(reg_graph)
    for conn_comp in comps:
        if (len(conn_comp) > 1):
            logging.debug('Size of component is %s. Members are: %s', len(conn_comp), str([x.name for x in conn_comp]))
    most_dense_group = max(nx.connected_components(reg_graph), key= len)

    logging.info('Size of largest component is %s. Members are: %s', len(most_dense_group), str([x.name for x in most_dense_group]))
    #TODO: fix the visualization
    if visualize:
        #gof = sorted(comps, key=lambda x: len(x), reverse=True )
        #most_dense_group = gof[0]
        logging.info('Members are: %s', str([x.name for x in most_dense_group]))
        subgraph = reg_graph.subgraph(most_dense_group)
        pos=nx.spring_layout(subgraph)
        nx.draw(subgraph, pos, with_labels=True)
        labels=dict([((u,v,),d['weight']) for u,v,d in subgraph.edges(data=True)])
        nx.draw_networkx_edge_labels(subgraph,pos,edge_labels=labels)
        plt.show()

    if watson_filename:
        watson.run_watson(most_dense_group, messages, watson_filename)
    else:
        print("No watsoning")




    #result = sp.run("curl --user 2ba9c82d-4590-4d77-ae45-d3988afb5446:JWCDPbtBBX1v \"https://gateway.watsonplatform.net/natural-language-understanding/api/v1/analyze?version=2017-02-27&text=" + lastmessage.body + "&features=sentiment\"", shell=True, check=True, stdout=sp.PIPE, universal_newlines=True)
    #print("Email output: %s", result.stdout)
    #jsonresult = json.loads(result.stdout)
    #print(jsonresult['sentiment']['document']['score'])
##############################################################
def thrash():
    #create groups of friends
    groups_of_friends = set()
    minsize_comps = 5
    email_threshold = 25
    email_remove_threshold = 25
    for conn_comp in comps:
        #if the subgraph is small, it's a friend group
        #and actually, probably worthless for research
        if len(conn_comp) <= minsize_comps:
            groups_of_friends.add(frozenset(conn_comp))

        #if the subgraph is large, look for well connected groups within
        else:
            for node in conn_comp:
                #if node.name == 'arsystem@mailman.enron.com':
                friends = {node}
                candidates = set()
                winner = node
                done_adding = False#now start adding more people to the group of friends iteratively
                while (not done_adding):
                #for i in range(0, maxsize_friend_group):
                    #add all neighbors of the new node to the candidate set and remove friends already added
                    candidates |= {*(nx.all_neighbors(full_graph, winner))}
                    candidates = candidates-friends
                    #add the strongest remaining connection to the friends set
                    #added x.name as second sort to make code run deterministic
                    winner, winner_weight = find_candidate(full_graph, friends, candidates, False)
                    #but don't add if there aren't at least email_threshold number of communications
                    winner_edge_weight = total_edge_weight(full_graph, winner, friends)
                    logging.debug('Winner is %s with value %s and edge-weight %s', winner.name, str(winner_weight), str(winner_edge_weight))
                    if winner_weight >= email_threshold:
                        logging.info('Winner %s was added due to weight %s', winner.name, str(winner_weight))
                        friends.add(winner)
                    else:
                        done_adding = True

                done_removing = False
                while (not done_removing) & len(friends) > 1:
                    loser, loser_weight = find_candidate(full_graph, friends, candidates, True)
                    loser_edge_weight = total_edge_weight(full_graph, loser, friends)
                    logging.debug('Loser is %s with value %s and edge-weight %s', loser.name, str(loser_weight), str(loser_edge_weight))
                    if loser_weight <= email_remove_threshold:
                        logging.info('Loser %s was removed due to weight %s', loser.name, str(loser_weight))
                        friends = friends - {loser}
                        candidates = candidates - {loser}
                    else:
                        done_removing = True





                #because of email_threshold restriction, may end up with groups of 1
                if len(friends) > 1:
                    groups_of_friends.add(frozenset(friends))

    #sorting based on group_density rather than size.
    gof = sorted(groups_of_friends, key=lambda x: full_graph.subgraph(x).size(weight = 'weight'), reverse=True )
    logging.info('Number of groups: %s', str(len(gof)))
    explained_edge_weight = 0
    for group in gof:
        group_weight = full_graph.subgraph(group).size(weight = 'weight')
        logging.info('Friend group (%s, weight = %s): %s', str(len(group)), str(group_weight), str([f.address for f in group]))
        explained_edge_weight += group_weight
    #so now I know how well my algorithm performed
    total_edges_weight = full_graph.size(weight = 'weight')
    logging.info('Algorithm created groups for a total of %s emails (out of %s emails, 1 email can be in multiple groups)',str(explained_edge_weight) ,str(total_edges_weight))


    #look at the top group
