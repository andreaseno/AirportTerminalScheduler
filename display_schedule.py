import json
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import sys

def parse_int_time(t):
    hour = t // 100
    minute = t % 100
    return datetime(2025, 1, 1, hour, minute)

def visualize_single_plot_datetime(schedule_path="schedule.json"):
    with open(schedule_path, 'r') as f:
        data = json.load(f)

    aircraft_data = data.get("aircraft", {})
    trucks_data = data.get("trucks", {})
    forklifts_data = data.get("forklifts", {})
    if aircraft_data is None or trucks_data is None or forklifts_data is None:
        print("No valid solution. Cannot plot.")
        return

    plot_bars = []
    y_labels = []
    current_y = 0

    # [1] AIRCRAFT
    aircraft_sorted = sorted(aircraft_data.items(), key=lambda x: x[1]["Arrival"])
    for ac_name, info in aircraft_sorted:
        start_dt = parse_int_time(info["Arrival"])
        end_dt = parse_int_time(info["Departure"])
        plot_bars.append({
            "y": current_y,
            "start": start_dt,
            "end": end_dt,
            "label": f"{ac_name}\nHangar: {info['Hangar']} "
                     f"({start_dt.strftime('%H:%M')}-{end_dt.strftime('%H:%M')})"
        })
        y_labels.append(ac_name)
        current_y += 1

    # if aircraft_sorted:
    #     current_y += 1

    # [2] TRUCKS
    trucks_sorted = sorted(trucks_data.items(), key=lambda x: x[1]["Arrival"])
    for truck_name, info in trucks_sorted:
        start_dt = parse_int_time(info["Arrival"])
        end_dt   = parse_int_time(info["Departure"])
        plot_bars.append({
            "y": current_y,
            "start": start_dt,
            "end": end_dt,
            "label": f"{truck_name}\nHangar: {info['Hangar']} "
                     f"({start_dt.strftime('%H:%M')}-{end_dt.strftime('%H:%M')})"
        })
        y_labels.append(truck_name)
        current_y += 1

    # if trucks_sorted:
    #     current_y += 1

    # [3] FORKLIFTS
    forklift_durations = {"Unload": 20, "Load": 5}
    forklift_names = sorted(forklifts_data.keys())
    for fk_name in forklift_names:
        y_labels.append(fk_name)
        fk_y = current_y
        current_y += 1

        jobs = sorted(forklifts_data[fk_name], key=lambda j: j["Time"])
        for job in jobs:
            start_dt = parse_int_time(job["Time"])
            duration = forklift_durations.get(job["Job"], 0)
            # Use Python's datetime.timedelta to add minutes
            end_dt = start_dt + timedelta(minutes=duration)

            job_str = (f"{job['Job'][0]} @ {job['Hangar'][0]} "
                       f"({start_dt.strftime('%H:%M')}-{end_dt.strftime('%H:%M')})")
            plot_bars.append({
                "y": fk_y,
                "start": start_dt,
                "end": end_dt,
                "label": job_str
            })

    fig, ax = plt.subplots()

    all_dates = []
    for bar in plot_bars:
        start_num = mdates.date2num(bar["start"])
        end_num = mdates.date2num(bar["end"])
        width = end_num - start_num

        ax.barh(bar["y"], width, left=start_num, align='center')
        midpoint = (start_num + end_num) / 2
        ax.text(
            midpoint, bar["y"],
            bar["label"],
            ha='center', va='center', fontsize=8, rotation = 30
        )
        all_dates.extend([start_num, end_num])

    # Y-axis labels
    y_positions = list(range(len(y_labels)))
    ax.set_yticks(y_positions)
    ax.set_yticklabels(y_labels)

    ax.set_ylabel("Aircraft / Trucks / Forklifts (stacked)")
    ax.set_title("Combined Timeline with Real Time Spacing")

    # Tell Matplotlib these are date values
    ax.xaxis_date()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    # Optionally adjust the major tick locator, e.g. every 15 minutes
    # ax.xaxis.set_major_locator(mdates.MinuteLocator(interval=15))

    # Pad the x-limits
    if all_dates:
        min_x = min(all_dates) - (1 / 1440) * 10  # 10 minutes
        max_x = max(all_dates) + (1 / 1440) * 10
        ax.set_xlim(min_x, max_x)

    ax.set_xlabel("Time (HH:MM)")
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(sys.argv[1])
        visualize_single_plot_datetime(sys.argv[1])
    else:
        visualize_single_plot_datetime("MyTests/test4/my_schedule.json")