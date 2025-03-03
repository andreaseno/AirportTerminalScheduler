import json
import sys
from csp import CSP, StateVariable, BacktrackingSolver
from datetime import datetime, timedelta
from itertools import product

def datetime_to_military(dt):
    """Turn a datetime into an Integer based on the .json output specifications"""
    return int(dt.strftime("%H%M"))

def find_forklift_jobs(solution, forklift_name):
    forklift_jobs = []
    for job, details in solution.items():
        if job.startswith('forklift_') and details.get('forklift_name') == forklift_name:
            job_type = 'Load' if '_load_' in job else 'Unload'
            forklift_jobs.append({
                'Hangar': details.get('hangar_assignment'),
                'Time': datetime_to_military(details.get('arrival_time')),
                'Job': job_type
            })
    
    return forklift_jobs

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
       
def generate_time_intervals(start_time: int, end_time: int):
    """Generate all datetimes between input start and start time in 5 minute intervals"""
    # Convert integers to datetime objects
    start_dt = datetime.strptime(f"{start_time:04d}", "%H%M")
    end_dt = datetime.strptime(f"{end_time:04d}", "%H%M")
    
    # Generate all 5-minute intervals
    time_intervals = []
    current_dt = start_dt
    while current_dt <= end_dt:
        time_intervals.append(current_dt)
        current_dt += timedelta(minutes=5)

    return time_intervals

def generate_aircraft_domain(valid_times, hangars, aircraft_name, cargo_amount, terminal_arrival_time):
    """Generate the domain for given Aircraft state variable"""
    domain = []
    
    # Generate all possible state combinations
    for hangar, arrival_time in product(hangars, valid_times):
        # Ensure departure time is after arrival time
        for departure_time in valid_times:
            if departure_time > arrival_time:
                domain.append({
                    'aircraft_name': aircraft_name,
                    'hangar_assignment': hangar,
                    'hangar_arrival_time': arrival_time,
                    'terminal_arrival_time': terminal_arrival_time,
                    'departure_time': departure_time,
                    'cargo_amount': cargo_amount
                })
    
    return domain

def generate_truck_domain(valid_times, hangars, truck_name, terminal_arrival_time):
    """Generate the domain for given Truck state variable"""
    domain = []
    
    # Generate all possible state combinations
    for hangar, arrival_time in product(hangars, valid_times):
        # Ensure departure time is after arrival time
        for departure_time in valid_times:
            if departure_time > arrival_time:
                domain.append({
                    'truck_name': truck_name,
                    'hangar_assignment': hangar,
                    'hangar_arrival_time': arrival_time,
                    'terminal_arrival_time': terminal_arrival_time,
                    'departure_time': departure_time
                })
    
    return domain

def generate_forklift_job_domain(forklifts, hangars, valid_times):
    """Generate the domain for given Forklift Job state variable"""
    domain = []
    
    # Generate all possible state combinations
    for hangar, arrival_time, forklift in product(hangars, valid_times, forklifts):
        # Ensure departure time is after arrival time
        # for departure_time in valid_times:
        #     if departure_time > arrival_time:
        domain.append({
            'forklift_name': forklift,
            'hangar_assignment': hangar,
            'arrival_time': arrival_time
        })
    
    return domain

def build_problem_csp(meta, aircrafts, trucks):
    """
    Build an CSP for the current scheduling probblem.
    :param meta: dict data from the read in meta.json file
    :param aircrafts: dict data from the read in aircraft.json file
    :param trucks: dict data from the read in trucks.json file
    :return: A CSP instance configured for scheduling this specific data
    """
    
    # 1) Create all state variables and domains
    
    variables = []
    
    # 1.1) Create state variables for each aircraft X_flight_n
    aircraft_variables = []
    all_valid_times = generate_time_intervals(meta["Start Time"], meta["Stop Time"])
    all_hangars = meta["Hangars"]
    total_cargo_amount = 0
    for i, aircraft in enumerate(aircraft_data):
        # var_name = f"aircraft_{i}"
        aircraft_name = aircraft
        aircraft_cargo_amount = aircraft_data[aircraft]["Cargo"]
        terminal_arrival_time = datetime.strptime(f"{aircraft_data[aircraft]['Time']:04d}", "%H%M")
        total_cargo_amount += aircraft_cargo_amount
        # Domain: all permutations of name, hangar, arrival time, departure time, and cargo amount where name and cargo amount are constants
        domain = generate_aircraft_domain(all_valid_times, all_hangars, aircraft_name, aircraft_cargo_amount, terminal_arrival_time)

        aircraft_variables.append(StateVariable(aircraft_name, domain))
    variables = variables + aircraft_variables
    
    # 1.2) Create state variables for each Truck X_truck_n
    truck_variables = []
    for i, truck in enumerate(trucks_data):
        # var_name = f"truck_{i}"
        truck_name = truck
        terminal_arrival_time = datetime.strptime(f"{trucks_data[truck]:04d}", "%H%M")
        # Domain: all permutations of name, hangar, arrival time, departure time where name is a constant
        domain = generate_truck_domain(all_valid_times, all_hangars, truck_name, terminal_arrival_time)

        truck_variables.append(StateVariable(truck_name, domain))
    variables = variables + truck_variables
        
    # 1.3) Create state variables for each Forklift Load Job X_forklift_job_m
    load_job_variables = []
    all_forklifts = meta["Forklifts"]
    for job_num in range(total_cargo_amount):
        var_name = f"forklift_load_job_{job_num}"
        domain = generate_forklift_job_domain(all_forklifts, all_hangars, all_valid_times)
        
        load_job_variables.append(StateVariable(var_name, domain))
    variables = variables + load_job_variables
        
    # 1.4) Create state variables for each Forklift Unload Job X_forklift_job_m
    # First, calulate total number of forklift jobs that will need to be created based on total cargo amount
    unload_job_variables = []
    all_forklifts = meta["Forklifts"]
    for job_num in range(total_cargo_amount):
        var_name = f"forklift_unload_job_{job_num}"
        domain = generate_forklift_job_domain(all_forklifts, all_hangars, all_valid_times)
        # print(len(domain))
        unload_job_variables.append(StateVariable(var_name, domain))
    variables = variables + unload_job_variables
    
    
    # 2) Build all constraints
    
    # Inititalize where to store all unary and binary constraints
    binary_constraints = {}
    unary_constraints = {}
    for var in variables:
        binary_constraints[var.name] = []
        unary_constraints[var.name] = []
        
    # 2.1) build out all aircraft specific constraints
    total_aircraft_vars = len(aircraft_variables)
    # Build out all aircraft state variable pair constraints
    for i in range(total_aircraft_vars):
        # aircraft_a = f"aircraft_{i}"
        aircraft_a = aircraft_variables[i].name
        # Constraint: plane cannot go to the hangar before it arrives at the terminal
        unary_constraints[aircraft_a].append(
            (lambda a: a["terminal_arrival_time"] <= a["hangar_arrival_time"])
        )
        for j in range(i + 1, total_aircraft_vars):
            
            aircraft_b = aircraft_variables[j].name
            
            print(f"Pair: {aircraft_a} and {aircraft_b}")
            # Constraint: if aircraft A comes in before aircraft B, then aircraft A must leave before aircraft B arr time and the vice versa situation unless they are in different hangars
            binary_constraints[aircraft_a].append(
                (aircraft_b, lambda a, b: 
                    ((a["hangar_arrival_time"] < b["hangar_arrival_time"] and a["departure_time"] < b["hangar_arrival_time"]) or not a["hangar_assignment"] == b["hangar_assignment"]) or
                    ((a["hangar_arrival_time"] > b["hangar_arrival_time"] and b["departure_time"] < a["hangar_arrival_time"]) or not a["hangar_assignment"] == b["hangar_assignment"])
                )
            )
    
    # 2.2) build out all truck specific constraints
    total_trucks_vars = len(truck_variables)
    # Build out all truck-specific state variable pair constraints
    for i in range(total_trucks_vars):
        truck_a = truck_variables[i].name
        # Constraint: truck cannot go to the hangar before it arrives at the terminal
        unary_constraints[truck_a].append(
            (lambda a: a["terminal_arrival_time"] <= a["hangar_arrival_time"])
        )
        for j in range(i + 1, total_trucks_vars):
            
            truck_b = truck_variables[j].name
            
            print(f"Pair: {truck_a} and {truck_b}")
            # Constraint: if truck A comes into the hangar before truck B, then truck A must leave before truck B arr time and the vice versa situation unless they are in different hangars
            binary_constraints[truck_a].append(
                (truck_b, lambda a, b: 
                    ((a["hangar_arrival_time"] < b["hangar_arrival_time"] and a["departure_time"] < b["hangar_arrival_time"]) or not a["hangar_assignment"] == b["hangar_assignment"]) or
                    ((a["hangar_arrival_time"] > b["hangar_arrival_time"] and b["departure_time"] < a["hangar_arrival_time"]) or not a["hangar_assignment"] == b["hangar_assignment"])
                )
            )
            
    # 2.3) build out all forklift unload job specific constraints
    total_unload_vars = len(unload_job_variables)
    total_load_vars = len(load_job_variables)
    # This loop should cover all (unload, unload) pairs and (unload, load) pairs. Will need another double for loop for all (load, load) pairs
    for i in range(total_unload_vars):
        unload_job_a = unload_job_variables[i].name
        # For (unload, unload) pairs
        for j in range(i + 1, total_unload_vars):
            unload_job_b = unload_job_variables[j].name
            # Constraint: for 2 unload job, job b cannot have the same forklift performing an unload within 20 minutes after job a
            binary_constraints[unload_job_a].append(
                (unload_job_b, lambda a, b: 
                    # either the two forklifts must have diff names or job b cannot perform an unload within 20 minutes after job a
                    ((not a["forklift_name"] == b["forklift_name"]) or (b["arrival_time"] >= a["arrival_time"] + timedelta(minutes=20))) or
                    # either the two forklifts must have diff names or job a cannot perform an unload within 20 minutes after job b
                    ((not a["forklift_name"] == b["forklift_name"]) or (a["arrival_time"] >= b["arrival_time"] + timedelta(minutes=20)))
                )
            )
        # For (unload, load) pairs
        for k in range(total_load_vars):
            load_job_b = load_job_variables[k].name
            # Constraint: for an unload job a and load job b, job b cannot have the same forklift performing an load within 20 minutes after job a
            #             or job a cannot have the same forklift performing an unload within 5 minutes after job b
            binary_constraints[unload_job_a].append(
                (load_job_b, lambda a, b: 
                    # either the two forklifts must have diff names or job b cannot perform an load within 20 minutes after job a starts unloading
                    ((not a["forklift_name"] == b["forklift_name"]) or (b["arrival_time"] >= a["arrival_time"] + timedelta(minutes=20))) or
                    # either the two forklifts must have diff names or job a cannot perform an unload within 5 minutes after job b unloads
                    ((not a["forklift_name"] == b["forklift_name"]) or (a["arrival_time"] >= b["arrival_time"] + timedelta(minutes=5)))
                )
            )
    
    # 2.3) build out all forklift load job specific constraints    
    for i in range(total_load_vars):
        load_job_a = load_job_variables[i].name

        for j in range(i + 1, total_load_vars):
            load_job_b = load_job_variables[j].name
            # Constraint: for an unload job a and load job b, job b cannot have the same forklift performing an load within 20 minutes after job a
            #             or job a cannot have the same forklift performing an unload within 5 minutes after job b
            binary_constraints[load_job_a].append(
                (load_job_b, lambda a, b: 
                    # either the two forklifts must have diff names or job b cannot perform an unload within 20 minutes after job a
                    ((not a["forklift_name"] == b["forklift_name"]) or (b["arrival_time"] >= a["arrival_time"] + timedelta(minutes=5))) or
                    # either the two forklifts must have diff names or job a cannot perform an unload within 20 minutes after job b
                    ((not a["forklift_name"] == b["forklift_name"]) or (a["arrival_time"] >= b["arrival_time"] + timedelta(minutes=5)))
                )
            )
            
        
            
    return CSP(variables, binary_constraints, unary_constraints)


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Please use this script as such: terminalScheduler.py META_PATH AIRCRAFT_PATH TRUCKS_PATH SCHEDULE_PATH")
        sys.exit(1)
    meta_path, aircraft_path, trucks_path, schedule_path = sys.argv[1:]
    meta_data = load_json(meta_path)
    aircraft_data = load_json(aircraft_path)
    trucks_data = load_json(trucks_path)
    
    csp = build_problem_csp(meta_data, aircraft_data, trucks_data)
    
    solver = BacktrackingSolver()
    solution = solver.naive_solve(csp)
    print("Solution:", solution)
    
    # insert code to create schedule here
    schedule = {"aircraft": {}, "trucks": {}, "forklifts": {}}
    
    for aircraft in aircraft_data:
        schedule["aircraft"][aircraft] = {
            # TODO make these not be default values
            "Hangar": solution[aircraft]["hangar_assignment"],
            "Arrival": datetime_to_military(solution[aircraft]["hangar_arrival_time"]),
            "Departure": datetime_to_military(solution[aircraft]["departure_time"])
            
        }
        
    for truck in trucks_data:
        schedule["trucks"][truck] = {
            # TODO make these not be default values
            "Hangar": solution[truck]["hangar_assignment"],
            "Arrival": datetime_to_military(solution[truck]["hangar_arrival_time"]),
            "Departure": datetime_to_military(solution[truck]["departure_time"])
        }
        
    for forklift in meta_data["Forklifts"]:
        schedule["forklifts"][forklift] = find_forklift_jobs(solution, forklift)
            
    with open(schedule_path, 'w') as file:
        json.dump(schedule, file, indent=4)
        
    print(f"Schedule written to {schedule_path}")
    