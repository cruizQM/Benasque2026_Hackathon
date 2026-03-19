from icecream import ic

from src.data_loader import BenasqueDataLoader


    
    
    
def main():
    # Load data
    loader = BenasqueDataLoader(nodes_path="data/nodes.csv",
                                distances_path="data/distances.csv",
                                gear_filter="Summer_Urban")
    loader.load()
    
    nodes_df, distances_df = loader.get_dataframes()
    ic(nodes_df.head())
    ic(distances_df.head())

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