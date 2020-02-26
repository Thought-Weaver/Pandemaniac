import json
import networkx as nx
import matplotlib.pyplot as plt
import sys
import sim
import numpy as np
import heapq
import community
import time
from networkx.algorithms.approximation.vertex_cover import min_weighted_vertex_cover
from networkx.algorithms.approximation.independent_set import maximum_independent_set
import random


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


def prune_graph_min_weight_vc(G):
    vc = min_weighted_vertex_cover(G)
    return G.subgraph(min_weighted_vertex_cover(G))


def prune_graph_max_independent_set(G):
    s = maximum_independent_set(G)
    return G.subgraph(G.nodes() - s)


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


def triangles_top_k(G, num_seeds):
    return abstracted_node_selection(nx.triangles(G), num_seeds)


def mix_stategies_ratio_additive(G, ratios, num_seeds):
    # Setting them manually for now.
    # Could use closeness, but it's slow for large graphs.
    ev = nx.eigenvector_centrality(G)
    # closeness = nx.closeness_centrality(G)
    btw = nx.betweenness_centrality(G)
    deg = nx.degree_centrality(G)
    tri = nx.triangles(G)

    centralities = {}
    for k in ev:
        centralities[k] = ratios[0] * ev[k] + \
                          ratios[1] * btw[k] + \
                          ratios[2] * deg[k] + \
                          ratios[3] * tri[k]

    return abstracted_node_selection(centralities, num_seeds)


def vertex_cover_top_k(G, num_seeds):
    pruned_G = prune_graph_min_weight_vc(G)
    num_nodes = min(num_seeds, len(pruned_G))

    final_nodes = list(abstracted_node_selection(nx.degree_centrality(pruned_G), num_nodes))
    final_nodes += list(set(abstracted_node_selection(nx.degree_centrality(G), num_seeds)) - set(final_nodes))

    return final_nodes[:num_seeds]


def mix_stategies_additive_uniform(G, num_seeds):
    # We're going to generate more seeds than we need in each case
    # and combine them, similarly to what we did in the additive
    # version, but a bit more clever -- instead of mixing them before
    # we have the top_k, we're going to do it after with more nodes.
    num_seeds *= 2

    ev = list(eigenvector_centrality_top_k(G, num_seeds))
    close = list(closeness_centrality_top_k(G, num_seeds))
    btw = list(betweenness_centrality_top_k(G, num_seeds))
    deg = list(degree_centrality_top_k(G, num_seeds))
    tri = list(triangles_top_k(G, num_seeds))

    # Essentially, we weight everything uniformly (for now at least,
    # though I think ratios would be better), and then the best nodes
    # are selected by the number of times they appear!

    centralities = {}
    for n in ev + close + btw + deg + tri:
        centralities[n] = 0
    for i in range(num_seeds):
        centralities[ev[i]] += 1
        centralities[close[i]] += 1
        centralities[btw[i]] += 1
        centralities[deg[i]] += 1
        centralities[tri[i]] += 1
    return abstracted_node_selection(centralities, num_seeds // 2)


# ------------------------------ #
# OUTPUT NODES                   #
# ------------------------------ #

def select_nodes(G, measure, ratios):
    # Generate top k and write to file
    if measure == 0:
        nodes = degree_centrality_top_k(G, num_seeds)
    elif measure == 1:
        nodes = closeness_centrality_top_k(G, num_seeds)
    elif measure == 2:
        nodes = betweenness_centrality_top_k(G, num_seeds)
    elif measure == 3:
        nodes = eigenvector_centrality_top_k(G, num_seeds)
    elif measure == 4:
        nodes = triangles_top_k(G, num_seeds)
    elif measure == 5:
        nodes = vertex_cover_top_k(G, num_seeds)
    elif measure == 6:
        nodes = mix_stategies_ratio_additive(G, ratios, num_seeds)
    else:
        nodes = mix_stategies_additive_uniform(G, num_seeds)

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
    # Not sure if this is ideal. Maybe don't prune at all?
    # G_pruned = prune_graph_min_weight_vc(G)

    # Closeness is currently best, but very slow.
    # Weights are currently guesses.
    nodes = select_nodes(G, int(sys.argv[2]), [0.6, 0.1, 0.6, 0.9])
    # nodes_2 = select_nodes(G, 1, [0.6, 0.1, 0.6, 0.9])

    # print("NODES: %s" % nodes)

    # Note that the input is {strategy_name: nodes} in a dict.
    # Add more to have them compete!
    # print(sim.run(nx.to_dict_of_lists(G), {int(sys.argv[2]): nodes, 1: nodes_2}))

    output_nodes(sys.argv[1], nodes)
    #e = time.time()
    #print(e - s)
