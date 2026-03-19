from icecream import ic

from src.data_loader import BenasqueDataLoader, generate_qaoa_inputs


def save_qaoa_inputs(num_nodes, num_edges, list_edges, output_path):
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
    ic(nodes_df.head())
    ic(distances_df.head())
    ic(elevation_df.head())
    
    num_nodes, num_edges, list_edges = generate_qaoa_inputs(distances_df, elevation_df)
    
    ic(num_nodes)
    ic(num_edges)
    ic(list_edges)
    
    save_qaoa_inputs(num_nodes, num_edges, list_edges, output_path="inputs.txt")
    
    exit()

    inputs = loader.get_optimization_inputs()
    
    ic(inputs)

    # Solve route
    route, obj_value = solve_hiking_route(inputs["distance"],
                                         inputs["elevation"],
                                         inputs["scenic"],
                                         max_distance=200.0,
                                         max_elevation=1000.0,
                                         alpha=0.1,
                                         beta=1.0)
    
    if route is not None:
        print("Optimal route found:")
        for i, j in route:
            print(f"{loader.places[i]} -> {loader.places[j]}")
        print(f"Objective value: {obj_value}")
    else:
        print("No feasible route found.")
    
    
if __name__ == "__main__":
    main()