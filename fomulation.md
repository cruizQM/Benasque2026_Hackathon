# Cost Function Formulation

## Problem Description

Given a directed, non-complete graph where:

- Each node represents a point of interest
- Each edge has an associated cost (combining elevation difference and travel time)

The goal is to find a route that:

- Minimizes the total cost of the selected edges
- Maximizes the number of visited nodes
- Satisfies path consistency constraints

---

## Decision Variables

We define the following binary variables:

- $x_{ij} \in \{0,1\}$: equals 1 if the edge from node \(i\) to node \(j\) is selected
- \( y_j \in \{0,1\} \): equals 1 if node \(j\) is visited

---

## Relaxed Variable Representation

Within the Pauli Correlation Encoding framework, variables are represented in the range:

\[
z \in [-1,1]
\]

and mapped to relaxed binary variables in \([0,1]\) as:

\[
x_{ij} = \frac{z_{ij} + 1}{2}, \quad y_j = \frac{z_j + 1}{2}
\]

---

## Objective Function

The base cost function is defined as:

\[
H = \sum_{i,j} w_{ij} x_{ij} \;-\; \mu \sum_j y_j
\]

where:

- \( w_{ij} \): cost associated with edge \((i,j)\)
- \( \mu \): parameter controlling the reward for visiting nodes

This term aims to:

- Minimize the total traversal cost
- Maximize the number of visited nodes

---

## Constraints as Penalty Terms

Since the formulation is expressed as a QUBO problem, all constraints are incorporated as quadratic penalty terms.

---

### 1. Node–Incoming Edge Consistency

If a node is visited, exactly one incoming edge must be selected:

\[
\sum_i x_{ij} = y_j
\]

Penalty term:

\[
\lambda_1 \sum_j \left( \sum_i x_{ij} - y_j \right)^2
\]

---

### 2. Node–Outgoing Edge Consistency

If a node is visited, exactly one outgoing edge must be selected:

\[
\sum_k x_{jk} = y_j
\]

Penalty term:

\[
\lambda_2 \sum_j \left( \sum_k x_{jk} - y_j \right)^2
\]

---

### 3. Start/End Node Constraint (Optional)

To enforce a closed route starting and ending at a specific node (e.g., node 0):

\[
\sum_j x_{0j} = 1, \quad \sum_i x_{i0} = 1
\]

Penalty term:

\[
\lambda_3 \left( \sum_j x_{0j} - 1 \right)^2
+
\lambda_4 \left( \sum_i x_{i0} - 1 \right)^2
\]

---

## Final Cost Function

The complete Hamiltonian is given by:

\[
H =
\underbrace{\sum_{i,j} w_{ij} x_{ij}}_{\text{edge cost}}
-
\underbrace{\mu \sum_j y_j}_{\text{node reward}}
+
\underbrace{\lambda_1 \sum_j (\sum_i x_{ij} - y_j)^2}_{\text{incoming constraint}}
+
\underbrace{\lambda_2 \sum_j (\sum_k x_{jk} - y_j)^2}_{\text{outgoing constraint}}
+
\underbrace{\lambda_3 (\sum_j x_{0j} - 1)^2}_{\text{start constraint}}
+
\underbrace{\lambda_4 (\sum_i x_{i0} - 1)^2}_{\text{end constraint}}
\]

---

## Important Considerations

- Penalty coefficients must satisfy:

\[
\lambda \gg w_{ij}
\]

to ensure constraint satisfaction.

- The parameter \( \mu \) controls the trade-off between:
  - visiting more nodes
  - minimizing traversal cost

- The formulation is compatible with:
  - QUBO models
  - Ising formulations
  - Pauli Correlation Encoding

---

## Remarks

- Additional terms such as \( x_{ij}(1 - y_j) \) are unnecessary, as consistency is already enforced through quadratic penalties.
- Subtour elimination is not explicitly enforced and may require additional constraints depending on the application.