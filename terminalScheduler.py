import json
import sys
from csp import CSP, StateVariable, BacktrackingSolver
from datetime import datetime, timedelta
from itertools import product

def datetime_to_military(dt):
    """Turn a datetime into an Integer based on the .json output specifications"""
    return int(dt.strftime("%H%M"))

def convert_datetimes(obj):
    """
    Recursively traverse obj (which can be a dict, list, or nested combinations).
    Whenever a datetime object is found, convert it with `datetime_to_military`.
    """
    if isinstance(obj, dict):
        # Recursively process each key-value pair
        return {k: convert_datetimes(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        # Recursively process each element of the list
        return [convert_datetimes(item) for item in obj]
    elif isinstance(obj, datetime):
        # Convert datetime objects to int
        return datetime_to_military(obj)
    else:
        # Leave all other types as is
        return obj


def find_forklift_jobs(solution, forklift_name):
    """
    Given a CSP solution, find and return any forklift jobs for forklift with name forklift_name.
    """
    forklift_jobs = []
    for job, details in solution.items():
        if job.startswith('forklift_') and details.get('forklift_name') == forklift_name:
            job_type = 'Load' if '_load_' in job else 'Unload'
            # associated_aircraft = find_associated_aircraft(solution, details.get('associated_aircraft_name'))
            forklift_jobs.append({
                'Hangar': details.get('hangar_assignment'),
                'Time': datetime_to_military(details.get('arrival_time')),
                'Job': job_type
            })
    
    return forklift_jobs

def find_associated_load_job(solution, truck_name):
    """
    Trucks are wrapped into Load jobs for simplicity, meaning a trucks arrival, departure, and hangar 
    are all the same as the load job. This is achieved by associating a truck with each load job through 
    the associated_truck_name variable and then placing constraints on that variable (ex: 2 trucks cannot
    be in the same hangar at the same time). This function finds the load job associated with a given truck
    and returns it.
    """
    for job, details in solution.items():
        if job.startswith("forklift_load_job") and details.get('associated_truck_name') == truck_name:
            return details
    
    return {}

def find_associated_unload_job(solution, airplane_name):
    """
    Airplanes are wrapped into unload jobs for simplicity, meaning a airplanes arrival, departure, and hangar 
    are all the same as the unload job. This is achieved by associating an airplane with each unload job through 
    the associated_airplane_name variable and then placing constraints on that variable (ex: 2 trucks cannot
    be in the same hangar at the same time). This function finds the load job associated with a given truck
    and returns it.
    """
    jobs = []
    # print("checking for airplane name ", airplane_name)
    for job, details in solution.items():
        # print("checking ", job)
        if job.startswith("forklift_unload_job") and details.get('associated_aircraft_name') == airplane_name:
            jobs.append(details)
    if len(jobs) > 0:
        return jobs
    else:
        return None

def find_associated_aircraft(solution, aircraft_name):
    """
    To simplify things further, we associate jobs with aircraft before solving the CSP, meaning that a 
    forklift job's hangar can be inferred by the hangar of the associated aircraft, and constraints can be
    placed on associated_aircraft_name instead of on load job hangars (ex: saying two load jobs cannot happen
    at the same time in a hangar is the same as saying two load jobs cannot happen at the same time if they 
    have the same associated aircrafts). This function finds the aircraft associated with a given aircraft
    name and returns it.
    """
    for var, details in solution.items():
        if var == aircraft_name:
            return details
    
    return {}

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
    while current_dt < end_dt:
        time_intervals.append(current_dt)
        print(current_dt)
        current_dt += timedelta(minutes=5)
    print(end_dt)

    return time_intervals

def generate_aircraft_domain(valid_times, hangars, aircraft_name, cargo_amount, terminal_arrival_time):
    """Generate the domain for given Aircraft state variable"""
    domain = []
    
    # Generate all possible state combinations
    for hangar, arrival_time in product(hangars, valid_times):
        # Ensure departure time is after arrival time
        for departure_time in valid_times:
            if departure_time > arrival_time and arrival_time >= terminal_arrival_time and (arrival_time-departure_time) % timedelta(minutes=20) == timedelta(0):
                domain.append({
                    'aircraft_name': aircraft_name,
                    'hangar_assignment': hangar,
                    'hangar_arrival_time': arrival_time,
                    'terminal_arrival_time': terminal_arrival_time,
                    'departure_time': departure_time,
                    'cargo_amount': cargo_amount
                })
    # print(domain)
    return domain

def generate_forklift_job_domain(jobtype, job_name, forklifts, hangars, valid_times, associated_job, associated_truck, associated_aircraft, associated_aircraft_data):
    """Generate the domain for given Forklift Job state variable"""
    domain = []
    if jobtype == "Load":
        # Generate all possible state combinations
        for hangar, arrival_time, forklift in product(hangars, valid_times, forklifts):
            # Ensure departure time is after arrival time
            # for departure_time in valid_times:
            if arrival_time >= associated_truck["terminal_arrival_time"]:
                domain.append({
                    'job_name': job_name, 
                    'forklift_name': forklift,
                    'arrival_time': arrival_time,
                    'associated_job': associated_job,
                    'associated_truck_name': associated_truck["name"],
                    'associated_aircraft_name': associated_aircraft,
                    'hangar_assignment': hangar,
                })
    elif jobtype == "Unload":
        # Generate all possible state combinations
        for hangar, arrival_time, forklift in product(hangars, valid_times, forklifts):
            if arrival_time >= datetime.strptime(f"{associated_aircraft_data['Time']:04d}", "%H%M"):
                domain.append({
                    'job_name': job_name, 
                    'forklift_name': forklift,
                    'arrival_time': arrival_time,
                    'associated_job': associated_job,
                    'associated_aircraft_name': associated_aircraft,
                    'hangar_assignment': hangar,
                    
                    # 'associated_aircraft_time': associated_aircraft_data["Time"]
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
    solvable = True
    
    # 1.1) Create state variables for each aircraft X_flight_n
    aircraft_variables = []
    
    # determine the earliest arircraft arrival. the start of valid times will be this time
    earliest_aircraft_arrival = meta["Stop Time"]
    for i, aircraft in enumerate(aircrafts):
            if aircrafts[aircraft]['Time'] < earliest_aircraft_arrival and aircrafts[aircraft]['Time'] >= meta["Start Time"]:
                earliest_aircraft_arrival = aircrafts[aircraft]['Time']
    if earliest_aircraft_arrival == meta["Stop Time"]:
        earliest_aircraft_arrival = meta["Start Time"]
    all_valid_times = generate_time_intervals(meta["Start Time"], meta["Stop Time"])
    
    all_hangars = meta["Hangars"]
    total_cargo_amount = 0
    aircraft_list = []
    
    for i, aircraft in enumerate(aircrafts):
        # aircraft_name = aircraft
        aircraft_cargo_amount = aircrafts[aircraft]["Cargo"]
        # terminal_arrival_time = datetime.strptime(f"{aircrafts[aircraft]['Time']:04d}", "%H%M")
        total_cargo_amount += aircraft_cargo_amount
        for _ in range(aircraft_cargo_amount):
            aircraft_list.append(aircraft)
        # Domain: all permutations of name, hangar, arrival time, departure time, and cargo amount where name and cargo amount are constants
        # domain = generate_aircraft_domain(all_valid_times, all_hangars, aircraft_name, aircraft_cargo_amount, terminal_arrival_time)

        # aircraft_variables.append(StateVariable(aircraft_name, domain))
    # variables = variables + aircraft_variables
    
    # 1.2) Create state variables for each Truck X_truck_n
    truck_info = []
    for i, truck in enumerate(trucks_data):
        # We only need one truck per cargo, so if the number of trucks are > total cargo, we don't need state variables for the extra trucks
        if (i >= total_cargo_amount):
            # TODO: NEED TO CHANGE schedule.json TRUCK LOGIC TO HANDLE CASE WHERE NOT ALL TRUCKS HAVE STATE VARS
            break
        truck_name = truck
        terminal_arrival_time = datetime.strptime(f"{trucks_data[truck]:04d}", "%H%M")
        truck_info.append({
            "name": truck_name,
            "terminal_arrival_time": terminal_arrival_time
        })    
        
    total_trucks = len(trucks_data)
    if (total_trucks < total_cargo_amount):
        print("CSP IS NOT SOLVABLE")
        return CSP(variables, {}, {}, False)

    
    # 1.3) Create state variables for each Forklift Load Job X_forklift_job_m
    load_job_variables = []
    all_forklifts = meta["Forklifts"]
    for job_num in range(total_cargo_amount):
        var_name = f"forklift_load_job_{job_num}"
        associated_unload = f"forklift_unload_job_{job_num}"
        associated_truck = truck_info[job_num]
        associated_aircraft = aircraft_list[job_num]
        domain = generate_forklift_job_domain("Load", var_name, all_forklifts, all_hangars, all_valid_times, associated_unload, associated_truck, associated_aircraft, aircrafts[aircraft])
        
        load_job_variables.append(StateVariable(var_name, domain))
    variables = variables + load_job_variables
        
    # 1.4) Create state variables for each Forklift Unload Job X_forklift_job_m
    # First, calulate total number of forklift jobs that will need to be created based on total cargo amount
    unload_job_variables = []
    all_forklifts = meta["Forklifts"]
    for job_num in range(total_cargo_amount):
        var_name = f"forklift_unload_job_{job_num}"
        associated_load = f"forklift_load_job_{job_num}"
        associated_aircraft = aircraft_list[job_num]
        domain = generate_forklift_job_domain("Unload", var_name, all_forklifts, all_hangars, all_valid_times, associated_load, None, associated_aircraft, aircrafts[aircraft])
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
        aircraft_a = aircraft_variables[i].name
        # Constraint: plane cannot go to the hangar before it arrives at the terminal
        unary_constraints[aircraft_a].append(
            (lambda a: a["terminal_arrival_time"] <= a["hangar_arrival_time"])
        )
        for j in range(i + 1, total_aircraft_vars):
            
            aircraft_b = aircraft_variables[j].name
            
            print(f"Pair: {aircraft_a} and {aircraft_b}")
            # Constraint: if aircraft A comes in before aircraft B, then aircraft A must leave before aircraft B arr time and the vice versa situation unless they are in different hangars
            # binary_constraints[aircraft_a].append(
            #     (aircraft_b, lambda a, b: 
            #         ((a["hangar_arrival_time"] < b["hangar_arrival_time"] and a["departure_time"] < b["hangar_arrival_time"]) or (not a["hangar_assignment"] == b["hangar_assignment"])) or
            #         ((a["hangar_arrival_time"] > b["hangar_arrival_time"] and b["departure_time"] < a["hangar_arrival_time"]) or (not a["hangar_assignment"] == b["hangar_assignment"]))
            #     )
            binary_constraints[aircraft_a].append(
                (aircraft_b, lambda a, b: 
                    # either they are not in the same hangar in which case we do not care about overlapping arrival times
                    (not a["hangar_assignment"] == b["hangar_assignment"]) or
                    # or they are in the same hangar in which case:
                    # a) if a arrives before b, then a must depart before b 
                    (((not a["hangar_arrival_time"] < b["hangar_arrival_time"]) or (a["departure_time"] < b["hangar_arrival_time"])) and
                    ((not a["hangar_arrival_time"] > b["hangar_arrival_time"]) or (b["departure_time"] < a["hangar_arrival_time"])) and
                    (not a["hangar_arrival_time"] == b["hangar_arrival_time"]))
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
            # Constraint: for unload job a and associated load job b, the load job must take place after the unload job finishes
            binary_constraints[unload_job_a].append(
                (load_job_b, lambda a, b: 
                    # 
                    ((not a["job_name"] == b["associated_job"]) or ((b["arrival_time"] > a["arrival_time"]+ timedelta(minutes=15)) and b['hangar_assignment'] == a['hangar_assignment']))
                )
            )
    
    # 2.3) build out all forklift load job specific constraints    
    for i in range(total_load_vars):
        load_job_a = load_job_variables[i].name

        for j in range(i + 1, total_load_vars):
            load_job_b = load_job_variables[j].name
            # Constraint: for a load job a and load job b, job b cannot have the same forklift performing an load within 5 minutes after job a
            #             or job a cannot have the same forklift performing an oad within 5 minutes after job b
            binary_constraints[load_job_a].append(
                (load_job_b, lambda a, b: 
                    # either the two forklifts must have diff names or job b cannot perform an unload within 20 minutes after job a
                    ((not a["forklift_name"] == b["forklift_name"]) or (b["arrival_time"] >= a["arrival_time"] + timedelta(minutes=5))) or
                    # either the two forklifts must have diff names or job a cannot perform an unload within 20 minutes after job b
                    ((not a["forklift_name"] == b["forklift_name"]) or (a["arrival_time"] >= b["arrival_time"] + timedelta(minutes=5)))
                )
            )
            # Constraint: for a load job a and load job b, jobs a and b cannot occur at the same time if they are in the same hangar
            binary_constraints[load_job_a].append(
                (load_job_b, lambda a, b: 
                    # either the two forklifts must have diff hangars or job a and b cannot happen at the same time
                    (not a["hangar_assignment"] == b["hangar_assignment"]) or (not b["arrival_time"] == a["arrival_time"])
                )
            )
    
    # 2.4) Build out all aircraft to job constraints
    for i in range(total_aircraft_vars):
        aircraft_a = aircraft_variables[i].name
        # For (aircraft, unload) pairs
        for j in range(0, total_unload_vars):
            unload_job_b = unload_job_variables[j].name
            # Constraint 1: if an associated aircraft unload  job pair, the unload job must start after the aircraft lands
            # binary_constraints[aircraft_a].append(
            #     (unload_job_b, lambda a, b: 
            #         ((not a["aircraft_name"] == b["associated_aircraft_name"]) or ((a["hangar_arrival_time"] <= b["arrival_time"]) and (a["departure_time"] >= b["arrival_time"]+timedelta(minutes=20))))
            #     )
            # )
            
            # ABOVE COMMENTED OUT CONSTRAINT IS COVERED BY REDUCING DOMAIN S.T. TIMES ARE ONLY ADDED TO DOMAIN IF THEY ARE AFTER AIRCRAFT["TIME"]
            
            
        # For (aircraft, load) pairs
        for k in range(total_load_vars):
            load_job_b = load_job_variables[k].name
            # Constraint 1: if an associated aircraft load job pair, the load job must start after the aircraft lands
            # binary_constraints[aircraft_a].append(
            #     (load_job_b, lambda a, b: 
            #         # either the aircraft and load job are not associated, or the load job must happen after the plane arrives at the hangar
            #         ((not a["aircraft_name"] == b["associated_aircraft_name"]) or ((a["hangar_arrival_time"] <= b["arrival_time"])))
            #     )
            # )
            
            # ABOVE COMMENTED OUT CONSTRAINT IS COVERED BY Unload -> Load constraint that associated loads have to happen after their associated unload finishes
            
            
            # Constraint 2: if an associated aircraft load job pair, the load job must happen at the same hangar as the aircraft 
            # binary_constraints[aircraft_a].append(
            #     (load_job_b, lambda a, b: 
            #         ((not a["aircraft_name"] == b["associated_aircraft_name"]) or (a["hangar_assignment"] == b["hangar_assignment"]))
            #     )
            # )
            
            # ABOVE COMMENTED OUT CONSTRAINT IS COVERED BY Unload -> Load constraint that associated loads have to happen at the same hangar as their associated load
            
            
            
    return CSP(variables, binary_constraints, unary_constraints, solvable)


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
    # solution = solver.naive_solve(csp, 0)
    # print("Solution:", solution)
    solution = solver.solve_with_forward_checking(csp, 0)
    # print("Solution:", solution)
    
    with open("solution.json", 'w') as file:
        json.dump(convert_datetimes(solution), file, indent=4)
    
    # insert code to create schedule here
    schedule = {"aircraft": {}, "trucks": {}, "forklifts": {}}
    
    for aircraft in aircraft_data:
        # if aircraft in solution:
        #     schedule["aircraft"][aircraft] = {
        #         "Hangar": solution[aircraft]["hangar_assignment"],
        #         "Arrival": datetime_to_military(solution[aircraft]["hangar_arrival_time"]),
        #         "Departure": datetime_to_military(solution[aircraft]["departure_time"])
                
        #     }
        # else: 
        #     schedule["aircraft"] = None
        associated_unloads = find_associated_unload_job(solution, aircraft)
        if associated_unloads and len(associated_unloads) > 0:
            earliest_job = associated_unloads[0]['arrival_time']
            latest_job = associated_unloads[0]['arrival_time']
            hangar_check = associated_unloads[0]['hangar_assignment']
            for job in associated_unloads:
                if job['arrival_time'] < earliest_job:
                    earliest_job = job['arrival_time']
                if job['arrival_time'] > latest_job:
                    latest_job = job['arrival_time']
                if not hangar_check == job['hangar_assignment']:
                    print(f"ERROR: NOT ALL ASSOCIATED UNLOADS FOR AIRCRAFT {aircraft} HAVE THE SAME HANGAR ASSIGNMENT")

            print(associated_unloads)
            
            schedule["aircraft"][aircraft] = {
                "Hangar": hangar_check,
                "Arrival": datetime_to_military(earliest_job),
                "Departure": datetime_to_military(latest_job + timedelta(minutes=20))
            }
        else:
            schedule["aircraft"] = None
        
        
    for truck in trucks_data:
        # assign a load job to each truck. That load job's arrival will be the same as this trucks arrival and departure will be 5 mins after
        associated_load = find_associated_load_job(solution, truck)
        print(f"truck: {truck}")
        if associated_load:  
            # associated_aircraft = find_associated_aircraft(solution, associated_load['associated_aircraft_name'])
            schedule["trucks"][truck] = {
                "Hangar": associated_load['hangar_assignment'],
                "Arrival": datetime_to_military(associated_load['arrival_time']),
                "Departure": datetime_to_military(associated_load['arrival_time']+timedelta(minutes=5))
            }
        else:
            schedule["trucks"] = None
            print("could not find load")
        print()
        
    no_forklifts_scheduled = True
    for forklift in meta_data["Forklifts"]:
        associated_jobs = find_forklift_jobs(solution, forklift)
        if associated_jobs:
            schedule["forklifts"][forklift] = associated_jobs
            no_forklifts_scheduled = False
    if no_forklifts_scheduled:
        schedule["forklifts"] = None
            
    with open(schedule_path, 'w') as file:
        json.dump(schedule, file, indent=4)
        
    print(f"Schedule written to {schedule_path}")
    