import json
import sys
from itertools import cycle

def load_json(file_path):
    """Load JSON data from a file."""
    try:
        with open(file_path, 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: File {file_path} is not a valid JSON file.")
        sys.exit(1)
        
def is_complete(assignment):
    
    return None

def backtrack(csp, assignment):
    if is_complete(assignment):
        return assignment
    var = select_unassigned_var(csp, assignment)
    for value in order_domain_variables(csp, var, assignment):
        if consistent(value, assignment):
            # assignment.add(var = value)
            inferences = inference(csp, var, assignment)
            if not inference_failure(inferences):
                # csp.add(inferences)
                result = backtrack(csp, assignment)
                if not result_failure(result):
                    return result
                # csp.remove(inferences)
            # assignment.remove(var = value)
            
def backtracking_search(csp):
    backtrack(csp, {})
    

    
if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Please use this script as such: terminalScheduler.py META_PATH AIRCRAFT_PATH TRUCKS_PATH SCHEDULE_PATH")
        sys.exit(1)
    meta_path, aircraft_path, trucks_path, schedule_path = sys.argv[1:]
    meta_data = load_json(meta_path)
    aircraft_data = load_json(aircraft_path)
    trucks_data = load_json(trucks_path)
    
    # insert code to create schedule here
    schedule = {"aircraft": {}, "trucks": {}, "forklifts": {}}
    
    for aircraft in aircraft_data:
        schedule["aircraft"][aircraft] = {
            # TODO make these not be default values
            "Hangar": None,
            "Arrival": None,
            "Departure": None
            
        }
        
    for truck in trucks_data:
        schedule["trucks"][truck] = {
            # TODO make these not be default values
            "Hangar": None,
            "Arrival": None,
            "Departure": None
        }
        
    for forklift in meta_data["Forklifts"]:
        schedule["forklifts"][forklift] = []
    
    with open(schedule_path, 'w') as file:
        json.dump(schedule, file, indent=4)
        
    print(f"Schedule written to {schedule_path}")
    