import json

import numpy as np
import pandas as pd

from icecream import ic
from src.data_loader import BenasqueDataLoader, generate_qaoa_inputs
from Code.Not_Noisy.MaxCut.PCE_CUNQA.main_example_simulation import run_simulation_experiment

BASE_NODE = "Benasque"  # Define the base node for route validation
VERBOSE = True  # Set to True for detailed diagnostics during validation


def save_qaoa_inputs(list_nodes, list_edges, output_path):
    num_nodes = len(list_nodes)
    num_edges = len(list_edges)
    with open(output_path, "w") as f:
        f.write(f"{num_nodes} {num_edges}\n")
        for i, j, w in list_edges:
            f.write(f"{i} {j} {w}\n")
            
   
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
    
    list_nodes, list_edges = generate_qaoa_inputs(distances_df, elevation_df,
                                                  p_distance=100, p_elevation=100)
    num_nodes = len(list_nodes)
    num_edges = len(list_edges)
    
    # output_path = f"Code/Not_Noisy/MaxCut/PCE_CUNQA/src/graphs/Route_select_{num_nodes}.txt"
    # save_qaoa_inputs(list_nodes, list_edges, output_path=output_path)

    solution_found = False
    run_simulation_experiment()
    
    

if __name__ == "__main__":
    main()
