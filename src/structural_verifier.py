# src/structural_verifier.py
from collections import deque
from typing import Any


def validate_directed_route_structure(
    dic_x: dict[tuple[str, str], int],
    dic_y: dict[str, int],
    base_node: str,
    verbose: bool = False,
) -> bool | tuple[bool, dict[str, Any]]:
    """
    Validate graph-level structural constraints for a decoded directed solution.

    This function performs only the checks that can be verified directly from
    the selected nodes and arcs, without reconstructing an explicit route.

    The selected directed arcs are interpreted as defining a candidate directed
    subgraph from which we later want to generate a closed walk that:
        - starts at the base node,
        - ends at the base node,
        - traverses all selected arcs,
        - and therefore also covers all selected nodes incident to those arcs.

    Structural feasibility here means that the candidate passes the necessary
    graph-level conditions for the existence of such a closed walk.

    The following conditions are enforced:

    -------------------------------------------------------------------------
    (1) Base node constraint
        - The base node must exist in dic_y.
        - The base node must be selected (visited).

    -------------------------------------------------------------------------
    (2) Non-empty selected structure
        - At least one directed arc must be selected.

    -------------------------------------------------------------------------
    (3) Arc validity and node consistency
        - Every selected arc (u, v) must refer to existing nodes.
        - No self-loops are allowed: (u, u) is forbidden.
        - If an arc (u, v) is selected, then both endpoint nodes must be
          selected:
              x_(u,v) = 1  =>  y_u = 1 and y_v = 1

    -------------------------------------------------------------------------
    (4) Selected-node incidence consistency
        - Every selected node must be incident to at least one selected arc.
        - This prevents isolated selected nodes that cannot belong to the walk.

    -------------------------------------------------------------------------
    (5) Connectivity of the selected structure
        - The selected structure must form a single connected component when
          viewed as an undirected graph.
        - The base node must belong to that connected component.

        This ensures that the selected structure is all in one piece.

    -------------------------------------------------------------------------
    (6) Directed degree balance (Eulerian balance)
        - For every node incident to selected arcs:
              in-degree(node) == out-degree(node)

        This is the graph-level condition needed for the existence of a closed
        directed walk traversing all selected arcs.

    -------------------------------------------------------------------------

    Parameters
    ----------
    dic_x : dict[(str, str), int]
        Directed arc-selection dictionary. dic_x[(u, v)] = 1 means that
        the directed arc u -> v is selected.
    dic_y : dict[str, int]
        Node-selection dictionary. dic_y[u] = 1 means that node u is selected.
    base_node : str
        Required base node of the route.
    verbose : bool, optional
        If False, return only a boolean feasibility flag.
        If True, return (feasible, diagnostics).

    Returns
    -------
    bool
        If verbose=False, returns True if the candidate passes the structural
        prechecks, otherwise False.

    tuple[bool, dict]
        If verbose=True, returns:
        - feasible: bool
        - diagnostics: dict with detailed validation information
    """
    errors: list[str] = []

    all_nodes = set(dic_y.keys())
    selected_nodes = [node for node, val in dic_y.items() if val == 1]
    selected_node_set = set(selected_nodes)
    selected_arcs = [(u, v) for (u, v), val in dic_x.items() if val == 1]

    # Degree bookkeeping for Eulerian balance
    in_degree = {node: 0 for node in dic_y}
    out_degree = {node: 0 for node in dic_y}

    # ---------------------------------------------------------------------
    # (1) Base node constraint
    # ---------------------------------------------------------------------
    if base_node not in dic_y:
        errors.append(f"Base node '{base_node}' is not present in dic_y.")
    elif dic_y[base_node] != 1:
        errors.append(f"Base node '{base_node}' is not marked as visited.")

    # ---------------------------------------------------------------------
    # (2) Non-empty selected structure
    # ---------------------------------------------------------------------
    if len(selected_arcs) == 0:
        errors.append("No directed arcs are selected.")

    # Data collected for diagnostics and connectivity
    incident_nodes = set()
    undirected_adjacency = {node: set() for node in dic_y}

    # ---------------------------------------------------------------------
    # (3) Arc validity and node consistency
    # ---------------------------------------------------------------------
    for u, v in selected_arcs:
        if u not in all_nodes:
            errors.append(f"Selected arc ({u}, {v}) uses unknown start node '{u}'.")
            continue

        if v not in all_nodes:
            errors.append(f"Selected arc ({u}, {v}) uses unknown end node '{v}'.")
            continue

        if u == v:
            errors.append(f"Self-loop ({u}, {v}) is not allowed.")

        if dic_y.get(u, 0) != 1:
            errors.append(f"Selected arc ({u}, {v}) leaves unvisited node '{u}'.")

        if dic_y.get(v, 0) != 1:
            errors.append(f"Selected arc ({u}, {v}) enters unvisited node '{v}'.")

        incident_nodes.add(u)
        incident_nodes.add(v)

        out_degree[u] += 1
        in_degree[v] += 1

        # Build underlying undirected adjacency for connectivity check
        undirected_adjacency[u].add(v)
        undirected_adjacency[v].add(u)

    # ---------------------------------------------------------------------
    # (4) Selected-node incidence consistency
    # ---------------------------------------------------------------------
    isolated_selected_nodes = selected_node_set - incident_nodes
    if isolated_selected_nodes:
        errors.append(
            f"Selected nodes with no incident selected arc: {sorted(isolated_selected_nodes)}."
        )

    # ---------------------------------------------------------------------
    # (5) Connectivity of the selected structure (undirected sense)
    # ---------------------------------------------------------------------
    if not errors:
        if base_node not in incident_nodes:
            errors.append(
                f"Base node '{base_node}' is selected but has no incident selected arc."
            )
        else:
            visited = set()
            queue = deque([base_node])

            while queue:
                node = queue.popleft()
                if node in visited:
                    continue
                visited.add(node)

                for neigh in undirected_adjacency[node]:
                    if neigh not in visited:
                        queue.append(neigh)

            if visited != incident_nodes:
                missing = incident_nodes - visited
                errors.append(
                    f"The selected structure is not connected. "
                    f"Nodes not connected to the base component: {sorted(missing)}."
                )

    # ---------------------------------------------------------------------
    # (6) Directed degree balance (Eulerian balance)
    # ---------------------------------------------------------------------
    if not errors:
        for node in incident_nodes:
            if in_degree[node] != out_degree[node]:
                errors.append(
                    f"Node '{node}' is not balanced: in-degree = {in_degree[node]}, "
                    f"out-degree = {out_degree[node]}."
                )

    feasible = len(errors) == 0

    if not verbose:
        return feasible

    diagnostics = {
        "errors": errors,
        "selected_nodes": selected_nodes,
        "selected_arcs": selected_arcs,
        "incident_nodes": sorted(incident_nodes),
        "in_degree": in_degree,
        "out_degree": out_degree,
        "base_node": base_node,
    }
    return feasible, diagnostics