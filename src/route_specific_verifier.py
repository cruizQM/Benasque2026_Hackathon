from typing import Any
import math


def validate_route_constraints(
    route_info: dict,
    max_total_time: float = 12.0,
    max_total_elevation_gain: float = 2000.0,
    base_node: str = "Benasque",
    verbose: bool = False,
) -> bool | tuple[bool, dict[str, Any]]:
    """
    Validate route-specific constraints for an already reconstructed route.

    This function assumes that the route has already been extracted from a
    structurally valid directed solution, for example via
    `extract_route_with_metrics(...)`.

    The reconstructed route is interpreted as a closed walk that:
        - starts at the required base node,
        - ends at the required base node,
        - traverses all selected arcs,
        - may revisit intermediate nodes if needed.

    The following constraints are checked:

    -------------------------------------------------------------------------
    (1) Route info integrity
        - route_info must contain:
            * "ordered_cycle"
            * "total_time"
            * "total_elevation_gain"
        - "ordered_cycle" must be a non-empty list with at least two nodes.
        - total_time and total_elevation_gain must be finite numeric values.

    -------------------------------------------------------------------------
    (2) Base node constraint
        - The reconstructed walk must start at the required base node.
        - The reconstructed walk must end at the required base node.

    -------------------------------------------------------------------------
    (3) Total travel time bound
        - The total time of the route must not exceed the maximum allowed time.

    -------------------------------------------------------------------------
    (4) Total elevation gain bound
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
    max_total_time : float, optional
        Maximum allowed total travel time.
    max_total_elevation_gain : float, optional
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
    segments = route_info.get("segments", None)

    # ---------------------------------------------------------------------
    # (1) Basic route_info integrity checks
    # ---------------------------------------------------------------------
    if ordered_cycle is None:
        violations.append("route_info is missing 'ordered_cycle'.")
    elif not isinstance(ordered_cycle, list):
        violations.append("'ordered_cycle' must be a list.")
    elif len(ordered_cycle) < 2:
        violations.append("'ordered_cycle' must contain at least two nodes.")

    if total_time is None:
        violations.append("route_info is missing 'total_time'.")
    elif not isinstance(total_time, (int, float)) or not math.isfinite(total_time):
        violations.append(f"'total_time' must be a finite numeric value, got {total_time}.")

    if total_elevation_gain is None:
        violations.append("route_info is missing 'total_elevation_gain'.")
    elif not isinstance(total_elevation_gain, (int, float)) or not math.isfinite(total_elevation_gain):
        violations.append(
            f"'total_elevation_gain' must be a finite numeric value, got {total_elevation_gain}."
        )

    # Optional consistency check with segments, if available
    if segments is not None:
        if not isinstance(segments, list):
            violations.append("'segments' must be a list when present.")
        elif isinstance(ordered_cycle, list) and len(ordered_cycle) >= 2:
            expected_num_segments = len(ordered_cycle) - 1
            if len(segments) != expected_num_segments:
                violations.append(
                    f"'segments' has length {len(segments)}, but expected {expected_num_segments} "
                    "from the ordered walk."
                )

    # ---------------------------------------------------------------------
    # (2) Base node constraint
    # ---------------------------------------------------------------------
    if isinstance(ordered_cycle, list) and len(ordered_cycle) >= 2:
        if ordered_cycle[0] != base_node:
            violations.append(
                f"The route starts at '{ordered_cycle[0]}' instead of the required base '{base_node}'."
            )

        if ordered_cycle[-1] != base_node:
            violations.append(
                f"The route ends at '{ordered_cycle[-1]}' instead of the required base '{base_node}'."
            )

    # ---------------------------------------------------------------------
    # (3) Total travel time bound
    # ---------------------------------------------------------------------
    if isinstance(total_time, (int, float)) and math.isfinite(total_time):
        if total_time > max_total_time:
            violations.append(
                f"Total time {total_time} exceeds maximum allowed time {max_total_time}."
            )

    # ---------------------------------------------------------------------
    # (4) Total elevation gain bound
    # ---------------------------------------------------------------------
    if isinstance(total_elevation_gain, (int, float)) and math.isfinite(total_elevation_gain):
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
        "segments": segments,
        "total_time": total_time,
        "total_elevation_gain": total_elevation_gain,
        "max_total_time": max_total_time,
        "max_total_elevation_gain": max_total_elevation_gain,
        "base_node": base_node,
    }
    return feasible, diagnostics