from mesa import Model, Agent
from mesa.space import MultiGrid
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import CanvasGrid
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
from mesa.visualization.modules import ChartModule, BarChartModule
from mesa.visualization.UserParam import Slider
import numpy as np
from static_values import NUM_INSTITUTIONS
from framework import SocialCapitalFramework
from MAS import MultiAgentSystem
from agents import DominantAgent, RandomAgent, SocialAgent
from scf import create_complete_scf

class MesaAgent(Agent):
    def __init__(self, unique_id, model, real_agent):
        super().__init__(unique_id, model)
        self.real_agent = real_agent  # Reference to the actual agent instance

    def step(self):
        self.real_agent.step()  # Delegate the step logic to the actual agent instance
        pass

def agent_portrayal(agent):
    if isinstance(agent.real_agent, DominantAgent):
        color = "red"
    elif isinstance(agent.real_agent, RandomAgent):
        color = "blue"
    else:  # Assumes other types are SocialAgents
        color = "green"

    portrayal = {
        "Shape": "circle",
        "Color": color,
        "Filled": "true",
        "Layer": 0,
        "r": 1
    }

    return portrayal

def calculate_grid_partitions(num_institutions, grid_width, grid_height, gap=6):
    """Calculate grid partitions for the given number of institutions with gaps."""
    per_row = int(np.ceil(np.sqrt(num_institutions)))
    # Adjust width and height to account for gaps
    width = (grid_width // per_row) - gap
    height = (grid_height // per_row) - gap
    partitions = []
    for i in range(per_row):
        for j in range(per_row):
            if len(partitions) < num_institutions:
                x_start = i * (width + gap) + gap/2
                y_start = j * (height + gap) + gap/2
                partitions.append((x_start, y_start, width, height))
    return partitions

def get_institution_number(institution_id):
    #Return the institution number from the institution_id or a random number if None
    if institution_id is None:
        return np.random.randint(NUM_INSTITUTIONS)
    else:
        return int(institution_id[len("institution"):])
    
def collect_trustworthiness(model):
    # This function collects the social capital data from each agent
    trustworthiness = {}

    scf = list(model.system.agents.values())[0].scf # Collect the scf from an agent
    for agent in model.schedule.agents:
        # Assuming you have a way to access trustworthiness and social_network scores
        trust = scf.data_structures['trustworthiness'].get(agent.unique_id, 0)
        # social_network = model.system.scf.data_structures['social_networks'].get(agent.unique_id, 0)
        trustworthiness[agent.unique_id] = trust

    sorted_trustworthiness = {"Social Agents": 0, "Dominant Agents": 0, "Random Agents": 0}

    for agent_id, social_capital in trustworthiness.items():
        # If it is an instance of social agent
        if isinstance(model.system.agents[agent_id], SocialAgent):
            sorted_trustworthiness["Social Agents"] += social_capital
        elif isinstance(model.system.agents[agent_id], DominantAgent):
            sorted_trustworthiness["Dominant Agents"] += social_capital
        else:
            sorted_trustworthiness["Random Agents"] += social_capital

    return  sorted_trustworthiness

def collect_institutions_capital(model):
    # This function collects the institutional capital data from each institution
    institutions_capital = {}
    for institution_id in range(NUM_INSTITUTIONS):
        institutions_capital["institution" + str(institution_id)] = 0

    scf = list(model.system.agents.values())[0].scf # Collect the scf from an agent

    for institution_id in range(NUM_INSTITUTIONS):
        # Assuming you have a way to access trustworthiness and social_network scores
        institution_capital = scf.data_structures['institutions'].get("institution" + str(institution_id), 0)
        institutions_capital["institution" + str(institution_id)] = institution_capital

    return institutions_capital

def collect_satisfaction(model):
    satisfaction = {"Social Agents": 0, "Dominant Agents": 0, "Random Agents": 0}

    for agent in list(model.system.agents.values()):
        if isinstance(agent, SocialAgent):
            satisfaction["Social Agents"] += agent.get_satisfaction()
        elif isinstance(agent, DominantAgent):
            satisfaction["Dominant Agents"] += agent.get_satisfaction()
        else:
            satisfaction["Random Agents"] += agent.get_satisfaction()


    # Calculate the total satisfaction
    total_satisfaction = sum(satisfaction.values())

    # Normalize the values between 0 and 1 if the total is not zero
    if total_satisfaction > 0:
        for key in satisfaction:
            satisfaction[key] /= total_satisfaction
            
    return satisfaction

def collect_social_capital(model):
    sc = {"Social Agents": 0, "Dominant Agents": 0, "Random Agents": 0}
    scf = list(model.system.agents.values())[0].scf # Collect the scf from an agent

    for agent in list(model.system.agents.values()):
        if isinstance(agent, SocialAgent):
            sc["Social Agents"] += agent.get_social_capital(scf)
        elif isinstance(agent, DominantAgent):
            sc["Dominant Agents"] += agent.get_social_capital(scf)
        else:
            sc["Random Agents"] += agent.get_social_capital(scf)

    return sc

class UDD(Model):
    def __init__(self, num_agents=30):
        super().__init__()
        self.num_agents = num_agents
        
        self.initialize_system()
       

        self.data_collector = DataCollector(
            model_reporters={
                "Trustworthiness": collect_trustworthiness,
                "Institutional Capital": collect_institutions_capital,
                "Satisfaction": collect_satisfaction,
                "Social Capital": collect_social_capital
                }
        )

    def initialize_system(self):
        # Create and setup the new system
        self.schedule = RandomActivation(self)
        self.grid = MultiGrid(50, 50, torus=False)
        scf = create_complete_scf()
        self.system = MultiAgentSystem(num_agents = self.num_agents)
        self.system.setup(scf)
        self.partitions = calculate_grid_partitions(NUM_INSTITUTIONS, self.grid.width, self.grid.height)
        self.place_agents()
    
    def place_agents(self):
        for agent_id, agent in self.system.agents.items():
            partition = self.partitions[get_institution_number(agent.chosen_dinner_group) % NUM_INSTITUTIONS]
            x = self.random.randrange(partition[0], partition[0] + partition[2])
            y = self.random.randrange(partition[1], partition[1] + partition[3])
            mesa_agent = MesaAgent(agent_id, self, agent)
            self.schedule.add(mesa_agent)
            self.grid.place_agent(mesa_agent, (x, y))

    def update_agent_positions(self):
        for agent in self.schedule.agents:
            institution_id = agent.real_agent.chosen_dinner_group
            institution_number = get_institution_number(institution_id)
            partition = self.partitions[institution_number % NUM_INSTITUTIONS]
            # Move agent to a random position within the designated partition
            x = self.random.randrange(partition[0], partition[0] + partition[2])
            y = self.random.randrange(partition[1], partition[1] + partition[3])
            self.grid.move_agent(agent, (x, y))

    def reset(self):
        print("Resetting the model")
        super().reset()
        self.initialize_system()

    def step(self):
        # Reset reputation data for each round
        self.system.reputation_sources['agents_reputation'].records = {}
        self.system.reputation_sources['institutional_reputation'].records = {}

        # First let each agent take their step
        self.schedule.step()

        # Then perform system-wide updates
        self.system.step()

        # Update agent positions on the grid
        self.update_agent_positions()

        self.data_collector.collect(self)


grid = CanvasGrid(agent_portrayal, 50, 50, 500, 500)

satisfaction_chart = ChartModule([
    {"Label": "Social Agents", "Color": "Green", "DataKey": "Satisfaction"},
    {"Label": "Dominant Agents", "Color": "Red", "DataKey": "Satisfaction"},
    {"Label": "Random Agents", "Color": "Blue", "DataKey": "Satisfaction"}
], data_collector_name='data_collector', canvas_height=100, canvas_width=200)

sc_chart = ChartModule([
    {"Label": "Social Agents", "Color": "Green", "DataKey": "Social Capital"},
    {"Label": "Dominant Agents", "Color": "Red", "DataKey": "Social Capital"},
    {"Label": "Random Agents", "Color": "Blue", "DataKey": "Social Capital"}
], data_collector_name='data_collector', canvas_height=100, canvas_width=200)


# Define a slider for the number of agents
agents_slider = Slider(
    name="Number of Agents",
    value=60,  # Initial number of agents
    min_value=3,
    max_value=300,
    step=3,  # Increment by 3
    description="Adjust the number of agents in the simulation"
)

server = ModularServer(UDD,
                       [grid, satisfaction_chart, sc_chart],
                       "Unscrupulous Diner's Dilemma",
                       {"num_agents": agents_slider})

server.launch()