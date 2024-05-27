from static_values import EXPEL_FROM_INSTITUTION_THRESHOLD, ADMIT_TO_INSTITUTION_THRESHOLD, DECISION_INDICATOR_WEIGHTS, COOPERATION_THRESHOLD, REPORT_REPUTATION_THRESHOLD, INEXPENSIVE_PRICE, EXPENSIVE_PRICE, AGENT_EVENT_WEIGHTS, AGENT_REPUTATION_WEIGHT, LEAVE_INSTITUTION_THRESHOLD, INSTITUTION_EVENT_WEIGHTS
import random
from events import ReputationEvent, SocialNetworkEvent, InstitutionEvent
import numpy as np

class Agent():
    def __init__(self, agent_id, scf, system):
        self.agent_id = agent_id
        self.scf = scf
        self.system = system
        self.institutions = set()
        self.last_ten_satisfactions = []
        self.chosen_dinner_group = None
        self.last_choice = "inexpensive"

    def calculate_utility(self, meal_type, individually_spent):
        joy = 0
        if meal_type == "expensive":
            joy += 1.5
        else:
            joy += 1
        
        current_satisfaction = joy / individually_spent
        # Append the new satisfaction and maintain only the last five entries
        self.last_ten_satisfactions.append(current_satisfaction)
        if len(self.last_ten_satisfactions) > 10:
            self.last_ten_satisfactions.pop(0)  # Remove the oldest satisfaction


    def get_satisfaction(self):
        return sum(self.last_ten_satisfactions) / len(self.last_ten_satisfactions)
    
    def get_social_capital(self, scf):
        trustworthiness = scf.metrics['trustworthiness'](scf, self.agent_id)
        social_network = scf.metrics['social_networks'](scf, self.agent_id)
        institutions = 0

        for institution in self.institutions:
            institutions += scf.metrics['institutions'](scf, institution)

        return trustworthiness + social_network + institutions

class SocialAgent(Agent):
    def __init__(self, agent_id, scf, system):
        self.agent_id = agent_id
        self.scf = scf
        self.system = system
        self.institutions = set()
        self.last_ten_satisfactions = []
        self.chosen_dinner_group = None
        self.last_choice = "inexpensive"

    def step(self):

        last_orders = self.system.institutions[self.chosen_dinner_group].last_orders
        events = self.system.institutions[self.chosen_dinner_group].events

        def process_events(events):
            # Process events and update social capital value

            if not events: # Indicates first round, no events to process
                return

            event_actions = {
                "Joined": ("social_network", "institutions"),
                "Left": ("social_network", "institutions"),
                "Expelled": ("social_network", "institutions"),
                "Sanctioned": ("social_network", "institutions"),
                "Not Sanctioned": ("social_network", "institutions"),
                "Cooperated": ("social_network", None),
                "Not Cooperated": ("social_network", None)
            }

            # Process each event in the list
            for event in events:
                # Check if the event type is in our predefined actions
                if event.type in event_actions:
                    # Handle social network update
                    try:
                        weight = INSTITUTION_EVENT_WEIGHTS[event.type]
                    except KeyError:
                        weight = AGENT_EVENT_WEIGHTS[event.type]
                    new_event = SocialNetworkEvent(event.type, weight, self.agent_id, event.agent_id)
                    self.scf.update_data("social_networks", new_event)
                    
                    # Handle institutional update if applicable
                    if event_actions[event.type][1]:
                        new_event = InstitutionEvent(event.type, INSTITUTION_EVENT_WEIGHTS[event.type], self.agent_id, self.chosen_dinner_group)
                        self.scf.update_data("institutions", new_event)
                else:
                    print(f"Event type {event.type} not found in event actions. Could not update scf from agent.")
        
        def process_orders(last_orders):
            # Process last orders and add events to the events set
    
            if not last_orders: # Indicates first round, no orders to process
                return

            bill_choices = {"expensive": 0, "inexpensive": 0}
            for choice in last_orders.items():
                meal_type = choice[1]
                bill_choices[meal_type] += 1

            bill_total = bill_choices["expensive"] * EXPENSIVE_PRICE + bill_choices["inexpensive"] * INEXPENSIVE_PRICE
            individually_spent = bill_total/len(last_orders)
            self_cost = EXPENSIVE_PRICE if self.last_choice == "expensive" else INEXPENSIVE_PRICE

            success = (individually_spent >= self_cost)

            for order in last_orders.items():
                their_agent_id = order[0]

                # Report if the meal was successful with probability q (Found in static_values.py)
                if random.random() < REPORT_REPUTATION_THRESHOLD:
                    self.system.reputation_sources['agents_reputation'].report_meal_success(their_agent_id, success)
     

        process_orders(last_orders)
        process_events(events)

    def choose_dinner_group(self): 
        """
        Choose the group dinner based on the highest social capital value among the institutions the agent is a member of.

        Returns:
        - (str): The name of the institution organizing the dinner with the highest social capital, or None if not a member of any institutions.
        """

        while not self.institutions:
            print(f"Agent {self.agent_id} is not a member of any institutions. Joining one.")
            institution = self.choose_institution_to_join(self.system.institutions)
            self.system.institutions[institution].add_member(self.agent_id)

        # Initialize variables to find the institution with the highest social capital
        highest_social_capital = -float('inf')
        self.chosen_dinner_group = None

        # Iterate over each institution the agent is a member of
        for institution_id in self.institutions:
            social_capital = self.scf.metrics["institutions"](self.scf, institution_id)
            if social_capital > highest_social_capital:
                highest_social_capital = social_capital
                self.chosen_dinner_group = institution_id

        return self.chosen_dinner_group
        
    def decide(self, dinner_group):
        """
        Calculate the cooperation score for an agent based on the social capital indicators.
        scf: instance of SocialCapitalFramework containing all social capital data and metrics.
        """

        institutions_sc = 0
        for institution in self.institutions:
            # Get SC of all institutions the agent is member of
            sc = self.scf.metrics['institutions'](self.scf, institution)
            institutions_sc += sc

        indicators = {
            'agents_reputation': self.scf.data_structures['trustworthiness'].get(self.agent_id, 0),
            'institutional_reputation': self.scf.data_structures['trustworthiness'].get(dinner_group, 1),
            'social_networks': self.scf.metrics['social_networks'](self.scf, self.agent_id),
            'institution': institutions_sc
        }

        # Compute the weighted sum of social capital indicators
        cooperation_score = sum(DECISION_INDICATOR_WEIGHTS[key] * indicators[key] for key in DECISION_INDICATOR_WEIGHTS.keys())

        if cooperation_score < COOPERATION_THRESHOLD:
            self.last_choice = "expensive"
            return self.last_choice
        else:
            self.last_choice = "inexpensive"
            return self.last_choice

    def choose_institution_to_join(self, all_institutions):
        """
        Choose an institution based on social capital values using a Boltzmann distribution.
        
        Parameters:
        - action (str): 'Join' or 'Leave'
        - institutions (dict): Dictionary where keys are institution names and values are their social capital values
        
        Returns:
        - (str): The chosen institution name
        """

        # Filter institutions based on if the agent is already member
        filtered_institutions = {k: v for k, v in all_institutions.items() if k not in self.institutions}
        
        chosen_institution = None

        while chosen_institution is None:
         
            if filtered_institutions == {}:
                print("No institution to join.")
                break

            sc_set = {}
            # Fetch social capital values and compute probabilities
            for institution_id in filtered_institutions.keys():
                sc_set[institution_id] = self.scf.metrics['institutions'](self.scf, institution_id)

            values = np.array(list(sc_set.values()))

            probabilities = np.exp(values) / np.sum(np.exp(values))
            chosen_institution = np.random.choice(list(filtered_institutions.keys()), p=probabilities)
            filtered_institutions.pop(chosen_institution, None) 

        return chosen_institution
    
    def evaluate_institutions(self):
        for institution in self.institutions:
            if  self.scf.metrics['institutions'](self.scf, institution) < LEAVE_INSTITUTION_THRESHOLD:
                self.system.institutions[institution].remove_member(self.agent_id, self.agent_id)
                print(f"Agent {self.agent_id} left institution {institution}.")
            break

    def vote(self, action_type, agent_id):

        # Calculate social capital of the agent
        # Social network is the agents connection to the other agent
        social_network_capital = self.scf.data_structures['social_networks'][self.agent_id].get(agent_id, 0)
        trustworthiness_capital = self.scf.metrics['trustworthiness'](self.scf, agent_id)

        sc = social_network_capital + trustworthiness_capital

        if action_type == "Expel":
            if sc < EXPEL_FROM_INSTITUTION_THRESHOLD:
                return True
            else:
                return False
        elif action_type == "Join":
            if sc > ADMIT_TO_INSTITUTION_THRESHOLD:
                return True
            else:
                return False


class RandomAgent(Agent):
    def __init__(self, agent_id, scf, system):
        self.agent_id = agent_id
        self.system = system
        self.institutions = set()
        self.last_ten_satisfactions = []
        self.chosen_dinner_group = None
        self.last_choice = "inexpensive"

    def step(self):
        self.process_orders(self.system.institutions[self.chosen_dinner_group].last_orders)

    def choose_dinner_group(self):
        possible_institutions = self.system.institutions.keys()

        while not self.institutions:
            print(f"Agent {self.agent_id} is not a member of any institutions. Joining one.")
            institution = self.choose_institution_to_join(self.system.institutions)
            possible_institutions.institutions.remove(institution)
            self.system.institutions[institution].add_member(self.agent_id)

        self.chosen_dinner_group = random.choice(list(self.institutions))
        return self.chosen_dinner_group

    def choose_institution_to_join(self, all_institutions):
        # Has no info of the institutions social capital, so chooses randomly between institutions
        return random.choice(list(all_institutions.keys()))

    def decide(self, dinner_group):
        return random.choice(["expensive", "inexpensive"])

    def vote(self, action_type, agent_id):
        return random.choice([True, False])

    def process_orders(self, last_orders):
            # Process last orders and add events to the events set
    
            if not last_orders: # Indicates first round, no orders to process
                return

            bill_choices = {"expensive": 0, "inexpensive": 0}
            for choice in last_orders.items():
                meal_type = choice[1]
                bill_choices[meal_type] += 1

            bill_total = bill_choices["expensive"] * EXPENSIVE_PRICE + bill_choices["inexpensive"] * INEXPENSIVE_PRICE
            individually_spent = bill_total/len(last_orders)
            self_cost = EXPENSIVE_PRICE if self.last_choice == "expensive" else INEXPENSIVE_PRICE

            success = (individually_spent >= self_cost)

            for order in last_orders.items():
                their_agent_id = order[0]

                # Report if the meal was successful with probability q (Found in static_values.py)
                if random.random() < REPORT_REPUTATION_THRESHOLD:
                    self.system.reputation_sources['agents_reputation'].report_meal_success(their_agent_id, success)
     

class DominantAgent(Agent):
    def __init__(self, agent_id, scf, system):
        self.agent_id = agent_id
        self.system = system
        self.institutions = set()
        self.last_ten_satisfactions = []
        self.chosen_dinner_group = None
        self.last_choice = "expensive"

    def step(self):
        self.process_orders(self.system.institutions[self.chosen_dinner_group].last_orders)

    def choose_dinner_group(self):
        # If there are no institutions in the set, retry until there is one
        possible_institutions = self.system.institutions.keys()

        while not self.institutions:
            print(f"Agent {self.agent_id} is not a member of any institutions. Joining one.")
            institution = self.choose_institution_to_join(self.system.institutions)
            possible_institutions.institutions.remove(institution)
            self.system.institutions[institution].add_member(self.agent_id)

        self.chosen_dinner_group = random.choice(list(self.institutions))
        return self.chosen_dinner_group

    def choose_institution_to_join(self, all_institutions):
        # Has no info of the institutions social capital, so chooses randomly between institutions
        return random.choice(list(all_institutions.keys()))

    def decide(self, dinner_group):
        return "expensive"

    def vote(self, action_type, agent_id):
        return random.choice([True, False])

    def process_orders(self, last_orders):
            # Process last orders and add events to the events set
    
            if not last_orders: # Indicates first round, no orders to process
                return

            bill_choices = {"expensive": 0, "inexpensive": 0}
            for choice in last_orders.items():
                meal_type = choice[1]
                bill_choices[meal_type] += 1

            bill_total = bill_choices["expensive"] * EXPENSIVE_PRICE + bill_choices["inexpensive"] * INEXPENSIVE_PRICE
            individually_spent = bill_total/len(last_orders)
            self_cost = EXPENSIVE_PRICE if self.last_choice == "expensive" else INEXPENSIVE_PRICE

            success = (individually_spent >= self_cost)

            for order in last_orders.items():
                their_agent_id = order[0]

                # Report if the meal was successful with probability q (Found in static_values.py)
                if random.random() < REPORT_REPUTATION_THRESHOLD:
                    self.system.reputation_sources['agents_reputation'].report_meal_success(their_agent_id, success)
     
