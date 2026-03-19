import math
from collections import defaultdict
import pandas as pd


def extract_route_with_metrics(
    dic_x: dict[tuple[str, str], int],
    distance_df: pd.DataFrame,
    elevation_df: pd.DataFrame,
    base_node: str = "Benasque",
) -> dict:
    """
    Reconstruct a closed directed walk that traverses all selected arcs exactly once
    and compute total travel time and total elevation cost.

    This function assumes that the selected arcs already correspond to a
    structurally valid directed route in the Eulerian sense:
        - the selected directed subgraph is connected (in the underlying undirected sense)
        - every incident node satisfies in-degree == out-degree
        - the base node belongs to the selected component

    Parameters
    ----------
    dic_x : dict[(str, str), int]
        Directed arc-selection dictionary. dic_x[(u, v)] = 1 means arc u -> v is selected.
    distance_df : pd.DataFrame
        DataFrame containing travel times between nodes.
    elevation_df : pd.DataFrame
        DataFrame containing elevation costs between nodes.
    base_node : str, optional
        Starting/ending node of the route.

    Returns
    -------
    dict
        Dictionary with:
        - ordered_cycle
        - segments
        - total_time
        - total_elevation_gain
    """
    selected_arcs = [(u, v) for (u, v), val in dic_x.items() if val == 1]

    if not selected_arcs:
        raise ValueError("No selected arcs were found; cannot reconstruct a route.")

    # Build adjacency list with multiplicity preserved
    adjacency = defaultdict(list)
    incident_nodes = set()

    for u, v in selected_arcs:
        adjacency[u].append(v)
        incident_nodes.add(u)
        incident_nodes.add(v)

    if base_node not in incident_nodes:
        raise ValueError(
            f"Base node '{base_node}' is not incident to any selected arc."
        )

    # Hierholzer's algorithm for directed Eulerian circuit
    # We copy adjacency because we are going to consume arcs destructively
    adjacency_copy = {u: neighbors[:] for u, neighbors in adjacency.items()}

    stack = [base_node]
    circuit = []

    while stack:
        current = stack[-1]
        if current in adjacency_copy and adjacency_copy[current]:
            nxt = adjacency_copy[current].pop()
            stack.append(nxt)
        else:
            circuit.append(stack.pop())

    # Hierholzer returns the circuit in reverse order
    ordered_cycle = circuit[::-1]

    # A valid Eulerian circuit over E arcs must contain E+1 nodes in the walk
    if len(ordered_cycle) != len(selected_arcs) + 1:
        raise ValueError(
            f"Route reconstruction produced a walk of length {len(ordered_cycle)}, "
            f"but expected {len(selected_arcs) + 1} nodes for {len(selected_arcs)} selected arcs."
        )

    if ordered_cycle[0] != base_node:
        raise ValueError(
            f"Reconstructed route starts at '{ordered_cycle[0]}' instead of base '{base_node}'."
        )

    if ordered_cycle[-1] != base_node:
        raise ValueError(
            f"Reconstructed route ends at '{ordered_cycle[-1]}' instead of base '{base_node}'."
        )

    segments = []
    total_time = 0.0
    total_elevation_gain = 0.0

    traversed_arcs = 0
    traversed_arc_list = []

    for u, v in zip(ordered_cycle[:-1], ordered_cycle[1:]):
        if u not in distance_df.index or v not in distance_df.columns:
            raise ValueError(f"Missing time data for arc ({u}, {v}).")

        if u not in elevation_df.index or v not in elevation_df.columns:
            raise ValueError(f"Missing elevation data for arc ({u}, {v}).")

        time_val = float(distance_df.loc[u, v])
        elevation_val = float(elevation_df.loc[u, v])

        if not math.isfinite(time_val):
            raise ValueError(f"Invalid time value for arc ({u}, {v}): {time_val}")
        if not math.isfinite(elevation_val):
            raise ValueError(f"Invalid elevation value for arc ({u}, {v}): {elevation_val}")

        segments.append(
            {
                "from": u,
                "to": v,
                "time": time_val,
                "elevation_gain": elevation_val,
            }
        )

        total_time += time_val
        total_elevation_gain += elevation_val
        traversed_arcs += 1
        traversed_arc_list.append((u, v))

    # Check that every selected arc was traversed exactly once
    if sorted(traversed_arc_list) != sorted(selected_arcs):
        raise ValueError(
            "The reconstructed walk does not match the selected arc multiset."
        )

    if traversed_arcs != len(selected_arcs):
        raise ValueError(
            f"Route reconstruction used {traversed_arcs} arcs, but {len(selected_arcs)} "
            "arcs were selected."
        )

    return {
        "ordered_cycle": ordered_cycle,
        "segments": segments,
        "total_time": total_time,
        "total_elevation_gain": total_elevation_gain,
    }