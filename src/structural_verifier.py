#src/structural_verifier.py
from typing import Any


def validate_directed_route_structure(
    dic_x: dict[tuple[str, str], int],
    dic_y: dict[str, int],
    base_node: str,
    verbose: bool = False,
) -> bool | tuple[bool, dict[str, Any]]:
    """
    Validate whether a decoded directed solution defines a single closed route.

    This function checks that a candidate solution (given by dic_x and dic_y)
    represents a valid directed cycle (route) satisfying structural constraints.

    The following conditions are enforced:

    -------------------------------------------------------------------------
    (1) Arc validity and node consistency
        - Every selected arc (u, v) must refer to existing nodes.
        - No self-loops are allowed: (u, u) is forbidden.
        - If an arc (u, v) is selected, then both nodes must be visited:
              x_(u,v) = 1  =>  y_u = 1 and y_v = 1

    -------------------------------------------------------------------------
    (2) Degree constraints (flow conservation)
        For each node:
        - If the node is visited (y_u = 1):
            * exactly one outgoing arc must be selected
            * exactly one incoming arc must be selected
        - If the node is NOT visited (y_u = 0):
            * no incoming arcs must be selected
            * no outgoing arcs must be selected

        This enforces that visited nodes behave like a proper cycle,
        and unvisited nodes are completely disconnected.

    -------------------------------------------------------------------------
    (3) Base node constraint
        - The base node must exist in dic_y
        - The base node must be visited (y_base = 1)

    -------------------------------------------------------------------------
    (4) Single-cycle (no subtours)
        - The selected arcs must define exactly one directed cycle.
        - Starting from the base node and following successors:
            * we must return to the base
            * we must visit ALL visited nodes exactly once
            * no node can be revisited before closing the cycle

    -------------------------------------------------------------------------
    (5) Arc count consistency
        - A valid directed cycle with N visited nodes must have exactly N arcs.

    -------------------------------------------------------------------------

    Parameters
    ----------
    dic_x : dict[(str, str), int]
        Directed arc-selection dictionary. dic_x[(u, v)] = 1 means that
        the directed arc u -> v is selected.
    dic_y : dict[str, int]
        Node-selection dictionary. dic_y[u] = 1 means that node u is visited.
    base_node : str
        Required start/end node of the route.
    verbose : bool, optional
        If False, return only a boolean feasibility flag.
        If True, return (feasible, diagnostics).

    Returns
    -------
    bool
        If verbose=False, returns True if the route is structurally valid,
        otherwise False.

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

    in_degree = {node: 0 for node in dic_y}
    out_degree = {node: 0 for node in dic_y}
    successors: dict[str, str] = {}

    # 1. Basic checks on selected arcs
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

        out_degree[u] += 1
        in_degree[v] += 1

    # 2. Degree conditions
    for node in dic_y:
        visited = dic_y[node] == 1

        if visited:
            if out_degree[node] != 1:
                errors.append(
                    f"Visited node '{node}' has out-degree {out_degree[node]} instead of 1."
                )
            if in_degree[node] != 1:
                errors.append(
                    f"Visited node '{node}' has in-degree {in_degree[node]} instead of 1."
                )
        else:
            if out_degree[node] != 0:
                errors.append(
                    f"Unvisited node '{node}' has out-degree {out_degree[node]} instead of 0."
                )
            if in_degree[node] != 0:
                errors.append(
                    f"Unvisited node '{node}' has in-degree {in_degree[node]} instead of 0."
                )

    # 3. Base node must be visited
    if base_node not in dic_y:
        errors.append(f"Base node '{base_node}' is not present in dic_y.")
    elif dic_y[base_node] != 1:
        errors.append(f"Base node '{base_node}' is not marked as visited.")

    ordered_cycle = None

    # 4. Single-cycle reconstruction only if local constraints passed
    if not errors:
        for u, v in selected_arcs:
            if u in successors:
                errors.append(
                    f"Node '{u}' has more than one selected outgoing arc."
                )
            successors[u] = v

        if not errors:
            ordered_cycle = [base_node]
            seen = {base_node}
            current = base_node

            while True:
                if current not in successors:
                    errors.append(
                        f"Node '{current}' has no selected outgoing arc during traversal."
                    )
                    ordered_cycle = None
                    break

                nxt = successors[current]
                ordered_cycle.append(nxt)

                if nxt == base_node:
                    break

                if nxt in seen:
                    errors.append(
                        f"Traversal revisits node '{nxt}' before returning to the base."
                    )
                    ordered_cycle = None
                    break

                seen.add(nxt)
                current = nxt

            if ordered_cycle is not None:
                cycle_node_set = set(ordered_cycle[:-1])

                if cycle_node_set != selected_node_set:
                    missing = selected_node_set - cycle_node_set
                    extra = cycle_node_set - selected_node_set

                    if missing:
                        errors.append(
                            f"The cycle misses visited nodes: {sorted(missing)}."
                        )
                    if extra:
                        errors.append(
                            f"The cycle includes nodes not marked as visited: {sorted(extra)}."
                        )
                    ordered_cycle = None

                if len(selected_arcs) != len(selected_nodes):
                    errors.append(
                        f"A valid directed cycle should have the same number of selected arcs "
                        f"and visited nodes, but got {len(selected_arcs)} arcs and "
                        f"{len(selected_nodes)} visited nodes."
                    )
                    ordered_cycle = None

    feasible = len(errors) == 0

    if not verbose:
        return feasible

    diagnostics = {
        "errors": errors,
        "selected_nodes": selected_nodes,
        "selected_arcs": selected_arcs,
        "in_degree": in_degree,
        "out_degree": out_degree,
        "ordered_cycle": ordered_cycle,
    }
    return feasible, diagnostics