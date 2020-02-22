import json
import networkx as nx
import matplotlib.pyplot as plt

GRAPH = "example.json"

with open(GRAPH, 'r') as myfile:
    data=myfile.read()

graph_dict = json.loads(data)

g = nx.Graph(graph_dict)
nx.draw(g)
plt.show()