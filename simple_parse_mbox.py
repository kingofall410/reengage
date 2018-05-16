import mailbox, re, random
import dateutil.parser
from models import Endpoint, CustomHeader, Message
import networkx as nx
import matplotlib.pyplot as plt

################################################################################
def parse_endpoints(endpoint_string):
    if (endpoint_string):
        #split the individual recipients based on commas not inside quotes
        endpoint_strings = re.split(',(?=(?:[^"]*"[^"]*")*[^"]*$)', endpoint_string)

        #match each recipient's email address and name
        #TODO:these fail if there's no email address, needs fixed
        endpoint_addresses = [re.search("[\w\.'-]+@[\w\.-]+\.\w+", str).group().strip() for str in endpoint_strings]
        endpoint_names = [re.match('([^<]+)', str).group(0).strip('" \n\t') for str in endpoint_strings]

        #print("----------------------------------")
        #print(endpoint_strings)
        #print("Parsed Addresses:", endpoint_addresses)
        #print("Parsed Names:", endpoint_names)
        return endpoint_addresses, endpoint_names
    else:
        return None, None

################################################################################
def parse(filename):

    messages = []
    endpoints = []
    print(filename)
    input = mailbox.mbox(filename)
    for message in input:

        #see if it has a From, if not it's a bad mbox, just skip for now
        if (message['From']):

            #Create Sender Endpoint
            sender_add, sender_name = parse_endpoints(  message['From'])
            if (sender_add and sender_name):

                sender = Endpoint.get_or_create(endpoints, sender_add[0], sender_name[0])

            #Create Message object
            id = message['Message-ID']
            if (id):
                print("********* "+id)
            else:
                print("********* "+str(message))

            subject = message['Subject']
            date = dateutil.parser.parse(message['Date'])
            body = message.get_payload()
            mess = Message(id=id, sender=sender, subject=subject, datetime=date, body=body, flatmbox=str(message))

            #Add receiver Endpoints
            recipients_add, recipients_name = parse_endpoints(message['To'])
            if (recipients_add and recipients_name):
                for (recipient_add, recipient_name) in zip(recipients_add, recipients_name):

                    #print("*"+recipient_add+"*", recipient_name)
                    receiver = Endpoint.get_or_create(endpoints, recipient_add, recipient_name)
                    mess.addRecipient(receiver)

            #get all custom headers and save as strings
            headers = message.items()
            for header in headers:
                if (header[0].startswith('X') or header[0].startswith('x')):
                    ch = CustomHeader(header_key=header[0], header_value=header[1])
                    mess.addCH(ch)

            #add to the list
            messages.append(mess)

    return messages, endpoints

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
'''
def find_node(graph, emailaddress ):
    for node in graph.nodes:
        if(str(node) == emailaddress):
            result = node
    return result'''
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
def parse_and_vis(filename='..\\data\\enron\\processed\\small.mbox', visualize=False):

    messages, eps = parse(filename)

    #TODO: could be memory concern, but fine for now
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
            #print('New conn comp ('+str(len(conn_comp))+'): ', [c.address for c in conn_comp])

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

                #print('New friend group ('+str(len(friends))+'): ', [f.address for f in friends])
                groups_of_friends.add(frozenset(friends))
                
    gof = sorted(list(groups_of_friends), key=lambda x: len(x), reverse=True )
    for group in gof:
        print('Friend group ('+str(len(group))+'): ', [f.address for f in group])
#uncommnet to run from command line
#parse_and_vis

#list(nx.all_neighbors(full_graph, start_node)))
#keep iterating to add friends until we hit a stopping criteria
##newnode = find_node(full_graph, 'justin.rostant@enron.com')
#friends = {start_node, newnode}
#friends = friends.add(newnode)
#newnode = find_node(full_graph, 'john.griffith@enron.com')
#friends.add(newnode)
#print(friends)
#newlist = sorted(ut, key=lambda x: x.count, reverse=True)

#plot the graph.






#random tests
'''
print(messages[0].sender.address)
print(len(messages))
print (messages[random.randint(0, len(messages))])
print (messages[random.randint(0, len(messages))].flatmbox)

print("*********************")
for ep in eps:
    print (str(ep))
print("*********************")
'''
