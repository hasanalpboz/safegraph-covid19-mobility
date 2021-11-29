import igraph as ig
import numpy as np

def get_netsmile_features(net, nodes, weight=None, deg_dir=None):
    '''
    extract `netsmile` features as in Berlingerio 2012

    1. Degree of node
    2. Clustering coefficient of node
    3. Average degree of node's neighbors
    4. Average clustering coefficient of node's neighbors
    5. Number of edges in node's egonet
    6. Number of neighbors of node's egonet
    7. Number of outgoing edges from node's egonet
    '''

    # get node labels and their indices
    node_labels = net.vs['name']
    
    # indices of the selected nodes
    selected_nodes = set(nodes)
    nids = [ind for ind, node in enumerate(node_labels) if node in selected_nodes]

    # node to neighborhood dict
    negs = {node: [net.vs[i]['name'] for i in net.neighborhood(node)] for node in node_labels}

    # degree & strength vectors
    # and their mapping dict objects
    degree = np.array(net.degree(node_labels, mode='all'))
    strength = np.array(net.strength(node_labels, mode='all', weights='visits'))
    degree_dict = {node: degree[ind] for ind, node in enumerate(node_labels)}
    strength_dict = {node: strength[ind] for ind, node in enumerate(node_labels)}

    # avg degree of neighbors
    avg_neg_deg = np.array([sum([strength_dict[neg] for neg in negs[node]]) / strength[ind]
                                        for ind, node in enumerate(node_labels)])

    # clustering coefficients and a dict object that maps nodes to their scores
    clustering = np.array(net.transitivity_local_undirected(node_labels, weights='visits'))
    clustering_dict = {node: clustering[ind] for ind, node in enumerate(node_labels)}
    # avg clustering coefficients on the given nodes
    avg_clustering = np.array([sum([clustering_dict[neg] for neg in negs[node]]) / strength[ind]
                                                            for ind, node in enumerate(node_labels)])

    # ego network features
    num_ego_negs = []
    num_ego_edges = []
    num_ego_outgoing_edges = []
    for node in nodes:
        alters = set(net.neighborhood(node))
        ego = net.induced_subgraph(alters)
        # total number of edges
        num_ego_edges.append(len(ego.es))
        # total number of neighbors of the egonet
        total_negs = set.union(*[set(negs[i]) for i in ego.vs['name']])
        inside_ego = set(ego.vs['name'])
        num_ego_negs.append(len(total_negs - inside_ego))
        # outgoing edges from the egonet
        oe = 0
        for alter in alters:
            for edge in net.incident(alter):
                if net.es[edge].target not in alters:
                    oe += 1
        num_ego_outgoing_edges.append(oe)
        
    return np.vstack([degree[nids], strength[nids], avg_neg_deg[nids], clustering[nids], avg_clustering[nids], num_ego_negs, num_ego_edges, num_ego_outgoing_edges]).T