import json
import networkx as nx
import matplotlib.pyplot as plt
import sys
import heapq


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
    G.remove_nodes_from(nx.isolates(G))

    return G, num_players, num_seeds, unique_id


# ------------------------------ #
# TOP K NODE SELECTION           #
# ------------------------------ #


def degree_centrality_top_k(G, num_seeds):
    return heapq.nlargest(nx.degree_centrality(G), num_seeds)


def closeness_centrality_top_k(G, num_seeds):
    return heapq.nlargest(nx.closeness_centrality(G), num_seeds)


def betweenness_centrality_top_k(G, num_seeds):
    return heapq.nlargest(nx.betweenness_centrality(G), num_seeds)


# ------------------------------ #
# MAIN PROGRAM                   #
# ------------------------------ #

if __name__ == "__init__":
    if len(sys.argv) < 2:
        print("Error: Need to specify a JSON graph filename.")
        exit(1)

    G, num_players, num_seeds, unique_id = load_graph(sys.argv[1])
