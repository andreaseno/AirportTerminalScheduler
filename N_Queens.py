from csp import CSP, StateVariable, BacktrackingSolver

# build the n queens csp
def build_n_queens_csp(n):
    """
    Build an n-queens CSP.
    :param n: size of the board and number of queens
    :return: A CSP instance configured for n-queens
    """
    # 1) Create state variables for each queen: 'Queen_1', 'Queen_2', ...
    variables = []
    for i in range(1, n + 1):
        name = f"Queen_{i}"
        # Domain: all board positions (row, column) in [1..n]
        domain = [(row, col) for row in range(1, n + 1) for col in range(1, n + 1)]
        variables.append(StateVariable(name, domain))

    # 2) Build all constraints
    constraints = {}
    # Initialize each queen with an empty constraint list
    for var in variables:
        constraints[var.name] = []

    # For each pair of queens, add constraints:
    for i in range(1, n + 1):
        queen_a = f"Queen_{i}"
        for j in range(i + 1, n + 1):
            queen_b = f"Queen_{j}"
            # same column
            constraints[queen_a].append(
                (queen_b, lambda a, b: a[0] != b[0])
            )
            # same row
            constraints[queen_a].append(
                (queen_b, lambda a, b: a[1] != b[1])
            )
            # diagonal
            constraints[queen_a].append(
                (queen_b, lambda a, b: abs(a[0] - b[0]) != abs(a[1] - b[1]))
            )

    # Return a CSP instance
    return CSP(variables, constraints)


if __name__ == "__main__":
    n = 7
    csp_instance = build_n_queens_csp(n)

    solver = BacktrackingSolver()
    solution = solver.naive_solve(csp_instance)
    print("Solution:", solution)
    solution = solver.solve_with_forward_checking(csp_instance)
    print("Solution:", solution)
    # solution = solver.solve_with_ac3(csp_instance)
    # print("Solution:", solution)