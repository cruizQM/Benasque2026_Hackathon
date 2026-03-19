import pandas as pd
import numpy as np

from icecream import ic


class BenasqueDataLoader:
    def __init__(self, nodes_path, distances_path, gear_filter=None):
        self.nodes_path = nodes_path
        self.distances_path = distances_path
        self.gear_filter = gear_filter

        # DataFrames
        self.nodes_df = None
        self.dist_df = None

        # Derived
        self._distance_matrix = None
        self._elevation_matrix = None
        self._scenic_scores = None
        
    def filter_nodes(self):

        station, gear = self.gear_filter.split("_")
        if self.gear_filter:
            self.nodes_df = self.nodes_df[self.nodes_df[f"{station} gear"] == gear]
        
    def filter_distances(self):
        if self.nodes_df is not None:
            valid_ids = list(self.nodes_df.index)
            self.dist_df = self.dist_df[self.dist_df.index.isin(valid_ids)]
            ic(self.dist_df)
            self.dist_df = self.dist_df[valid_ids]
            
    # -------------------------
    # Load data
    # -------------------------
    def load(self):
        self.nodes_df = pd.read_csv(self.nodes_path, index_col=1)
        self.dist_df = pd.read_csv(self.distances_path, index_col=0)        
        
        self.dist_df.index = self.nodes_df.index # align indices
        self.dist_df.columns = self.nodes_df.index
        
        self.filter_nodes()
        self.filter_distances()
        
        ic(self.dist_df)
        
        self._clean_nodes()
        self._clean_distances()

        self._build_distance_matrix()
        self._build_elevation_matrix()
        self.elevation_df = pd.DataFrame(self._elevation_matrix, index=self.nodes_df.index, columns=self.nodes_df.index)
        self._build_scenic_scores()

    # -------------------------
    # Cleaning
    # -------------------------
    def _clean_nodes(self):
        self.nodes_df.columns = [c.lower().strip() for c in self.nodes_df.columns]

        # Ensure id exists
        if "id" not in self.nodes_df.columns:
            self.nodes_df["id"] = range(len(self.nodes_df))

        self.nodes_df = self.nodes_df.reset_index(drop=True)

    def _clean_distances(self):        
        # Make the matrix symmetric by copying upper triangle to lower triangle
        for i in range(len(self.dist_df)):
             for j in range(i+1, len(self.dist_df)):
                if pd.notna(self.dist_df.iloc[i, j]) and pd.isna(self.dist_df.iloc[j, i]):
                    self.dist_df.iloc[j, i] = self.dist_df.iloc[i, j]
                elif pd.isna(self.dist_df.iloc[i, j]) and pd.notna(self.dist_df.iloc[j, i]):
                    self.dist_df.iloc[i, j] = self.dist_df.iloc[j, i]
        
        # Convert all values to numeric
        self.dist_df = self.dist_df.apply(
            lambda col: col.map(self._convert_to_numeric)
        )

        # # Fill missing with large penalty
        # self.dist_df = self.dist_df.fillna(1e6)
        
        # Fill 0s with small penalty (except diagonal)
        for i in range(len(self.dist_df)):
            for j in range(len(self.dist_df)):
                if i != j and self.dist_df.iloc[i, j] == 0:
                    self.dist_df.iloc[i, j] = 20*(1/60)  # 20 minutes in hours

    # -------------------------
    # Conversion helper
    # -------------------------
    def _convert_to_numeric(self, val):
        if pd.isna(val):
            return np.nan

        if isinstance(val, str):
            # Handle "4'35" format
            if "'" in val:
                try:
                    minutes, seconds = val.split("'")
                    return float(minutes) + float(seconds) / 60
                except:
                    return np.nan

            try:
                return float(val)
            except:
                return np.nan

        return float(val)

    # -------------------------
    # Build matrices
    # -------------------------
    def _build_distance_matrix(self):
        self._distance_matrix = self.dist_df.fillna(1e6).replace(0, 1/12).to_numpy(dtype=float)

    def _build_elevation_matrix(self):
        """
        If elevation per node exists, derive edge elevation gain.
        Otherwise default to zeros.
        """
        if "elevation" in self.nodes_df.columns:
            elevations = self.nodes_df["elevation"].to_numpy()

            n = len(elevations)
            elev_matrix = np.zeros((n, n))

            for i in range(n):
                for j in range(n):
                    gain = elevations[j] - elevations[i]
                    elev_matrix[i, j] = gain if gain > 0 else -gain/2  # penalize descents less than ascents

            self._elevation_matrix = elev_matrix
        else:
            self._elevation_matrix = np.zeros_like(self._distance_matrix)

    def _build_scenic_scores(self):
        """
        Extract scenic score or create default.
        """
        possible_cols = ["scenic", "scenic_score", "score", "value"]

        for col in possible_cols:
            if col in self.nodes_df.columns:
                self._scenic_scores = self.nodes_df[col].to_numpy()
                return

        # Default: all equal
        self._scenic_scores = np.ones(len(self.nodes_df))

    # -------------------------
    # Public API
    # -------------------------
    @property
    def distance_matrix(self):
        return self._distance_matrix

    @property
    def elevation_matrix(self):
        return self._elevation_matrix

    @property
    def scenic_scores(self):
        return self._scenic_scores

    def get_dataframes(self):
        return self.nodes_df, self.dist_df, self.elevation_df

    def get_optimization_inputs(self):
        return {
            "distance": self.distance_matrix,
            "elevation": self.elevation_matrix,
            "scenic": self.scenic_scores,
        }
        
        
def generate_qaoa_inputs(distance_df, elevation_df, p_distance=1.0, p_elevation=1.0):
    """
    Generate QAOA inputs (cost and mixer Hamiltonians) based on the problem data.
    This is a placeholder function and should be implemented according to the specific QAOA formulation.
    """
    num_nodes = distance_df.shape[0]
    # number of edges in the graph (not None)
    list_nodes = distance_df.index.tolist()
    
    ic(distance_df)    
    
    list_edges = []
    for i in range(num_nodes):
        for j in range(num_nodes):
            if not np.isnan(distance_df.iloc[i, j]) and i != j:
                w_ij = p_distance * distance_df.iloc[i, j] + p_elevation * elevation_df.iloc[i, j]
                list_edges.append((i, j, float(w_ij)))
                
    return list_nodes, list_edges