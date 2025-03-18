import time
from collections import deque, defaultdict


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
    def __init__(self, variables, binary_constraints=None, unary_constraints=None, solvable=True):
        """
        :param variables: List of StateVariable objects
        :param constraints: Dictionary of constraints where
                 key = variable name,
                 value = list of (other_variable_name, constraint_function)
        """
        self.variables = variables
        self.solvable = solvable 
        self.verbose = 0
        self.binary_constraints = binary_constraints if binary_constraints else {}
        self.unary_constraints = unary_constraints if unary_constraints else {}
        
        # Ensure every variable has an entry in constraints (even if empty)
        for var in self.variables:
            if var.name not in self.binary_constraints:
                self.binary_constraints[var.name] = []
            if var.name not in self.unary_constraints:
                self.unary_constraints[var.name] = []

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
            if state in self.binary_constraints:
                for neighbor, constraint_func in self.binary_constraints[state]:
                    if neighbor in assignment:  # Check only if neighbor has been assigned
                        if not constraint_func(val, assignment[neighbor]):
                            del assignment[var_name]
                            return False  # Constraint violated
            if state in self.unary_constraints:
                for constraint_func in self.unary_constraints[state]:
                    if not constraint_func(val):
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

    def naive_solve(self, csp, verbose = 0):
        """
        solve the CSP using naive backtracking.
        """
        start_time = time.time()

        if verbose >= 1:
            print("Beginning search")
        self.verbose = verbose
        ret = self.naive_backtrack(csp, {})
        end_time = time.time()
        # Calculate and print execution time
        execution_time = end_time - start_time
        print(f"Execution time for naive backtracking alg: {execution_time:.2f} seconds")
        return ret
    
    def naive_backtrack(self, csp, assignment):
        """
        The main recursive backtracking function.
        :param csp: The CSP instance
        :param assignment: Current partial assignment (dict: var_name -> value)
        :param verbose: 0 = no terminal output, 1 = minimal terminal output, 2 = maximum terminal output
        
        :return: A complete assignment if found, or None if no solution is possible
        """
        if self.verbose >= 1: 
            print("checking for completeness")
        if csp.is_complete(assignment):
            return assignment

        var = csp.select_unassigned_variable(assignment)
        if var is None:
            return None  # Should not happen if csp.is_complete is correct

        for value in csp.order_domain_values(var.name):
            # if self.verbose == 2:
            #     print(f"trying to assign variable: {var.name} value: {value}")
            if csp.is_consistent(var.name, value, assignment):
                # Try assigning this value
                assignment[var.name] = value
                
                if self.verbose == 2:
                    print(f"current state assignment {assignment} is consistent.")
                if self.verbose >= 1: 
                    print("Recursing further")

                result = self.naive_backtrack(csp, assignment)
                if result is not None:
                    return result
                
                if self.verbose == 2:
                    print(f"current state assignment {assignment} had no further valid solutions, so {var.name}'s assignment of {value} is being removed.")
                if self.verbose >= 1: 
                    print("Backtracking")
                
                # Backtrack (remove the assignment)
                del assignment[var.name]

        return None

    def solve_with_forward_checking(self, csp, verbose=0):
        """
        Solve the CSP using backtracking + forward checking.
        """
        start_time = time.time()
        print(f"Starting at {time.ctime(start_time)  }")
        self.verbose = verbose
        # We assume the domains in csp.variables are the live, modifiable domains.
        ret  = self.backtrack_with_forward_check(csp, assignment={})
        end_time = time.time()
        # Calculate and print execution time
        execution_time = end_time - start_time
        print(f"Execution time for forward checking backtracking alg: {execution_time:.2f} seconds")
        if ret is None:
            return {
                "aircraft": None,
                "trucks": None,
                "forklifts": None
            }
        else:    
            return ret
    
    def backtrack_with_forward_check(self, csp, assignment):
        """
        The main recursive backtracking function that includes forward checking.
        """
        if not csp.solvable: 
            return {
                "aircraft": None,
                "trucks": None,
                "forklifts": None
            }
        
        if csp.is_complete(assignment):
            # Found a solution
            return assignment

        # Pick an unassigned variable
        var = csp.select_unassigned_variable(assignment)
        if var is None:
            return None  # No unassigned variable found -> no solution or unexpected

        var_name = var.name
        # For each value in var's domain
        for value in csp.order_domain_values(var_name):
            if csp.is_consistent(var_name, value, assignment):
                # Tentatively assign var = value
                assignment[var_name] = value

                # RECORD of pruned values: pruned[var_name] = list of domain values removed
                pruned = defaultdict(list)

                # 1) Forward Check: prune neighbors' domains 
                if self.forward_check(csp, assignment, var_name, value, pruned):
                    # 2) If forward check didn't fail, recurse
                    result = self.backtrack_with_forward_check(csp, assignment)
                    if result is not None:
                        return result

                # 3) If we’re here, either forward check failed or recursion failed,
                #    so we must UNDO the prunes and the assignment
                self.restore_pruned_values(csp, pruned)
                del assignment[var_name]

        return None  # No valid value found for this variable => backtrack

    def forward_check(self, csp, assignment, var_name, value, pruned):
        """
        For each unassigned neighbor of var_name, remove any domain values 
        that are inconsistent with var_name = value. 
        If any domain is wiped out, return False immediately.
        
        :param csp: The CSP instance
        :param assignment: Current partial assignment
        :param var_name: Name of the variable just assigned
        :param value: Value assigned to var_name
        :param pruned: A dictionary to keep track of pruned values so we can restore them
        :return: True if forward checking succeeded, False if it found an empty domain
        """
        # For every neighbor that has constraints with var_name
        for (neighbor, constraint_func) in csp.binary_constraints[var_name]:
            # Only prune if neighbor is not yet assigned
            if neighbor not in assignment:
                # Find the neighbor's StateVariable object
                neighbor_var = next((v for v in csp.variables if v.name == neighbor), None)
                if not neighbor_var:
                    continue  # Safety check

                # We’ll build a list of domain values to remove
                to_remove = []

                # For each candidate in the neighbor's domain:
                for neighbor_val in neighbor_var.domain:
                    # Check constraint between the newly assigned (var_name=value) 
                    # and neighbor=(neighbor_val)
                    # If it violates the constraint, we remove neighbor_val
                    if not constraint_func(value, neighbor_val):
                        to_remove.append(neighbor_val)

                # Now apply the pruning
                for val in to_remove:
                    neighbor_var.domain.remove(val)
                    pruned[neighbor].append(val)

                # If domain becomes empty => fail forward check
                if len(neighbor_var.domain) == 0:
                    return False
                
        return True

    def restore_pruned_values(self, csp, pruned):
        """
        Undo the domain pruning recorded in 'pruned'.
        :param csp: The CSP instance
        :param pruned: dict => var_name -> list of domain values removed
        """
        for var_name, vals in pruned.items():
            neighbor_var = next((v for v in csp.variables if v.name == var_name), None)
            if neighbor_var:
                neighbor_var.domain.extend(vals)