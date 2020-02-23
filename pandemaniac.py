import json
import networkx as nx
import matplotlib.pyplot as plt
import sys
import sim
import numpy as np


# ------------------------------ #
# PARSING AND LOADING GRAPHS     #
# ------------------------------ #

def load_graph(filename):
    """
    Given a JSON graph filename, return a tuple of the NetworkX
    graph, the number of players, the number of seeds, and the
    unique ID.
    :param filename: The path to a JSON graph file.
    :return: (NX Graph, num_players, num_seeds, unique_id)
    """
    with open(filename, 'r') as f:
        data = f.read()

    split_filename = filename.split('.')
    num_players = int(split_filename[0])
    num_seeds   = int(split_filename[1])
    unique_id   = int(split_filename[2])

    graph_dict = json.loads(data)
    G = nx.Graph(graph_dict)

    # Get rid of isolated nodes.
    G.remove_nodes_from(list(nx.isolates(G)))

    return G, num_players, num_seeds, unique_id


# ------------------------------ #
# TOP K NODE SELECTION           #
# ------------------------------ #

def abstracted_node_selection(centrality, num_seeds):
    sorted_centrality = np.array(sorted(centrality.items(), key=lambda x: x[1]))
    return sorted_centrality[-num_seeds:, 0]


def degree_centrality_top_k(G, num_seeds):
    return abstracted_node_selection(nx.degree_centrality(G), num_seeds)


def closeness_centrality_top_k(G, num_seeds):
    return abstracted_node_selection(nx.closeness_centrality(G), num_seeds)


def betweenness_centrality_top_k(G, num_seeds):
    return abstracted_node_selection(nx.betweenness_centrality(G), num_seeds)


# ------------------------------ #
# OUTPUT NODES                   #
# ------------------------------ #

def select_nodes(measure):
    # Generate top k and write to file 
    if measure == 0:
        nodes = degree_centrality_top_k(G, num_seeds)
    elif measure == 1:
        nodes = closeness_centrality_top_k(G, num_seeds)
    else:
        nodes = betweenness_centrality_top_k(G, num_seeds)

    return nodes


def output_nodes(filename, nodes):
    out = ""
    for node in nodes:
        out += str(node) + "\n"
    with open(filename.replace('json', 'txt'), 'w') as f:
        f.write(out * 50)


# ------------------------------ #
# MAIN PROGRAM                   #
# ------------------------------ #

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Error: Correct input is [JSON filename] [centrality_measure]")
        exit(1)

    G, num_players, num_seeds, unique_id = load_graph(sys.argv[1])

    nodes = select_nodes(int(sys.argv[2]))

    print("NODES: %s" % nodes)

    print(sim.run(nx.to_dict_of_lists(G), {sys.argv[2]: nodes}))

    output_nodes(sys.argv[1], nodes)



