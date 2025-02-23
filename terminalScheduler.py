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

# def schedule_operations(meta, aircraft, trucks):
#     """Schedule aircraft and trucks within the given constraints."""
#     start_time = meta["Start Time"]
#     stop_time = meta["Stop Time"]
#     hangars = cycle(meta["Hangars"])  # Rotate through hangars
#     forklifts = cycle(meta["Forklifts"])  # Rotate through forklifts
    
#     schedule = {"aircraft": {}, "trucks": {}, "forklifts": {f: [] for f in meta["Forklifts"]}}
    
#     current_time = start_time
    
#     # Schedule aircraft
#     for ac_id, details in sorted(aircraft.items(), key=lambda x: x[1]["Time"]):
#         if current_time + 20 > stop_time:
#             return {"aircraft": None, "trucks": None, "forklifts": None}  # Cannot fit all schedules
#         hangar = next(hangars)
#         schedule["aircraft"][ac_id] = {"Hangar": hangar, "Arrival": current_time, "Departure": current_time + 20}
        
#         forklift = next(forklifts)
#         schedule["forklifts"][forklift].append({"Hangar": hangar, "Time": current_time, "Job": "Unload"})
#         schedule["forklifts"][forklift].append({"Hangar": hangar, "Time": current_time + 20, "Job": "Load"})
        
#         current_time += 20
    
#     # Schedule trucks
#     for truck_id, arrival_time in sorted(trucks.items(), key=lambda x: x[1]):
#         if current_time + 5 > stop_time:
#             return {"aircraft": None, "trucks": None, "forklifts": None}
#         hangar = next(hangars)
#         schedule["trucks"][truck_id] = {"Hangar": hangar, "Arrival": current_time, "Departure": current_time + 5}
        
#         forklift = next(forklifts)
#         schedule["forklifts"][forklift].append({"Hangar": hangar, "Time": current_time, "Job": "Load"})
        
#         current_time += 5
    
#     return schedule    
    
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
    