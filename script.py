import json

import numpy as np
import pandas as pd

from icecream import ic
from src.data_loader import BenasqueDataLoader, generate_qaoa_inputs
from src.decoding import decode_solution
from src.structural_verifier import validate_directed_route_structure
from src.route_generator import extract_route_with_metrics
from src.route_specific_verifier import validate_route_constraints


def save_qaoa_inputs(list_nodes, list_edges, output_path):
    num_nodes = len(list_nodes)
    num_edges = len(list_edges)
    with open(output_path, "w") as f:
        f.write(f"{num_nodes} {num_edges}\n")
        for i, j, w in list_edges:
            f.write(f"{i} {j} {w}\n")


def main():
    VERBOSE = False  # Toggle to test both behaviors

    # Example route-specific bounds
    MAX_TOTAL_TIME = 300.0
    MAX_TOTAL_ELEVATION_GAIN = 1200.0
    BASE_NODE = "Benasque"

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

    print("\n=== Structural verification ===")
    print(f"Base node: {BASE_NODE}")

    if VERBOSE:
        structural_feasible, structural_diagnostics = validate_directed_route_structure(
            dic_x=dic_x,
            dic_y=dic_y,
            base_node=BASE_NODE,
            verbose=True,
        )

        print(f"Structurally feasible route: {structural_feasible}")

        if not structural_feasible:
            print("Structural validation errors:")
            for err in structural_diagnostics["errors"]:
                print(f" - {err}")
            return

    else:
        structural_feasible = validate_directed_route_structure(
            dic_x=dic_x,
            dic_y=dic_y,
            base_node=BASE_NODE,
            verbose=False,
        )

        print(f"Structurally feasible route: {structural_feasible}")

        if not structural_feasible:
            print("Route extraction skipped because the solution is not structurally valid.")
            return

    # Extract ordered route and route metrics
    print("\n=== Route extraction ===")
    route_info = extract_route_with_metrics(
        dic_x=dic_x,
        distance_df=distances_df,
        elevation_df=elevation_df,
        base_node=BASE_NODE,
    )

    print("Ordered cycle:")
    print(route_info["ordered_cycle"])
    print(f"Total time: {route_info['total_time']}")
    print(f"Total elevation gain: {route_info['total_elevation_gain']}")

    # Route-specific constraints
    print("\n=== Route-specific verification ===")

    if VERBOSE:
        route_feasible, route_diagnostics = validate_route_constraints(
            route_info=route_info,
            max_total_time=MAX_TOTAL_TIME,
            max_total_elevation_gain=MAX_TOTAL_ELEVATION_GAIN,
            base_node=BASE_NODE,
            verbose=True,
        )

        print(f"Route-specific feasible: {route_feasible}")

        if route_feasible:
            print("Route satisfies all route-specific constraints.")
        else:
            print("Route-specific violations:")
            for violation in route_diagnostics["violations"]:
                print(f" - {violation}")

    else:
        route_feasible = validate_route_constraints(
            route_info=route_info,
            max_total_time=MAX_TOTAL_TIME,
            max_total_elevation_gain=MAX_TOTAL_ELEVATION_GAIN,
            base_node=BASE_NODE,
            verbose=False,
        )

        print(f"Route-specific feasible: {route_feasible}")


if __name__ == "__main__":
    main()