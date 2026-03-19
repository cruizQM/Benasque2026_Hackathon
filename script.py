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
            
            
def main():
    # Load data
    loader = BenasqueDataLoader(nodes_path="data/nodes.csv",
                                distances_path="data/distances.csv",
                                gear_filter="Summer_Urban")
    loader.load()
    
    nodes_df, distances_df, elevation_df = loader.get_dataframes()
    
    nodes_df.to_csv("data/urban_nodes.csv")
    distances_df.to_csv("data/urban_distances.csv")
    elevation_df.to_csv("data/urban_elevation.csv")
    
    list_nodes, list_edges = generate_qaoa_inputs(distances_df, elevation_df)
    num_nodes = len(list_nodes)
    num_edges = len(list_edges)
    
    save_qaoa_inputs(list_nodes, list_edges, output_path=f"Code/Not_Noisy/MaxCut/PCE_CUNQA/src/graphs/Route_select_{num_nodes}.txt")

    # run_simulation_experiment()
    # VQA calls would go here, using the generated inputs
    # the result is finally obtained as list of bits representing the solution, which can be decoded using the decode_solution function from decoding.py
    output_path = f"Code/Not_Noisy/MaxCut/PCE_CUNQA/Resultados/Route_select/Simulation/{num_nodes}_vertices/DIFFERENTIALEVOLUTION/Route_select_{num_nodes}_DIFFERENTIALEVOLUTION_2.json"
    # read json file and extract the solution (list of bits)
    with open(output_path, "r") as f:
        data = json.load(f)
        last_run = data["resultados"][-1]  # get the last run (best solution)
        solution = last_run["initial_bitstring"]  # this should be the list of bits representing the solution
    ic(solution)
    
    dic_x, dic_y = decode_solution(solution, 
                                       num_nodes, num_edges,
                                       list_nodes, list_edges)
    ic(dic_x, dic_y)
    
    

if __name__ == "__main__":
    main()
