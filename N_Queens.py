import copy



def build_constraints(csp, n):
    constraints = {}
    # instantiate the neighbor 1 lists
    for var1 in csp["State Variables"]:
        constraints[var1["state name"]] = []
        
    # enumerate all queen constraints
    for i in range(1, n+1):
        queen_a = f"Queen_{i}"
        for j in range(i+1, n+1):
            if not i == j:
                # comparing queen_a to queen_b
                queen_b = f"Queen_{j}"
                # same column constraints
                constraints[queen_a].append((queen_b, lambda a, b: a[0] != b[0]))
                # same row constraints
                constraints[queen_a].append((queen_b, lambda a, b: a[1] != b[1]))
                # diagnal constraints
                constraints[queen_a].append((queen_b, lambda a, b: abs(a[0] - b[0]) != abs(a[1] - b[1])))

    return constraints
        

def is_var_assigned(assignment, var_name):
    if var_name in assignment:
        return True
    return False
    
def is_complete(csp, assignment):
    for var in csp["State Variables"]: 
        if not is_var_assigned(assignment, var["state name"]):
            return False
    return True

def select_unassigned_var(csp, assignment):
    for var in csp["State Variables"]: 
            if not is_var_assigned(assignment, var["state name"]):
                return var
            
def order_domain_variables(csp, state_variable_name, assignment):
    for var in csp["State Variables"]: 
        if var['state name'] == state_variable_name:
            return var['domain']

# IMPORTANT: THIS IS WHERE CONSTRAINTS WOULD BE DEFINED EVAUATED
def consistent(state_assignment, assignment, constraints, depth):
    assignment_check = assignment
    assignment_check[state_assignment[0]] = state_assignment[1]
    # print(f"Checking if assignment is consistent at depth {depth}: ", assignment_check)
    for state, value in assignment_check.items():
        if state in constraints:
            for neighbor, constraint_func in constraints[state]:
                if neighbor in assignment_check:  # Check only if neighbor has been assigned
                    if not constraint_func(value, assignment_check[neighbor]):
                        # print(f"between {state} and {neighbor}, this delta was violated: ", inspect.getsource(constraint_func))
                        return False  # Constraint violated
    return True  # All constraints satisfied

def result_failure(result):
    return result is None
            
def backtrack(csp, assignment, depth):
    if is_complete(csp, assignment):
        return assignment
    var = select_unassigned_var(csp, assignment)
    state_variable_name = var["state name"]
    order_domain_variables = var["domain"]
    for value in order_domain_variables:
        state_assignment = (state_variable_name, value)
        if consistent(state_assignment, assignment, csp["Constraints"], depth):
            recursion_copy = copy.deepcopy(assignment)

            recursion_copy[state_variable_name] = value
            result = backtrack(csp, recursion_copy, depth + 1)
            if not result_failure(result):
                return result
            # inferences = inference(csp, var, assignment)
            # if not inference_failure(inferences):
            #     # csp.add(inferences)
            #     result = backtrack(csp, assignment)
            #     if not result_failure(result):
            #         return result
            #     # csp.remove(inferences)
            del recursion_copy[state_variable_name]
    return None
            
def backtracking_search(csp):
    depth = 0
    print("Beginning search")
    return backtrack(csp, {}, depth)


n = 10

n_queens_csp = {
    "State Variables":[]
    
}

for i in range(1, n+1):
    
    state_name = f"Queen_{i}"
    domain = [(x, y) for x in range(1, n+1) for y in range(1, n+1)]
    n_queens_csp["State Variables"].append({
        "state name": state_name,
        "domain": domain
    })
    
    
# for i in range(n):

constraints = build_constraints(n_queens_csp, n)
    
# n_queens_csp["Constraints" = ]


# print("CSP STRUCTURE\n")
# print("-"*64)
# print()
# print(n_queens_csp)

# print("CSP CONSTRAINTS\n")
# print("-"*64)
# print()
# print(constraints)
n_queens_csp["Constraints"] = constraints




print(backtracking_search(n_queens_csp))