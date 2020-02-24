import json
import networkx as nx
import matplotlib.pyplot as plt
import sys
import sim
import numpy as np
import heapq
import community
import time


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


def prune_graph(G, r=1):
    # Min cut?
    # Could we prune using an MST?
    # Also there's something in NX called a dominating set?
    # Trying something I found called communities that uses NX.
    best_part = community.best_partition(G, resolution=r)

    nodes = {}
    for node, group in best_part.items():
        if nodes.get(group) is None:
            nodes[group] = [node]
        else:
            nodes[group].append(node)

    return G.subgraph(max(nodes.items(), key=len)[1])


def get_largest_strongly_connected_component(G):
    return max(nx.strongly_connected_components(G), key=len)


def get_largest_weakly_connected_component(G):
    return max(nx.weakly_connected_components(G), key=len)


# ------------------------------ #
# TOP K NODE SELECTION           #
# ------------------------------ #

def abstracted_node_selection(centrality, num_seeds):
    sorted_centrality = heapq.nlargest(num_seeds, centrality.items(), key=lambda x: x[1])
    return np.array(sorted_centrality)[:, 0]


def degree_centrality_top_k(G, num_seeds):
    return abstracted_node_selection(nx.degree_centrality(G), num_seeds)


def closeness_centrality_top_k(G, num_seeds):
    return abstracted_node_selection(nx.closeness_centrality(G), num_seeds)


def betweenness_centrality_top_k(G, num_seeds):
    return abstracted_node_selection(nx.betweenness_centrality(G), num_seeds)


def eigenvector_centrality_top_k(G, num_seeds):
    return abstracted_node_selection(nx.eigenvector_centrality(G), num_seeds)


def clustering_coefficient_top_k(G, num_seeds):
    return abstracted_node_selection(nx.clustering(G), num_seeds)


def katz_centrality_top_k(G, num_seeds):
    return abstracted_node_selection(nx.katz_centrality(G), num_seeds)


def mix_stategies_additive(G, num_seeds):
    # Setting them manually for now.
    # Could use closeness, but it's slow for large graphs.
    ev = nx.eigenvector_centrality(G)
    # closeness = nx.closeness_centrality(G)
    btw = nx.betweenness_centrality(G)

    centralities = {}
    for k in ev:
        centralities[k] = ev[k] + btw[k]

    return abstracted_node_selection(centralities, num_seeds)


# ------------------------------ #
# OUTPUT NODES                   #
# ------------------------------ #

def select_nodes(G, measure):
    # Generate top k and write to file 
    if measure == 0:
        nodes = degree_centrality_top_k(G, num_seeds)
    elif measure == 1:
        nodes = closeness_centrality_top_k(G, num_seeds)
    elif measure == 2:
        nodes = betweenness_centrality_top_k(G, num_seeds)
    elif measure == 3:
        nodes = mix_stategies_additive(G, num_seeds)
    else:
        nodes = eigenvector_centrality_top_k(G, num_seeds)

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

    #s = time.time()
    G, num_players, num_seeds, unique_id = load_graph(sys.argv[1])

    # Prune G to its best community.
    G_pruned = prune_graph(G)

    # I recommend using 3.
    nodes = select_nodes(G_pruned, int(sys.argv[2]))
    # nodes_2 = select_nodes(G, 1)

    # print("NODES: %s" % nodes)

    # Note that the input is {strategy_name: nodes} in a dict.
    # Add more to have them compete!
    # print(sim.run(nx.to_dict_of_lists(G), {int(sys.argv[2]): nodes, 1: nodes_2}))

    # {3: 440, 1: 9558}
    # Pure closeness is stronger.

    output_nodes(sys.argv[1], nodes)
    #e = time.time()
    #print(e - s)
