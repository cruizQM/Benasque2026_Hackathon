"""
Test suite for the graph-level structural route verifier.

This module validates the correctness of the function
`validate_directed_route_structure`, which checks whether a decoded
candidate solution (dic_x, dic_y) passes the structural prechecks that
can be verified directly from the selected nodes and directed arcs,
without reconstructing an explicit route.

The verifier is intended as a graph-level filter before route generation.
It does NOT enforce a single simple directed cycle. Instead, it checks
the graph-level conditions required for the existence of a closed
directed walk traversing all selected arcs.

The tests cover the following structural conditions:

---------------------------------------------------------------------
(1) Valid balanced connected selected structure
    - A selected set of arcs connecting selected nodes in a single
      connected component containing the base node is accepted,
      provided that all incident nodes satisfy:
          in-degree == out-degree
    - Tested in both:
        * non-verbose mode (returns only True/False)
        * verbose mode (returns diagnostics)

---------------------------------------------------------------------
(2) Base node constraint
    - The base node must exist in dic_y and must be selected.

---------------------------------------------------------------------
(3) Arc-node consistency
    - Every selected arc must connect two selected nodes.
    - Any selected arc touching an unvisited node is invalid.

---------------------------------------------------------------------
(4) Self-loop rejection
    - Selected arcs of the form (u, u) are not allowed.

---------------------------------------------------------------------
(5) Connectivity
    - The selected structure must form a single connected component in
      the underlying undirected sense.
    - Disconnected selected components must be rejected.

---------------------------------------------------------------------
(6) Isolated selected nodes
    - A selected node with no incident selected arc is invalid.

---------------------------------------------------------------------
(7) Non-empty selected structure
    - At least one selected arc must exist.

---------------------------------------------------------------------
(8) Eulerian balance
    - For every node incident to selected arcs:
          in-degree == out-degree
    - Unbalanced nodes must be rejected.

---------------------------------------------------------------------

Design notes:
- Tests use small handcrafted examples for clarity and determinism.
- Error checking is done via substring matching to avoid brittle tests.
- Both boolean output and verbose diagnostics are validated.

This suite validates the structural prechecks required before attempting
explicit route generation.
"""

import unittest

from src.structural_verifier import validate_directed_route_structure


class TestStructuralVerifier(unittest.TestCase):
    def setUp(self):
        self.nodes = ["A", "B", "C", "D"]
        self.base_node = "A"

    def test_valid_balanced_connected_structure_non_verbose(self):
        dic_y = {"A": 1, "B": 1, "C": 1, "D": 0}
        dic_x = {
            ("A", "B"): 1,
            ("B", "C"): 1,
            ("C", "B"): 1,
            ("B", "A"): 1,
            ("A", "C"): 0,
            ("C", "A"): 0,
            ("D", "A"): 0,
            ("A", "D"): 0,
        }

        result = validate_directed_route_structure(
            dic_x=dic_x,
            dic_y=dic_y,
            base_node=self.base_node,
            verbose=False,
        )

        self.assertTrue(result)

    def test_valid_balanced_connected_structure_verbose(self):
        dic_y = {"A": 1, "B": 1, "C": 1, "D": 0}
        dic_x = {
            ("A", "B"): 1,
            ("B", "C"): 1,
            ("C", "B"): 1,
            ("B", "A"): 1,
            ("A", "C"): 0,
            ("C", "A"): 0,
            ("D", "A"): 0,
            ("A", "D"): 0,
        }

        feasible, diagnostics = validate_directed_route_structure(
            dic_x=dic_x,
            dic_y=dic_y,
            base_node=self.base_node,
            verbose=True,
        )

        self.assertTrue(feasible)
        self.assertEqual(diagnostics["errors"], [])
        self.assertEqual(set(diagnostics["selected_nodes"]), {"A", "B", "C"})
        self.assertEqual(set(diagnostics["incident_nodes"]), {"A", "B", "C"})
        self.assertEqual(diagnostics["in_degree"]["A"], 1)
        self.assertEqual(diagnostics["out_degree"]["A"], 1)
        self.assertEqual(diagnostics["in_degree"]["B"], 2)
        self.assertEqual(diagnostics["out_degree"]["B"], 2)
        self.assertEqual(diagnostics["in_degree"]["C"], 1)
        self.assertEqual(diagnostics["out_degree"]["C"], 1)

    def test_base_node_not_visited(self):
        dic_y = {"A": 0, "B": 1, "C": 1, "D": 0}
        dic_x = {
            ("B", "C"): 1,
            ("C", "B"): 1,
        }

        feasible, diagnostics = validate_directed_route_structure(
            dic_x=dic_x,
            dic_y=dic_y,
            base_node=self.base_node,
            verbose=True,
        )

        self.assertFalse(feasible)
        self.assertTrue(
            any("Base node 'A' is not marked as visited." in err for err in diagnostics["errors"])
        )

    def test_selected_arc_touches_unvisited_node(self):
        dic_y = {"A": 1, "B": 1, "C": 0, "D": 0}
        dic_x = {
            ("A", "B"): 1,
            ("B", "C"): 1,
            ("B", "A"): 1,
        }

        feasible, diagnostics = validate_directed_route_structure(
            dic_x=dic_x,
            dic_y=dic_y,
            base_node=self.base_node,
            verbose=True,
        )

        self.assertFalse(feasible)
        self.assertTrue(
            any("enters unvisited node 'C'" in err for err in diagnostics["errors"])
        )

    def test_self_loop_is_rejected(self):
        dic_y = {"A": 1, "B": 1, "C": 0, "D": 0}
        dic_x = {
            ("A", "A"): 1,
            ("A", "B"): 1,
            ("B", "A"): 1,
        }

        feasible, diagnostics = validate_directed_route_structure(
            dic_x=dic_x,
            dic_y=dic_y,
            base_node=self.base_node,
            verbose=True,
        )

        self.assertFalse(feasible)
        self.assertTrue(
            any("Self-loop (A, A) is not allowed." in err for err in diagnostics["errors"])
        )

    def test_disconnected_selected_structure(self):
        dic_y = {"A": 1, "B": 1, "C": 1, "D": 1}
        dic_x = {
            ("A", "B"): 1,
            ("B", "A"): 1,
            ("C", "D"): 1,
            ("D", "C"): 1,
        }

        feasible, diagnostics = validate_directed_route_structure(
            dic_x=dic_x,
            dic_y=dic_y,
            base_node=self.base_node,
            verbose=True,
        )

        self.assertFalse(feasible)
        self.assertTrue(
            any("not connected" in err.lower() for err in diagnostics["errors"])
        )

    def test_selected_node_with_no_incident_arc(self):
        dic_y = {"A": 1, "B": 1, "C": 1, "D": 0}
        dic_x = {
            ("A", "B"): 1,
            ("B", "A"): 1,
        }

        feasible, diagnostics = validate_directed_route_structure(
            dic_x=dic_x,
            dic_y=dic_y,
            base_node=self.base_node,
            verbose=True,
        )

        self.assertFalse(feasible)
        self.assertTrue(
            any("Selected nodes with no incident selected arc" in err for err in diagnostics["errors"])
        )

    def test_no_selected_arcs(self):
        dic_y = {"A": 1, "B": 0, "C": 0, "D": 0}
        dic_x = {
            ("A", "B"): 0,
            ("B", "A"): 0,
        }

        feasible, diagnostics = validate_directed_route_structure(
            dic_x=dic_x,
            dic_y=dic_y,
            base_node=self.base_node,
            verbose=True,
        )

        self.assertFalse(feasible)
        self.assertTrue(
            any("No directed arcs are selected." in err for err in diagnostics["errors"])
        )

    def test_base_selected_but_not_incident_to_any_arc(self):
        dic_y = {"A": 1, "B": 1, "C": 1, "D": 0}
        dic_x = {
            ("B", "C"): 1,
            ("C", "B"): 1,
        }

        feasible, diagnostics = validate_directed_route_structure(
            dic_x=dic_x,
            dic_y=dic_y,
            base_node=self.base_node,
            verbose=True,
        )

        self.assertFalse(feasible)
        self.assertTrue(
            any("Selected nodes with no incident selected arc" in err for err in diagnostics["errors"])
        )

    def test_unbalanced_node_is_rejected(self):
        dic_y = {"A": 1, "B": 1, "C": 1, "D": 0}
        dic_x = {
            ("A", "B"): 1,
            ("B", "C"): 1,
            ("C", "A"): 1,
            ("A", "C"): 1,  # A becomes unbalanced: out=2, in=1
        }

        feasible, diagnostics = validate_directed_route_structure(
            dic_x=dic_x,
            dic_y=dic_y,
            base_node=self.base_node,
            verbose=True,
        )

        self.assertFalse(feasible)
        self.assertTrue(
            any("not balanced" in err.lower() for err in diagnostics["errors"])
        )

    def test_multiple_outgoing_arcs_can_be_valid_if_balanced(self):
        dic_y = {"A": 1, "B": 1, "C": 1, "D": 1}
        dic_x = {
            ("A", "B"): 1,
            ("B", "A"): 1,
            ("A", "C"): 1,
            ("C", "A"): 1,
            ("B", "D"): 1,
            ("D", "B"): 1,
        }

        feasible, diagnostics = validate_directed_route_structure(
            dic_x=dic_x,
            dic_y=dic_y,
            base_node=self.base_node,
            verbose=True,
        )

        self.assertTrue(feasible)
        self.assertEqual(diagnostics["errors"], [])


if __name__ == "__main__":
    unittest.main()