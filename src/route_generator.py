import math
import pandas as pd


def extract_route_with_metrics(
    dic_x: dict[tuple[str, str], int],
    distance_df: pd.DataFrame,
    elevation_df: pd.DataFrame,
    base_node: str = "Benasque",
) -> dict:
    """
    Reconstruct the ordered directed cycle from the selected arcs and compute
    total travel time and total elevation cost.

    This function assumes that the selected arcs already correspond to a
    structurally valid directed route.

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

    successors = {}
    for u, v in selected_arcs:
        if u in successors:
            raise ValueError(
                f"Node '{u}' has more than one selected outgoing arc; "
                "cannot reconstruct a unique route."
            )
        successors[u] = v

    if base_node not in successors:
        raise ValueError(f"Base node '{base_node}' has no selected outgoing arc.")

    ordered_cycle = [base_node]
    current = base_node
    seen = {base_node}

    while True:
        nxt = successors.get(current)
        if nxt is None:
            raise ValueError(
                f"Node '{current}' has no successor during route reconstruction."
            )

        ordered_cycle.append(nxt)

        if nxt == base_node:
            break

        if nxt in seen:
            raise ValueError(
                f"Route reconstruction revisits node '{nxt}' before returning to base."
            )

        seen.add(nxt)
        current = nxt

    segments = []
    total_time = 0.0
    total_elevation_gain = 0.0

    traversed_arcs = 0
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

    if traversed_arcs != len(selected_arcs):
        raise ValueError(
            f"Route reconstruction used {traversed_arcs} arcs, but {len(selected_arcs)} "
            "arcs were selected. The selected arcs may contain disconnected components."
        )

    return {
        "ordered_cycle": ordered_cycle,
        "segments": segments,
        "total_time": total_time,
        "total_elevation_gain": total_elevation_gain,
    }