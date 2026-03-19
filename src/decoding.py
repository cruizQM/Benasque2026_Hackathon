import pandas as pd
import numpy as np

from icecream import ic


def decode_solution(solution: list[int], 
                    num_nodes: int, 
                    num_edges: int, 
                    nodes_list: list[str], 
                    edges_list: list[tuple[str, str]]) -> tuple[dict[str, int], dict[str, int]]:
    """
    Decodes the QAOA solution into a route and its total effort.
    
    Args:
        solution: list of bits representing the solution from QAOA, where each bit corresponds to a variable in the optimization problem.
                    the first num_nodes bits correspond to the y_i variables (whether node i is visited), and the next num_edges bits correspond to the x_{i,j} variables (whether edge (i, j) is included in the route).
        num_nodes: the number of nodes in the problem.
        num_edges: the number of edges in the problem.
    Returns:
        A tuple containing two dictionaries:
        - dic_x: a dictionary mapping each edge (i, j) to a binary value indicating whether it is included in the route.
        - dic_y: a dictionary mapping each node i to a binary value indicating whether it is visited in the route.
    """
    
    # check that the solution length matches the expected number of variables
    expected_length = num_nodes + num_edges
    if len(solution) != expected_length:
        raise ValueError(f"Expected solution length {expected_length}, but got {len(solution)}")
    
    dic_x = {}
    dic_y = {}

    # Decode y_i variables (first num_nodes bits)
    for i in range(num_nodes):
        dic_y[nodes_list[i]] = solution[i]
        
    # Decode x_{i,j} variables (next num_edges bits)
    for i in range(num_edges):
        edge_index = num_nodes + i
        ic(edges_list, i)
        nodeA_idx, nodeB_idx, _ = edges_list[i]  # assuming edges_list contains tuples of the form (nodeA_idx, nodeB_idx, weight)
        nodeA = nodes_list[nodeA_idx]
        nodeB = nodes_list[nodeB_idx]
        dic_x[(nodeA, nodeB)] = solution[edge_index]
        
    return dic_x, dic_y