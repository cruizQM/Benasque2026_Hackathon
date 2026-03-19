import numpy as np
import pandas as pd

from icecream import ic
from src.data_loader import BenasqueDataLoader, generate_qaoa_inputs
from src.decoding import decode_solution
from src.structural_verifier import validate_directed_route_structure


def save_qaoa_inputs(list_nodes, list_edges, output_path):
    num_nodes = len(list_nodes)
    num_edges = len(list_edges)
    with open(output_path, "w") as f:
        f.write(f"{num_nodes} {num_edges}\n")
        for i, j, w in list_edges:
            f.write(f"{i} {j} {w}\n")


def main():
    VERBOSE = False  # 🔁 toggle this to test both behaviors

    # Load data
    loader = BenasqueDataLoader(
        nodes_path="data/nodes.csv",
        distances_path="data/distances.csv",
        gear_filter="Summer_Urban",
    )
    loader.load()

    nodes_df, distances_df, elevation_df = loader.get_dataframes()

    nodes_df.to_csv("data/urban_nodes.csv")
    distances_df.to_csv("data/urban_distances.csv")
    elevation_df.to_csv("data/urban_elevation.csv")

    list_nodes, list_edges = generate_qaoa_inputs(distances_df, elevation_df)

    save_qaoa_inputs(list_nodes, list_edges, output_path="inputs.txt")

    # Dummy solution
    num_nodes = len(list_nodes)
    num_edges = len(list_edges)
    solution = np.random.randint(2, size=num_nodes + num_edges).tolist()

    # Decode
    dic_x, dic_y = decode_solution(
        solution,
        num_nodes,
        num_edges,
        list_nodes,
        list_edges,
    )

    ic(solution)
    ic(dic_x, dic_y)

    base_node = "Benasque"

    print("\n=== Structural verification ===")
    print(f"Base node: {base_node}")

    # 🔁 Handle both modes cleanly
    if VERBOSE:
        feasible, diagnostics = validate_directed_route_structure(
            dic_x=dic_x,
            dic_y=dic_y,
            base_node=base_node,
            verbose=True,
        )

        print(f"Feasible route: {feasible}")

        if feasible:
            print("Ordered cycle:")
            print(diagnostics["ordered_cycle"])
        else:
            print("Validation errors:")
            for err in diagnostics["errors"]:
                print(f" - {err}")

    else:
        feasible = validate_directed_route_structure(
            dic_x=dic_x,
            dic_y=dic_y,
            base_node=base_node,
            verbose=False,
        )

        print(f"Feasible route: {feasible}")


if __name__ == "__main__":
    main()