import json

import numpy as np
import pandas as pd

from icecream import ic
from src.data_loader import BenasqueDataLoader, generate_qaoa_inputs
from src.decoding import decode_solution
from src.route_specific_verifier import validate_route_constraints
from src.structural_verifier import validate_directed_route_structure
from src.route_generator import extract_route_with_metrics

BASE_NODE = "Benasque"  # Define the base node for route validation
VERBOSE = True  # Set to True for detailed diagnostics during validation

def check_structural_feasibility(dic_x, dic_y, base_node=BASE_NODE):
    """
    Check if the decoded solution satisfies structural constraints.

    Parameters
    ----------
    dic_x : dict[(str, str), int]
        Dictionary mapping edges (u, v) to binary values indicating whether the edge is included in the route.
    dic_y : dict[str, int]
        Dictionary mapping nodes to binary values indicating whether the node is visited in the route.
    base_node : str
        The required base node that must be included in the route.

    Returns
    -------
    bool
        True if the solution satisfies structural constraints, False otherwise.
    """
    print("\n=== Structural verification ===")
    print(f"Base node: {base_node}")

    if VERBOSE:
        feasible, diagnostics = validate_directed_route_structure(
            dic_x=dic_x,
            dic_y=dic_y,
            base_node=base_node,
            verbose=True,
        )

        print(f"Structurally feasible: {feasible}")
        if not feasible:
            print("Structural validation errors:")
            for err in diagnostics["errors"]:
                print(f" - {err}")

        return feasible

    feasible = validate_directed_route_structure(
        dic_x=dic_x,
        dic_y=dic_y,
        base_node=base_node,
        verbose=False,
    )

    print(f"Structurally feasible: {feasible}")
    return feasible


def check_route_specific_feasibility(
    dic_x,
    dic_y,
    distances_df,
    elevation_df,
    base_node=BASE_NODE,
    max_total_time=12.0,
    max_total_elevation_gain=2000.0,
):
    """
    Check if the decoded solution satisfies route-specific constraints.

    Parameters
    ----------
    dic_x : dict[(str, str), int]
        Dictionary mapping directed edges (u, v) to binary values indicating whether the edge is included in the route.
    dic_y : dict[str, int]
        Dictionary mapping nodes to binary values indicating whether the node is visited in the route.
    distances_df : pd.DataFrame
        DataFrame containing travel times between nodes.
    elevation_df : pd.DataFrame
        DataFrame containing elevation costs/gains between nodes.
    base_node : str
        The required base node that must be included in the route.
    max_total_time : float
        Maximum allowed total travel time.
    max_total_elevation_gain : float
        Maximum allowed total elevation gain.

    Returns
    -------
    bool
        True if the solution satisfies route-specific constraints, False otherwise.
    """
    print("\n=== Route-specific verification ===")

    try:
        route_info = extract_route_with_metrics(
            dic_x=dic_x,
            distance_df=distances_df,
            elevation_df=elevation_df,
            base_node=base_node,
        )
    except Exception as e:
        print(f"Route generation failed: {e}")
        return False

    if VERBOSE:
        print("Generated route:")
        print(f" - ordered_cycle: {route_info['ordered_cycle']}")
        print(f" - total_time: {route_info['total_time']}")
        print(f" - total_elevation_gain: {route_info['total_elevation_gain']}")

        feasible, diagnostics = validate_route_constraints(
            route_info=route_info,
            max_total_time=max_total_time,
            max_total_elevation_gain=max_total_elevation_gain,
            base_node=base_node,
            verbose=True,
        )

        print(f"Route-specific feasible: {feasible}")
        if not feasible:
            print("Route-specific violations:")
            for violation in diagnostics["violations"]:
                print(f" - {violation}")

        return feasible

    feasible = validate_route_constraints(
        route_info=route_info,
        max_total_time=max_total_time,
        max_total_elevation_gain=max_total_elevation_gain,
        base_node=base_node,
        verbose=False,
    )

    print(f"Route-specific feasible: {feasible}")
    return feasible



def save_qaoa_inputs(list_nodes, list_edges, output_path):
    num_nodes = len(list_nodes)
    num_edges = len(list_edges)
    with open(output_path, "w") as f:
        f.write(f"{num_nodes} {num_edges}\n")
        for i, j, w in list_edges:
            f.write(f"{i} {j} {w}\n")
            
            
def get_nth_best_solution(json_path, n=1):
    with open(json_path, "r") as f:
        data = json.load(f)
        resultados = data["resultados"]
        if len(resultados) < n:
            raise ValueError(f"Requested the {n}-th best solution, but only {len(resultados)} solutions are available.")
        nth_best_run = resultados[-n]  # Get the n-th best run (assuming they are ordered by performance)
        return nth_best_run["initial_bitstring"], nth_best_run["f_loss_value"]  # Return the solution (list of bits)
   

def objective_value(dic_x, dic_y, distances_df, elevation_df, p_distance=100, p_elevation=100, mu=1):
    total_distance = 0.0
    total_elevation = 0.0
    
    for (u, v), included in dic_x.items():
        if included == 1:
            # Get the distance and elevation cost for this edge
            distance = distances_df.loc[u, v]
            elevation = elevation_df.loc[u, v]
            total_distance += distance
            total_elevation += elevation
            
    # Calculate the objective value as a weighted sum of distance and elevation
    objective_val = p_distance * total_distance + p_elevation * total_elevation
    
    # Add the penalty for visiting nodes (if needed, based on dic_y)
    for node, visited in dic_y.items():
        if visited == 1:
            # If there's a penalty for visiting nodes, it can be added here
            objective_val -= mu  # Assuming no penalty for visiting nodes, otherwise add it here
        
    return objective_val
       
       
def main():
    # Load data
    loader = BenasqueDataLoader(nodes_path="data/nodes.csv",
                                distances_path="data/distances.csv",
                                gear_filter="Summer_Urban")
    loader.load()
    
    nodes_df, distances_df, elevation_df = loader.get_dataframes()
        
    # nodes_df.to_csv("data/urban_nodes.csv")
    # distances_df.to_csv("data/urban_distances.csv")
    # elevation_df.to_csv("data/urban_elevation.csv")
    
    list_nodes, list_edges = generate_qaoa_inputs(distances_df, elevation_df,
                                                  p_distance=100, p_elevation=100)
    num_nodes = len(list_nodes)
    num_edges = len(list_edges)
    
    
    output_path = f"Code/Not_Noisy/MaxCut/PCE_CUNQA/Resultados/Route_select/Simulation/{num_nodes}_vertices/DIFFERENTIALEVOLUTION/Route_select_{num_nodes}_DIFFERENTIALEVOLUTION_2.json"
    n = 1
    feasible_solutions = []
    while True:
        print(f"    Trying to decode the {n}-th best solution from the results...")
        try:
            solution, f_loss_value = get_nth_best_solution(output_path, n=n)
        except Exception as e:
            print(f"No more solutions after trying to get the {n}-th best solution.")
            break
        ic(solution, f_loss_value)
        
        dic_x, dic_y = decode_solution(solution, 
                                        num_nodes, num_edges,
                                        list_nodes, list_edges)
        print(f"DICTS")
        ic(dic_x, dic_y)
        
        feasible_structural = check_structural_feasibility(dic_x, dic_y)
        feasible_specific = check_route_specific_feasibility(dic_x, dic_y, distances_df, elevation_df) 
        if not feasible_structural or not feasible_specific:
            n = n + 1
            continue
        
        objective_val = objective_value(dic_x, dic_y, distances_df, elevation_df)
    
        print(f"    The {n}-th best solution is feasible.")
        feasible_solutions.append((n, dic_x, dic_y, f_loss_value, objective_val))
        

    ic(feasible_solutions)
    
    

if __name__ == "__main__":
    main()
