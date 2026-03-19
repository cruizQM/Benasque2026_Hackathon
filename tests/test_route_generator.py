# tests/test_route_generator.py
import unittest
import pandas as pd
import numpy as np

from src.route_generator import extract_route_with_metrics


class TestRouteGenerator(unittest.TestCase):
    def setUp(self):
        self.nodes = ["A", "B", "C", "D"]

        self.distance_df = pd.DataFrame(
            [
                [0.0, 1.0, 2.0, 3.0],
                [1.0, 0.0, 4.0, 5.0],
                [2.0, 4.0, 0.0, 6.0],
                [3.0, 5.0, 6.0, 0.0],
            ],
            index=self.nodes,
            columns=self.nodes,
        )

        self.elevation_df = pd.DataFrame(
            [
                [0.0, 10.0, 20.0, 30.0],
                [10.0, 0.0, 40.0, 50.0],
                [20.0, 40.0, 0.0, 60.0],
                [30.0, 50.0, 60.0, 0.0],
            ],
            index=self.nodes,
            columns=self.nodes,
        )

    def test_extract_simple_cycle(self):
        dic_x = {
            ("A", "B"): 1,
            ("B", "C"): 1,
            ("C", "A"): 1,
            ("A", "C"): 0,
            ("C", "B"): 0,
            ("B", "A"): 0,
        }

        route_info = extract_route_with_metrics(
            dic_x=dic_x,
            distance_df=self.distance_df,
            elevation_df=self.elevation_df,
            base_node="A",
        )

        self.assertEqual(route_info["ordered_cycle"], ["A", "B", "C", "A"])
        self.assertEqual(len(route_info["segments"]), 3)
        self.assertAlmostEqual(route_info["total_time"], 1.0 + 4.0 + 2.0)
        self.assertAlmostEqual(route_info["total_elevation_gain"], 10.0 + 40.0 + 20.0)

    def test_extract_eulerian_walk_with_repeated_node(self):
        dic_x = {
            ("A", "B"): 1,
            ("B", "C"): 1,
            ("C", "B"): 1,
            ("B", "A"): 1,
            ("A", "C"): 0,
            ("C", "A"): 0,
        }

        route_info = extract_route_with_metrics(
            dic_x=dic_x,
            distance_df=self.distance_df,
            elevation_df=self.elevation_df,
            base_node="A",
        )

        self.assertEqual(route_info["ordered_cycle"], ["A", "B", "C", "B", "A"])
        self.assertEqual(len(route_info["segments"]), 4)
        self.assertAlmostEqual(route_info["total_time"], 1.0 + 4.0 + 4.0 + 1.0)
        self.assertAlmostEqual(route_info["total_elevation_gain"], 10.0 + 40.0 + 40.0 + 10.0)

    def test_no_selected_arcs_raises(self):
        dic_x = {
            ("A", "B"): 0,
            ("B", "A"): 0,
        }

        with self.assertRaises(ValueError) as ctx:
            extract_route_with_metrics(
                dic_x=dic_x,
                distance_df=self.distance_df,
                elevation_df=self.elevation_df,
                base_node="A",
            )

        self.assertIn("No selected arcs were found", str(ctx.exception))

    def test_base_node_not_incident_raises(self):
        dic_x = {
            ("B", "C"): 1,
            ("C", "B"): 1,
            ("A", "B"): 0,
            ("B", "A"): 0,
        }

        with self.assertRaises(ValueError) as ctx:
            extract_route_with_metrics(
                dic_x=dic_x,
                distance_df=self.distance_df,
                elevation_df=self.elevation_df,
                base_node="A",
            )

        self.assertIn("Base node 'A' is not incident", str(ctx.exception))

    def test_missing_time_data_raises(self):
        dic_x = {
            ("A", "B"): 1,
            ("B", "A"): 1,
        }

        bad_distance_df = self.distance_df.copy()
        bad_distance_df = bad_distance_df.drop(columns=["B"])

        with self.assertRaises(ValueError) as ctx:
            extract_route_with_metrics(
                dic_x=dic_x,
                distance_df=bad_distance_df,
                elevation_df=self.elevation_df,
                base_node="A",
            )

        self.assertIn("Missing time data for arc (A, B)", str(ctx.exception))

    def test_missing_elevation_data_raises(self):
        dic_x = {
            ("A", "B"): 1,
            ("B", "A"): 1,
        }

        bad_elevation_df = self.elevation_df.copy()
        bad_elevation_df = bad_elevation_df.drop(index=["A"])

        with self.assertRaises(ValueError) as ctx:
            extract_route_with_metrics(
                dic_x=dic_x,
                distance_df=self.distance_df,
                elevation_df=bad_elevation_df,
                base_node="A",
            )

        self.assertIn("Missing elevation data for arc (A, B)", str(ctx.exception))

    def test_invalid_time_value_raises(self):
        dic_x = {
            ("A", "B"): 1,
            ("B", "A"): 1,
        }

        bad_distance_df = self.distance_df.copy()
        bad_distance_df.loc["A", "B"] = np.nan

        with self.assertRaises(ValueError) as ctx:
            extract_route_with_metrics(
                dic_x=dic_x,
                distance_df=bad_distance_df,
                elevation_df=self.elevation_df,
                base_node="A",
            )

        self.assertIn("Invalid time value for arc (A, B)", str(ctx.exception))

    def test_invalid_elevation_value_raises(self):
        dic_x = {
            ("A", "B"): 1,
            ("B", "A"): 1,
        }

        bad_elevation_df = self.elevation_df.copy()
        bad_elevation_df.loc["A", "B"] = np.nan

        with self.assertRaises(ValueError) as ctx:
            extract_route_with_metrics(
                dic_x=dic_x,
                distance_df=self.distance_df,
                elevation_df=bad_elevation_df,
                base_node="A",
            )

        self.assertIn("Invalid elevation value for arc (A, B)", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()