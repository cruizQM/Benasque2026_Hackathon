import numpy as np
import pandas as pd

from icecream import ic
from src.data_loader import BenasqueDataLoader, generate_qaoa_inputs
from src.decoding import decode_solution
from Code.Not_Noisy.MaxCut.PCE_CUNQA.main_example_simulation import run_simulation_experiment

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
    
    save_qaoa_inputs(list_nodes, list_edges, output_path="inputs.txt")

    run_simulation_experiment()
    # VQA calls would go here, using the generated inputs
    # the result is finally obtained as list of bits representing the solution, which can be decoded using the decode_solution function from decoding.py
    
    # generate num_nodes + num_edges bits as a dummy solution for testing the decoding function
    num_nodes = len(list_nodes)
    num_edges = len(list_edges)
    solution = np.random.randint(2, size=num_nodes + num_edges).tolist()
    dic_x, dic_y = decode_solution(solution, 
                                       num_nodes, num_edges,
                                       list_nodes, list_edges)
    ic(dic_x, dic_y)

if __name__ == "__main__":
    main()
