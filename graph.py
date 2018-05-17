from models import Endpoint, CustomHeader, Message
import networkx as nx
import matplotlib.pyplot as plt

################################################################################
def build_graph(messages, endpoints, is_show_graph):
    G = nx.DiGraph()
    #print(str(endpoints[0]))
    #print(list(endpoints))
    for endpoint in endpoints:
        G.add_node(endpoint)

    for message in messages:
        for receiver in message.receivers:
            G.add_edge(message.sender, receiver, weight=str(G.number_of_edges(message.sender, receiver)+1))

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
            result += graph.number_of_edges(from_node, node)
        if graph.has_edge(node, from_node):
            result += graph.number_of_edges(node, from_node)
    #print(from_node + ": " + str(result))
    return result

################################################################################
def build_and_analyze(messages, eps, visualize=False):

    full_graph = build_graph(messages, eps, visualize)
    #find distinct subgraphs
    comps = nx.weakly_connected_components(full_graph)

    #for each distinct subgraph
    groups_of_friends = set()
    minsize_comps = 5

    for conn_comp in comps:
        #if the subgraph is small, it's a friend group
        if len(conn_comp) <= minsize_comps:
            groups_of_friends.add(frozenset(conn_comp))

        #if the subgraph is large, look for well connected groups within
        else:
            for node in conn_comp:
                friends = {node}
                candidates = set()
                winner = node

                #now start adding more people to the group of friends iteratively
                for i in range(0, minsize_comps - 1):
                    #add all neighbors of the new node to the candidate set and remove friends already added
                    candidates |= {*(nx.all_neighbors(full_graph, winner))}
                    candidates = candidates-friends

                    #add the strongest remaining connection to the friends set
                    winner = sorted(list(candidates), key=lambda x: total_edge_weight(full_graph, x, friends), reverse=True)[0]
                    friends.add(winner)

                groups_of_friends.add(frozenset(friends))

    gof = sorted(list(groups_of_friends), key=lambda x: len(x), reverse=True )
    for group in gof:
        print('Friend group ('+str(len(group))+'): ', [f.address for f in group])
