import copy

class StateVariable:
    """
    Encapsulates a single state variable for the CSP,
    holding a name and a domain of possible values.
    """
    def __init__(self, name, domain):
        self.name = name
        self.domain = domain


class CSP:
    """
    A general CSP class containing:
      - A list of variables (StateVariable objects)
      - A dictionary of binary constraints:
         constraints[var_name] -> list of (neighbor_name, constraint_function)
    """
    def __init__(self, variables, constraints=None):
        """
        :param variables: List of StateVariable objects
        :param constraints: Dictionary of constraints where
                 key = variable name,
                 value = list of (other_variable_name, constraint_function)
        """
        self.variables = variables
        self.constraints = constraints if constraints else {}
        
        # Ensure every variable has an entry in constraints (even if empty)
        for var in self.variables:
            if var.name not in self.constraints:
                self.constraints[var.name] = []

    def is_complete(self, assignment):
        """
        Checks if every variable is assigned.
        :param assignment: dict var_name -> value
        :return: True if all variables have an assignment, False otherwise
        """
        for var in self.variables:
            if var.name not in assignment:
                return False
        return True

    def select_unassigned_variable(self, assignment):
        """
        Selects the first unassigned variable.
        """
        for var in self.variables:
            if var.name not in assignment:
                return var
        return None  

    def order_domain_values(self, var_name):
        """
        Return the domain of a given variable.
        """
        for var in self.variables:
            if var.name == var_name:
                return var.domain
        return []

    def is_consistent(self, var_name, value, assignment):
        """
        Check consistency of a potential (var_name, value) with the existing assignment.
        This checks the relevant constraints for var_name against already-assigned neighbors.
        """
        # Temporarily assign the value
        assignment[var_name] = value
        # print(f"Checking if assignment is consistent at depth {depth}: ", assignment_check)
        for state, val in assignment.items():
            if state in self.constraints:
                for neighbor, constraint_func in self.constraints[state]:
                    if neighbor in assignment:  # Check only if neighbor has been assigned
                        if not constraint_func(val, assignment[neighbor]):
                            del assignment[var_name]
                            return False  # Constraint violated
        del assignment[var_name]
        return True  # All constraints satisfied
    
class BacktrackingSolver:
    """
    A solver class for backtracking search on a CSP.
    """
    def __init__(self):
        self.depth = 0

    def naive_solve(self, csp):
        """
        solve the CSP using naive backtracking.
        """
        print("Beginning search")
        return self.naive_backtrack(csp, {})

    def naive_backtrack(self, csp, assignment):
        """
        The main recursive backtracking function.
        :param csp: The CSP instance
        :param assignment: Current partial assignment (dict: var_name -> value)
        :return: A complete assignment if found, or None if no solution is possible
        """
        if csp.is_complete(assignment):
            return assignment

        var = csp.select_unassigned_variable(assignment)
        if var is None:
            return None  # Should not happen if csp.is_complete is correct

        for value in csp.order_domain_values(var.name):
            if csp.is_consistent(var.name, value, assignment):
                # Try assigning this value
                assignment[var.name] = value

                result = self.naive_backtrack(csp, assignment)
                if result is not None:
                    return result

                # Backtrack (remove the assignment)
                del assignment[var.name]

        return None