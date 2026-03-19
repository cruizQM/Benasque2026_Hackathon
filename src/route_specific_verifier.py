from typing import Any


def validate_route_constraints(
    route_info: dict,
    max_total_time: float=12.0,
    max_total_elevation_gain: float=2000.0,
    base_node: str = "Benasque",
    verbose: bool = False,
) -> bool | tuple[bool, dict[str, Any]]:
    """
    Validate route-specific constraints for an already reconstructed route.

    This function assumes that the route has already been extracted from a
    structurally valid directed solution, for example via
    `extract_route_with_metrics(...)`.

    The following constraints are checked:

    -------------------------------------------------------------------------
    (1) Base node constraint
        - The ordered cycle must start at the required base node.
        - The ordered cycle must end at the required base node.

    -------------------------------------------------------------------------
    (2) Total travel time bound
        - The total time of the route must not exceed the maximum allowed time.

    -------------------------------------------------------------------------
    (3) Total elevation gain bound
        - The total elevation gain/cost of the route must not exceed the
          maximum allowed elevation gain.

    -------------------------------------------------------------------------

    Parameters
    ----------
    route_info : dict
        Dictionary returned by `extract_route_with_metrics(...)`, expected to
        contain at least:
        - "ordered_cycle"
        - "total_time"
        - "total_elevation_gain"
    max_total_time : float
        Maximum allowed total travel time.
    max_total_elevation_gain : float
        Maximum allowed total elevation gain/cost.
    base_node : str, optional
        Required start/end node of the route.
    verbose : bool, optional
        If False, return only a boolean feasibility flag.
        If True, return (feasible, diagnostics).

    Returns
    -------
    bool
        If verbose=False, returns True if all route-specific constraints are
        satisfied, otherwise False.

    tuple[bool, dict]
        If verbose=True, returns:
        - feasible: bool
        - diagnostics: dict with detailed validation information
    """
    violations: list[str] = []

    ordered_cycle = route_info.get("ordered_cycle")
    total_time = route_info.get("total_time")
    total_elevation_gain = route_info.get("total_elevation_gain")

    # ---------------------------------------------------------------------
    # (0) Basic route_info integrity checks
    # ---------------------------------------------------------------------
    if ordered_cycle is None:
        violations.append("route_info is missing 'ordered_cycle'.")
    elif not isinstance(ordered_cycle, list) or len(ordered_cycle) == 0:
        violations.append("'ordered_cycle' must be a non-empty list.")

    if total_time is None:
        violations.append("route_info is missing 'total_time'.")

    if total_elevation_gain is None:
        violations.append("route_info is missing 'total_elevation_gain'.")

    # ---------------------------------------------------------------------
    # (1) Base node constraint
    # ---------------------------------------------------------------------
    if not violations:
        if ordered_cycle[0] != base_node:
            violations.append(
                f"The route starts at '{ordered_cycle[0]}' instead of the required base '{base_node}'."
            )

        if ordered_cycle[-1] != base_node:
            violations.append(
                f"The route ends at '{ordered_cycle[-1]}' instead of the required base '{base_node}'."
            )

    # ---------------------------------------------------------------------
    # (2) Total travel time bound
    # ---------------------------------------------------------------------
    if not violations:
        if total_time > max_total_time:
            violations.append(
                f"Total time {total_time} exceeds maximum allowed time {max_total_time}."
            )

    # ---------------------------------------------------------------------
    # (3) Total elevation gain bound
    # ---------------------------------------------------------------------
    if not violations:
        if total_elevation_gain > max_total_elevation_gain:
            violations.append(
                f"Total elevation gain {total_elevation_gain} exceeds maximum allowed elevation gain "
                f"{max_total_elevation_gain}."
            )

    feasible = len(violations) == 0

    if not verbose:
        return feasible

    diagnostics = {
        "violations": violations,
        "ordered_cycle": ordered_cycle,
        "total_time": total_time,
        "total_elevation_gain": total_elevation_gain,
        "max_total_time": max_total_time,
        "max_total_elevation_gain": max_total_elevation_gain,
        "base_node": base_node,
    }
    return feasible, diagnostics