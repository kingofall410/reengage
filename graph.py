import logging

from models import Endpoint, CustomHeader, Message
import networkx as nx
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
    #logging.debug("%s: %d", from_node.address,result) -- careful, this seems to log an insane amount of data for some reason
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

def build_and_analyze(messages, eps, visualize=False):

    full_graph = build_graph(messages, eps, visualize)

    #goal is to explain the total amount of emails with as simple a structure as possible.
    #so first assess how many emails we have in total
    total_edges_weight = full_graph.size(weight = 'weight')
    total_number_edges = full_graph.size()
    logging.info("Total number of edges is %s with a total weight of %s", str(total_number_edges), str(total_edges_weight))
    #let's see what the heaviest edges are
    edge_list = sorted(list(full_graph.edges), key=lambda x: full_graph[x[0]][x[1]]['weight'], reverse=True)
    for i in range(0,25):
        edge = edge_list[i]
        logging.info("Edge from %s to %s has weight %s", edge[0], edge[1], full_graph[edge[0]][edge[1]]['weight'])
    #find distinct subgraphs
    comps = nx.weakly_connected_components(full_graph)

    #create groups of friends
    groups_of_friends = set()
    minsize_comps = 5
    email_threshold = 50
    maxsize_friend_group = 10
    for conn_comp in comps:
        #if the subgraph is small, it's a friend group
        if len(conn_comp) <= minsize_comps:
            groups_of_friends.add(frozenset(conn_comp))

        #if the subgraph is large, look for well connected groups within
        else:
            for node in conn_comp:
               #if node.name == 'arsystem@mailman.enron.com':
                friends = {node}
                candidates = set()
                winner = node
                friends_total_weight = 0
                #now start adding more people to the group of friends iteratively
                for i in range(0, maxsize_friend_group):
                    #add all neighbors of the new node to the candidate set and remove friends already added
                    candidates |= {*(nx.all_neighbors(full_graph, winner))}
                    candidates = candidates-friends
                    #add the strongest remaining connection to the friends set
                    #added x.name as second sort to make code run deterministic
                    winner = sorted(list(candidates), key=lambda x: (connectedness_kpi(full_graph, x, friends), x.name), reverse=True)[0]
                    #but don't add if there aren't at least email_threshold number of communications
                    winner_weight = total_edge_weight(full_graph, winner, friends)
                    logging.info('Winner is %s with weight %s', winner.name, str(winner_weight))
                    if winner_weight >= email_threshold:
                        logging.info('Winner %s was added due to weight %s', winner.name, str(winner_weight))
                        friends.add(winner)
                        #DC: I'd like to save some attributes of the friends while building this
                        #things like how connected it is. Would be efficient to keep track of it while building
                        #but right now I don't know where to store it
                        friends_total_weight += winner_weight
                #because of email_threshold restriction, may end up with groups of 1
                if len(friends) > 1:
                    groups_of_friends.add(frozenset(friends))
    #sorting based on group_density rather than size.
    gof = sorted(list(groups_of_friends), key=lambda x: full_graph.subgraph(x).size(weight = 'weight'), reverse=True )
    logging.info('Number of groups: %s', str(len(gof)))
    explained_edge_weight = 0
    for group in gof:
        group_weight = full_graph.subgraph(group).size(weight = 'weight')
        logging.info('Friend group (%s, weight = %s): %s', str(len(group)), str(group_weight), str([f.address for f in group]))
        explained_edge_weight += group_weight
    #so now I know how well my algorithm performed
    logging.info('Algorithm created groups for a total of %s emails (out of %s emails, 1 email can be in multiple groups)',str(explained_edge_weight) ,str(total_edges_weight))

    #look at the top group
    most_dense_group = gof[0]
    subgraph = full_graph.subgraph(most_dense_group)
    pos=nx.spring_layout(subgraph)
    nx.draw(subgraph, pos, with_labels=True)
    labels=dict([((u,v,),d['weight']) for u,v,d in subgraph.edges(data=True)])
    nx.draw_networkx_edge_labels(subgraph,pos,edge_labels=labels)
    plt.show()
