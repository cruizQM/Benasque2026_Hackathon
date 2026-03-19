
from abc import ABC, abstractmethod

from ortools.sat.python import cp_model


class RouteSolver(ABC):
    def __init__(self, distance, elevation, scenic,
                 max_distance, max_elevation,
                 alpha=1.0, beta=1.0):
        self.distance = distance
        self.elevation = elevation
        self.scenic = scenic
        self.max_distance = max_distance
        self.max_elevation = max_elevation
        self.alpha = alpha
        self.beta = beta
        
        self.define_variables()
        self.define_constraints()
        self.define_objective()
        
        
    @abstractmethod
    def define_variables(self):
        pass
    
    @abstractmethod
    def define_constraints(self):
        pass
    
    @abstractmethod
    def define_objective(self):
        pass
    
    @abstractmethod
    def solve(self):
        pass
    
    
class RouteSolverCP(RouteSolver):
    def __init__(self, *args, **kwargs):
        self.model = cp_model.CpModel()
        super().__init__(*args, **kwargs)
        
        
    def define_variables(self):
        n = len(self.distance)
        self.x = {}
        for i in range(n):
            for j in range(n):
                self.x[i, j] = self.model.NewBoolVar(f"x_{i}_{j}")

        self.y = [self.model.NewBoolVar(f"y_{i}") for i in range(n)]

        # MTZ order variables
        self.u = [self.model.NewIntVar(0, n - 1, f"u_{i}") for i in range(n)]
        
    
    def define_constraints(self):
        n = len(self.distance)
        # No self loops
        for i in range(n):
            self.model.Add(self.x[i, i] == 0)

        # Start/end at base (node 0)
        self.model.Add(sum(self.x[0, j] for j in range(n)) == 1)
        self.model.Add(sum(self.x[i, 0] for i in range(n)) == 1)

        # Flow constraints
        for i in range(1, n):
            self.model.Add(sum(self.x[i, j] for j in range(n)) == self.y[i])
            self.model.Add(sum(self.x[j, i] for j in range(n)) == self.y[i])

        # Base is always visited
        self.model.Add(self.y[0] == 1)

        # MTZ subtour elimination
        for i in range(1, n):
            for j in range(1, n):
                if i != j:
                    self.model.Add(self.u[i] - self.u[j] + n * self.x[i, j] <= n - 1)
                    
        # -----------------------
        # Resource constraints
        # -----------------------

        total_distance = sum(int(self.distance[i][j]) * self.x[i, j]
                            for i in range(n) for j in range(n))

        total_elevation = sum(int(self.elevation[i][j]) * self.x[i, j]
                            for i in range(n) for j in range(n))

        self.model.Add(total_distance <= int(1e6))
        # self.model.Add(total_elevation <= int(self.max_elevation))
        
    def define_objective(self):
        # -----------------------
        # Objective
        # -----------------------

        n = len(self.distance)
        effort = sum((self.distance[i][j] + self.alpha * self.elevation[i][j]) * self.x[i, j]
                    for i in range(n) for j in range(n))

        reward = sum(self.scenic[i] * self.y[i] for i in range(n))

        self.model.Minimize(effort - self.beta * reward)
        
        
    def solve(self):
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 30

        status = solver.Solve(self.model)

        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            route = []
            current = 0
            visited = set([0])

            while True:
                for j in range(len(self.distance)):
                    if solver.Value(self.x[current, j]) == 1:
                        route.append((current, j))
                        current = j
                        if current == 0:
                            return route, solver.ObjectiveValue()
                        if current in visited:
                            return route, solver.ObjectiveValue()
                        visited.add(current)
                        break
        else:
            return None, None
        