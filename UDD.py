from static_values import EXPENSIVE_PRICE, INEXPENSIVE_PRICE
from scf import create_complete_scf
from MAS import MultiAgentSystem
from agents import SocialAgent, DominantAgent, RandomAgent
import time
import sys
import contextlib
import io
from contextlib import contextmanager
from collections import defaultdict

# Context manager to suppress print statements
@contextlib.contextmanager
def suppress_print():
    # Redirect stdout to a string IO
    original_stdout = sys.stdout
    sys.stdout = io.StringIO()
    try:
        yield
    finally:
        sys.stdout = original_stdout

class UDD:
    def __init__(self, num_agents = 60):
        self.num_agents = num_agents

    def initialize_system(self):
        # Create and setup the new system
        scf = create_complete_scf()
        self.system = MultiAgentSystem(num_agents = self.num_agents)
        self.system.setup(scf)

    def step(self):
        # Reset reputation data for each round
        self.system.reputation_sources['agents_reputation'].records = {}
        self.system.reputation_sources['institutional_reputation'].records = {}

        # First let each agent take their step
        for agent in self.system.agents.values():
            agent.step()

        # Then perform system-wide updates
        self.system.step()

    def check_breakpoint(self):
        # Check wether the system has reached a breakpoint
        # The system has reached a breakpoint if the the social agents have surpassed the other agents for the last 5 rounds

        # Get the satisfaction of the last rounds for each agent type
        social_satisfactions = []
        dominant_satisfactions = []
        random_satisfactions = []

        for agent in self.system.agents.values():
            if isinstance(agent, SocialAgent):
                social_satisfactions.append(agent.last_ten_satisfactions) # Appends the array of satisfactions
            elif isinstance(agent, DominantAgent):
                dominant_satisfactions.append(agent.last_ten_satisfactions)
            else:
                random_satisfactions.append(agent.last_ten_satisfactions)

        # Check if the social agents have surpassed the other agents for the last 5 rounds
        sum_social = sum([sum(satisfaction) for satisfaction in social_satisfactions])
        sum_dominant = sum([sum(satisfaction) for satisfaction in dominant_satisfactions])
        sum_random = sum([sum(satisfaction) for satisfaction in random_satisfactions])

        return sum_social > sum_dominant and sum_social > sum_random


    
    def get_average_satisfactions(self):
        # Get the average satisfaction of the agents

        satisfactions = {"Social Agent": 0, "Dominant Agent": 0, "Random Agent": 0}

        for agent in self.system.agents.values():
            if isinstance(agent, SocialAgent):
                satisfactions["Social Agent"] += agent.get_satisfaction()
            elif isinstance(agent, DominantAgent):
                satisfactions["Dominant Agent"] += agent.get_satisfaction()
            else:
                satisfactions["Random Agent"] += agent.get_satisfaction()

        # Return the average satisfaction of each agent type
        return {key: value/(self.num_agents/3) for key, value in satisfactions.items()}

def play_satisfaction(file):
    start_time = time.time()

    # Run simulations
    ROUNDS = 100
    GAMES = 50

    averages = {"Social Agent": 0, "Dominant Agent": 0, "Random Agent": 0}

    
    udd = UDD()

    round_satisfactions = defaultdict(lambda: {"Social Agent": 0, "Dominant Agent": 0, "Random Agent": 0})
    round_counts = defaultdict(int)

    for game in range(GAMES):
        game_start_time = time.time()

        udd.initialize_system()


        # Play the game for a set amount of rounds
        with suppress_print():
            for round_num in range(ROUNDS):
                udd.step()

                # Collect satisfaction every second round
                if round_num % 2 == 1:
                    current_averages = udd.get_average_satisfactions()
                    for key, value in current_averages.items():
                        round_satisfactions[round_num + 1][key] += value
                    round_counts[round_num + 1] += 1
        
        # Add the average satisfaction of each agent type to the averages
        for key, value in udd.get_average_satisfactions().items():
            averages[key] += value

        game_end_time = time.time()
        print(f"Game {game+1} - Total game time: {game_end_time - game_start_time} seconds")

    # Calculate average satisfaction for each recorded round
    average_satisfactions_per_round = defaultdict(lambda: {"Social Agent": 0, "Dominant Agent": 0, "Random Agent": 0})
    for round_num, counts in round_counts.items():
        for key in round_satisfactions[round_num]:
            average_satisfactions_per_round[round_num][key] = round_satisfactions[round_num][key] / counts

    # Log averages to the file
    # file.write("Satisfaction\n")
    # file.write(f"Social Agents: {averages['Social Agent']/GAMES}\n")
    # file.write(f"Dominant Agents: {averages['Dominant Agent']/GAMES}\n")
    # file.write(f"Random Agents: {averages['Random Agent']/GAMES}\n")
    # file.write("\n")
    # file.flush()

    # Print the average satisfaction of each agent type
    for key, value in averages.items():
        print(f"Average satisfaction of {key}: {value/GAMES}")


    print()
    end_time = time.time()
    print(f"play_satisfaction() took {end_time - start_time} seconds")
    print()

    # Return the averages of the satisfaction of each agent type
    for key, value in averages.items():
        averages[key] = value/GAMES
    
    #return averages
    return average_satisfactions_per_round




def play_breakpoints(file):
    start_time = time.time()

    MAXROUNDS = 1000
    GAMES = 50
    breakpoints = {15: 0, 30: 0, 60: 0, 90: 0, 120: 0, 150: 0, 180: 0, 240: 0, 300: 0}


    for game in range(GAMES):
        game_start_time = time.time()

        for game_type in breakpoints.keys():

            udd = UDD(num_agents = game_type)
            udd.initialize_system()
            breakpoint = None

            # Play until the breakpoint is reached, or rounds reach 1000
            with suppress_print():
                for round in range(MAXROUNDS):
                    udd.step()
                    if udd.check_breakpoint():
                        # Records what round the breakpoint was reached
                        breakpoint = round
                        breakpoints[game_type] += round
                        break
            
            if breakpoint is None:
                print(f"Breakpoint for {game_type} agents was never reached")
                # If the breakpoint was never reached, add the max rounds to the breakpoints
                breakpoints[game_type] += int(MAXROUNDS)
            
        game_end_time = time.time()
        print(f"Game {game+1} - Total game time: {game_end_time - game_start_time} seconds")


    # Log breakpoints to the file
    # file.write("Breakpoints\n")
    # for key, value in breakpoints.items():
    #     file.write(f"{key}:{value/GAMES}\n")
    # file.write("\n")
    # file.flush()

    # Print the breakpoints average breakpoint for each game type
    for key, value in breakpoints.items():
        print(f"Average breakpoint for {key} agents: {value/GAMES}")

    end_time = time.time()
    print(f"play_breakpoints() took {end_time - start_time} seconds")

    # Return the average breakpoints for each game type
    for key, value in breakpoints.items():
        breakpoints[key] = value/GAMES

    return breakpoints

    

def run_simulations(num):

    averages = {"Social Agent": 0, "Dominant Agent": 0, "Random Agent": 0}
    breakpoints = {15: 0, 30: 0, 60: 0, 90: 0, 120: 0, 150: 0, 180: 0, 240: 0, 300: 0}
    times = []
    average_satisfactions_per_round = defaultdict(lambda: {"Social Agent": 0, "Dominant Agent": 0, "Random Agent": 0})
    round_counts = defaultdict(int)

    sim_start = time.time()

    # Run simulations and add to the averages and breakpoints
    with open('simulation_results.csv', 'w') as file:
        for simulation_nr in range(num):
            print(f"Running simulation {simulation_nr+1}")
            start_time = time.time()

            satisfactions = play_satisfaction(file)

            # for key, value in satisfactions.items():
            #     averages[key] += value
            for round_num, averages in satisfactions.items():
                for key, value in averages.items():
                    average_satisfactions_per_round[round_num][key] += value
                round_counts[round_num] += 1
            
            points = play_breakpoints(file)

            for key, value in points.items():
                breakpoints[key] += value
        
            end_time = time.time()
            print(f"Simulation {simulation_nr+1} took {end_time - start_time} seconds")
            times.append(end_time - start_time)

            # # Write the time it took to run the simulation to the file
            # file.write(f"Simulation {simulation_nr+1} took {end_time - start_time} seconds\n")
            # file.write(f"Total time elapsed: {end_time - sim_start} seconds\n\n")

            # Write averages every tenth round to file
            # if (simulation_nr+1) % 10 == 0:
            #     file.write("Simulation Results so far\n")
            #     for key, value in averages.items():
            #         file.write(f"Average satisfaction of {key}: {value/(simulation_nr+1)}\n")
                
            #     for key, value in breakpoints.items():
            #         file.write(f"Average breakpoint for {key} agents: {value/(simulation_nr+1)}\n")

            #     file.write("\n")
            #     file.flush()
                

        # Write the results to file
        # file.write("Simulation Results\n")
        # for key, value in averages.items():
        #     file.write(f"Average satisfaction of {key}: {value/num}\n")
    

    # Calculate final average satisfactions per round
    for round_num, counts in round_counts.items():
        for key in average_satisfactions_per_round[round_num]:
            average_satisfactions_per_round[round_num][key] /= num

    with open('simulation_results.csv', 'w') as file:
        file.write("Simulation Results\n")
        for round_num, averages in average_satisfactions_per_round.items():
            file.write(f"Round {round_num}\n")
            file.write(f"Social Agents: {averages['Social Agent']}\n")
            file.write(f"Dominant Agents: {averages['Dominant Agent']}\n")
            file.write(f"Random Agents: {averages['Random Agent']}\n")
            file.write("\n")

        for key, value in breakpoints.items():
            file.write(f"Average breakpoint for {key} agents: {value/num}\n")

    # Print the averages and breakpoints
    print()
    print("Averages:")
    for key, value in averages.items():
        print(f"Average satisfaction of {key}: {value/num}")

    print()
    print("Breakpoints:")
    for key, value in breakpoints.items():
        print(f"Average breakpoint for {key} agents: {value/num}")
    
    print()

    sim_end = time.time()
    print(f"run_simulations() took {sim_end - sim_start} seconds")
    for num in range(len(times)):
        print(f"Simulation {num} took {times[num]} seconds")
    print()

run_simulations(10)