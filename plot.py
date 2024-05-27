import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict

def read_and_plot(file_path):
    # Read the CSV file
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Initialize dictionaries to hold satisfaction data and breakpoints
    satisfaction_data = defaultdict(lambda: {"Social Agent": 0, "Dominant Agent": 0, "Random Agent": 0})
    breakpoints = {}

    # Parse the CSV file data
    round_num = None
    for line in lines:
        line = line.strip()
        if line.startswith("Round"):
            round_num = int(line.split()[1])
        elif "Social Agents" in line:
            satisfaction_data[round_num]["Social Agent"] = float(line.split(":")[1].strip())
        elif "Dominant Agents" in line:
            satisfaction_data[round_num]["Dominant Agent"] = float(line.split(":")[1].strip())
        elif "Random Agents" in line:
            satisfaction_data[round_num]["Random Agent"] = float(line.split(":")[1].strip())
        elif line.startswith("Average breakpoint for"):
            agent_amount = int(line.split()[3])
            avg_rounds = float(line.split(":")[1].strip())
            breakpoints[agent_amount] = avg_rounds

    # Convert satisfaction_data to a DataFrame
    satisfaction_df = pd.DataFrame.from_dict(satisfaction_data, orient='index').sort_index()

    # Plot satisfaction over rounds
    plt.figure(figsize=(10, 5))
    plt.plot(satisfaction_df.index, satisfaction_df["Social Agent"], label="Social Agent", marker='o')
    plt.plot(satisfaction_df.index, satisfaction_df["Dominant Agent"], label="Dominant Agent", marker='o')
    plt.plot(satisfaction_df.index, satisfaction_df["Random Agent"], label="Random Agent", marker='o')
    plt.xlabel("Rounds")
    plt.ylabel("Satisfaction")
    plt.title("Satisfaction of Agents Over Rounds")
    plt.legend()
    plt.grid(True)
    plt.show()

    # Plot breakpoints
    agent_amounts = list(breakpoints.keys())
    avg_rounds = list(breakpoints.values())

    plt.figure(figsize=(10, 5))
    plt.plot(agent_amounts, avg_rounds, marker='o', linestyle='-', color='purple')
    plt.xlabel("Number of Agents")
    plt.ylabel("Average Rounds to Breakpoint")
    plt.title("Average Rounds to Breakpoint for Different Numbers of Agents")
    plt.grid(True)
    plt.show()

# Example usage
file_path = "simulation_results.csv"  # Replace with your file path
read_and_plot(file_path)
