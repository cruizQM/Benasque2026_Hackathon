import json

import numpy as np
import pandas as pd

from icecream import ic
from src.data_loader import BenasqueDataLoader, generate_qaoa_inputs
from src.decoding import decode_solution
# from Code.Not_Noisy.MaxCut.PCE_CUNQA.main_example_simulation import run_simulation_experiment

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
        return nth_best_run["initial_bitstring"]  # Return the solution (list of bits)
   
MAX_RUNS = 10         
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
    
    list_nodes, list_edges = generate_qaoa_inputs(distances_df, elevation_df)
    num_nodes = len(list_nodes)
    num_edges = len(list_edges)
    
    save_qaoa_inputs(list_nodes, list_edges, output_path=f"Code/Not_Noisy/MaxCut/PCE_CUNQA/src/graphs/Route_select_{num_nodes}.txt")

    solution_found = False
    for run in range(MAX_RUNS):
        print(f"\n=== Run {run+1}/{MAX_RUNS} ===")
        # run_simulation_experiment()
        # VQA calls would go here, using the generated inputs
        # the result is finally obtained as list of bits representing the solution, which can be decoded using the decode_solution function from decoding.py
        output_path = f"Code/Not_Noisy/MaxCut/PCE_CUNQA/Resultados/Route_select/Simulation/{num_nodes}_vertices/DIFFERENTIALEVOLUTION/Route_select_{num_nodes}_DIFFERENTIALEVOLUTION_2.json"
        
        n = 1
        while True:
            print(f"    Trying to decode the {n}-th best solution from the results...")
            try:
                solution = get_nth_best_solution(output_path, n=n)
            except Exception as e:
                print(f"No more solutions after trying to get the {n}-th best solution.")
                break
            # ic(solution)
            
            dic_x, dic_y = decode_solution(solution, 
                                            num_nodes, num_edges,
                                            list_nodes, list_edges)
            # ic(dic_x, dic_y)
            
            feasible_structural = False
            feasible_specific = True
            
            if not feasible_structural or not feasible_specific:
                n = n + 1
                continue
            
            solution_found = True
        
            print(f"    The {n}-th best solution is feasible.")
            break
        if solution_found:
            print(f"Feasible solution found in run {run+1}. Stopping further runs.")
            break
    
    if not solution_found:
        print("Reached the end of the experiment runs without finding a feasible solution.")
    else:
        print("Feasible solution found.")

    
    
    

if __name__ == "__main__":
    main()
