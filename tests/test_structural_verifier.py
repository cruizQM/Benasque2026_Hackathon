"""
Test suite for the directed structural route verifier.

This module validates the correctness of the function
`validate_directed_route_structure`, which checks whether a candidate
solution (dic_x, dic_y) represents a valid directed cycle (route).

The tests are designed to cover all key structural constraints enforced
by the verifier:

---------------------------------------------------------------------
(1) Valid directed cycle
    - Ensures that a correct solution (single directed cycle over visited nodes)
      is accepted.
    - Tested in both:
        * non-verbose mode (returns only True/False)
        * verbose mode (returns diagnostics, including ordered cycle)

---------------------------------------------------------------------
(2) Base node constraint
    - Verifies that the route must include the base node.
    - A solution where the base node is not visited must be rejected.

---------------------------------------------------------------------
(3) Arc-node consistency
    - Ensures that selected arcs only connect visited nodes.
    - Any arc touching an unvisited node should invalidate the solution.

---------------------------------------------------------------------
(4) Degree constraints
    - For visited nodes:
        * exactly one outgoing arc
        * exactly one incoming arc
    - For unvisited nodes:
        * zero incoming and outgoing arcs
    - Violations (e.g., multiple outgoing arcs) are detected.

---------------------------------------------------------------------
(5) Subtour detection (global connectivity)
    - Ensures that all visited nodes form a single cycle.
    - Disconnected cycles (subtours) must be rejected.

---------------------------------------------------------------------
(6) Unvisited node isolation
    - Verifies that unvisited nodes are not connected to the route.
    - Any selected arc involving an unvisited node is invalid.

---------------------------------------------------------------------

Design notes:
- Tests use small handcrafted graphs for clarity and determinism.
- Error checking is done via substring matching to avoid brittle tests.
- Both boolean output and verbose diagnostics are validated.

This suite provides a minimal but comprehensive validation of the
structural constraints required for feasible route solutions in the
directed formulation.
"""

import unittest

from src.structural_verifier import validate_directed_route_structure


class TestStructuralVerifier(unittest.TestCase):
    def setUp(self):
        # Common small node set for all tests
        self.nodes = ["A", "B", "C", "D"]
        self.base_node = "A"

    def test_valid_directed_cycle_non_verbose(self):
        dic_y = {"A": 1, "B": 1, "C": 1, "D": 0}
        dic_x = {
            ("A", "B"): 1,
            ("B", "C"): 1,
            ("C", "A"): 1,
            ("A", "C"): 0,
            ("C", "B"): 0,
            ("B", "A"): 0,
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

    def test_valid_directed_cycle_verbose(self):
        dic_y = {"A": 1, "B": 1, "C": 1, "D": 0}
        dic_x = {
            ("A", "B"): 1,
            ("B", "C"): 1,
            ("C", "A"): 1,
            ("A", "C"): 0,
            ("C", "B"): 0,
            ("B", "A"): 0,
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
        self.assertEqual(diagnostics["ordered_cycle"], ["A", "B", "C", "A"])
        self.assertEqual(diagnostics["errors"], [])

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
            ("B", "C"): 1,  # C is unvisited
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

    def test_wrong_out_degree_for_visited_node(self):
        dic_y = {"A": 1, "B": 1, "C": 1, "D": 0}
        dic_x = {
            ("A", "B"): 1,
            ("A", "C"): 1,  # A has two outgoing arcs
            ("B", "A"): 1,
            ("C", "A"): 1,
        }

        feasible, diagnostics = validate_directed_route_structure(
            dic_x=dic_x,
            dic_y=dic_y,
            base_node=self.base_node,
            verbose=True,
        )

        self.assertFalse(feasible)
        self.assertTrue(
            any("Visited node 'A' has out-degree 2 instead of 1." in err for err in diagnostics["errors"])
        )

    def test_subtour_disconnected_cycles(self):
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
            any("misses visited nodes" in err.lower() for err in diagnostics["errors"])
            or any("revisits node" in err.lower() for err in diagnostics["errors"])
        )

    def test_unvisited_node_with_selected_arc(self):
        dic_y = {"A": 1, "B": 1, "C": 0, "D": 0}
        dic_x = {
            ("A", "B"): 1,
            ("B", "A"): 1,
            ("C", "A"): 1,  # unvisited node C has outgoing arc
        }

        feasible, diagnostics = validate_directed_route_structure(
            dic_x=dic_x,
            dic_y=dic_y,
            base_node=self.base_node,
            verbose=True,
        )

        self.assertFalse(feasible)
        self.assertTrue(
            any("Unvisited node 'C' has out-degree 1 instead of 0." in err for err in diagnostics["errors"])
        )


if __name__ == "__main__":
    unittest.main()