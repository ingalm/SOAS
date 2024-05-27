from static_values import EXPENSIVE_PRICE, INEXPENSIVE_PRICE, NUM_AGENTS, NUM_INSTITUTIONS, JOIN_INSTITUTION_THRESHOLD, AGENT_REPUTATION_WEIGHT, INSTITUTION_EVENT_WEIGHTS, AGENT_EVENT_WEIGHTS, RULE_VIOLATION_THRESHOLD
from agents import SocialAgent, DominantAgent, RandomAgent
from reputations import AgentsReputation, InstitutionalReputation
from events import ReputationEvent, Event, InstitutionEvent
import random

# Not useful in our implementation of the game
class Network:
    def __init__(self):
        self.connections = {}

    def add_connection(self, agent1, agent2):
        # Ensure there is a set for agent1 and add agent2's ID to it
        self.connections.setdefault(agent1.agent_id, set()).add(agent2.agent_id)
        # Ensure there is a set for agent2 and add agent1's ID to it
        self.connections.setdefault(agent2.agent_id, set()).add(agent1.agent_id)

class Institution:
    def __init__(self, institution_id, rules, system):
        self.system = system
        self.institution_id = institution_id
        self.members = set()
        self.last_orders = set()
        self.events = set()
        self.violations = {}
        # Initialize rules with default values or provided values if specific rules are passed
        self.rules = {
            'vote': rules.get('vote', False),  # True if members must vote on key decisions
            'compulsory_cooperation': rules.get('compulsory_cooperation', False),  # True if members must choose inexpensive options
            'sanctions': rules.get('sanctions', False),  # True if sanctions are imposed for rule violations
            'graduated_sanctions': rules.get('graduated_sanctions', False)  # True if sanctions increase for repeated violations
        }

    def print_events(self):
        # Create dictionaries to store what agents made what action, and what type of agent they were
        expulsions = {}
        sanctions = {}
        cooperations = {}
        non_cooperations = {}

        for event in self.events:
            if isinstance(self.system.agents[event.agent_id], SocialAgent):
                agent_type = "Social Agent"
            elif isinstance(self.system.agents[event.agent_id], DominantAgent):
                agent_type = "Dominant Agent"
            else:
                agent_type = "Random Agent"

            if event.type == "Expelled":
                expulsions[event.agent_id] = agent_type
            elif event.type == "Sanctioned":
                sanctions[event.agent_id] = agent_type
            elif event.type == "Cooperated":
                cooperations[event.agent_id] = agent_type
            elif event.type == "Not Cooperated":
                non_cooperations[event.agent_id] = agent_type

    def add_member(self, agent_id):
        # Voting might be required to add a member if the 'vote' rule is True
        if self.rules['vote']:
            print(f"Vote required to add Agent {agent_id} to {self.institution_id}.")
            passed = self.vote_on("Join", agent_id)
            if passed:
                self.members.add(agent_id)
                self.system.agents[agent_id].institutions.add(self.institution_id)
                self.violations[agent_id] = 0
                event = InstitutionEvent("Joined", INSTITUTION_EVENT_WEIGHTS["Joined"], agent_id, self.institution_id)
                self.events.add(event)

                print(f"Vote for agent {agent_id} to join {self.institution_id} passed. Agent joined")

                return event
            else:
                print(f"Vote for agent {agent_id} to join {self.institution_id} did not pass.")
                return None
        
        else:
            self.members.add(agent_id)
            self.system.agents[agent_id].institutions.add(self.institution_id)
            self.violations[agent_id] = 0
            event = InstitutionEvent("Joined", INSTITUTION_EVENT_WEIGHTS["Joined"], agent_id, self.institution_id)
            self.events.add(event)
            print(f"Agent {agent_id} added to {self.institution_id} without a vote.")

            return event

    def remove_member(self, agent_id, source):
        """
        Remove a member from the institution
        :param agent_id: ID of the agent to remove
        :param source: The source of the request to remove the member, can be the member itself, or an expulsion call
        """
        # Voting might be required to remove a member if the 'vote' rule is True
        if self.rules['vote']:
            if source == agent_id: # Agent wanted to leave
                self.members.discard(agent_id)
                self.system.agents[agent_id].institutions.discard(self.institution_id)
                event = InstitutionEvent("Left", INSTITUTION_EVENT_WEIGHTS["Left"], agent_id, self.institution_id)
                self.events.add(event)
                print(f"Agent {agent_id} left {self.institution_id} without a vote.")
                
                return event

            print(f"Vote required to remove Agent {agent_id} from {self.institution_id}.")

            passed = self.vote_on("Expel", agent_id)
            if passed:
                self.members.discard(agent_id)
                self.system.agents[agent_id].institutions.discard(self.institution_id)
                event = InstitutionEvent("Expelled", INSTITUTION_EVENT_WEIGHTS["Expelled"], agent_id, self.institution_id)
                self.events.add(event)
                print(f"Vote for agent {agent_id} to be expelled from {self.institution_id} passed. Agent expelled.")

                return event
            else:
                print(f"Vote for agent {agent_id} to be expelled from {self.institution_id} did not pass.")
                return None
        else:
            self.members.discard(agent_id)
            self.system.agents[agent_id].institutions.discard(self.institution_id)
            event = InstitutionEvent("Left", INSTITUTION_EVENT_WEIGHTS["Left"], agent_id, self.institution_id)
            self.events.add(event)
            print(f"Agent {agent_id} removed from {self.institution_id} without a vote. (Expelled or left by choice)")

            return event

    def apply_rules(self, choice):
        # Gå gjennom de forskjellige reglene og sjekk om de er aktuelle for eventet
        agent_id = choice[0]
        meal_choice = choice[1]

        # Sjekke om rule = compulsory cooperation
        if self.rules['compulsory_cooperation']:
            if meal_choice == "expensive":
                if self.rules['sanctions']:
                    # If sanctions, New Event = Sanctioned
                    self.apply_sanction(agent_id)
                    new_event = Event("Sanctioned", INSTITUTION_EVENT_WEIGHTS["Sanctioned"], agent_id)
                    self.events.add(new_event)
                    # Else New Event = Not Sanctioned
                else:
                    new_event = Event("Not Sanctioned", INSTITUTION_EVENT_WEIGHTS["Not Sanctioned"], agent_id)
                    self.events.add(new_event)

        if meal_choice == "inexpensive":
            cooperation_event = Event("Cooperated", AGENT_EVENT_WEIGHTS["Cooperated"], agent_id)
            self.events.add(cooperation_event)
        else:
            cooperation_event = Event("Not Cooperated", AGENT_EVENT_WEIGHTS["Not Cooperated"], agent_id)
            self.events.add(cooperation_event)

        return cooperation_event

    def apply_sanction(self, agent_id):
        if self.rules['graduated_sanctions']:
            # Implement graduated sanctions logic
            pass
        else:
            self.violations[agent_id] += 1

    def update_institution(self, group_choices):
        #Each institution is updated with it members’ actions from last round
        events = set()
        for choice in group_choices.items():
            if choice[0] in self.members: # Checks if action as made by an institution member
                group_choices[choice[0]] = choice[1]
                event = self.apply_rules(choice) #Applies rules to the choice and saves choice to the institution, also updates institution reputation
                events.add(event)

    def evaluate_members(self):
        # Evaluate the members of the institution and remove if necessary
        for member in self.members:
            if self.violations[member] > RULE_VIOLATION_THRESHOLD:
                print(f"Agent {member} has violated the rules of {self.institution_id} too many times. Initiating removal.")
                self.remove_member(member, "violation")

    def vote_on(self, action_type, agent_id):
        # Initialize or reset votes for the particular action
        votes = {'for': 0, 'against': 0}

        # Each member votes
        for member in self.members:
            if member == agent_id:
                continue  # A member cannot vote on their own case
            member_vote = self.system.agents[member].vote(action_type, agent_id)
            if member_vote:
                votes['for'] += 1
            else:
                votes['against'] += 1

        print(f"Voting results for {action_type} {agent_id}: {votes['for']} for, {votes['against']} against")

        # Simple majority decision
        if votes['for'] ==  0 and votes['against'] == 0: # In this case no agent has joined yet, and the vote is considered passed
            return True

        return votes['for'] > votes['against']

    def add_event(self, event):
        self.events.add(event)

    def clear_events(self):
        self.events = set()


class MultiAgentSystem:
    def __init__(self, num_agents = 30):
        self.agents = {}
        self.reputation_sources = {}
        self.network = Network()
        self.institutions = {}
        self.games = {}
        self.num_agents = num_agents

    def setup(self, scf):
        # Attaching the defined reputations
        agents_reputation = AgentsReputation()
        institutional_reputation = InstitutionalReputation()

        self.reputation_sources['agents_reputation'] = agents_reputation
        self.reputation_sources['institutional_reputation'] = institutional_reputation

        agent_id = 0
        
        num_of_type = int(self.num_agents / 3)

        #Setup for the agents
        for _ in range(num_of_type):
            self.agents["agent" + str(agent_id)] = SocialAgent("agent" + str(agent_id), scf, self)
            agent_id += 1

        for _ in range(num_of_type):
            self.agents["agent" + str(agent_id)] = DominantAgent("agent" + str(agent_id), scf, self)
            agent_id += 1

        for _ in range(num_of_type):
            self.agents["agent" + str(agent_id)] = RandomAgent("agent" + str(agent_id), scf, self)
            agent_id += 1

        institution_id = 0
        for num in range(NUM_INSTITUTIONS):
            # Create ruleset, must ensure at least one institution without voting rule, to prevent deadloops
            if num == 0:
                rules = {
                    'vote': False,
                    'compulsory_cooperation': random.choice([True, False]),
                    'sanctions': random.choice([True, False]),
                    'graduated_sanctions': random.choice([True, False])
                }
            else:
                rules = {
                    'vote': random.choice([True, False]),
                    'compulsory_cooperation': random.choice([True, False]),
                    'sanctions': random.choice([True, False]),
                    'graduated_sanctions': random.choice([True, False])
                }

            institution = Institution("institution" + str(institution_id), rules, self)
            self.institutions["institution" + str(institution_id)] = institution

            institution_id += 1

        for agent in self.agents.values():
            agent.institutions.add(random.choice(list(self.institutions.keys())))

        # Setup the institutions social capital. Each institution starts with a capital of 0.5
        scf.data_structures["institutions"] = {institution: 0.5 for institution in self.institutions.keys()}
        
        # Setup the agents social capital. Each agent starts with a capital of 0.5
        scf.data_structures["trustworthiness"] = {agent: 0.5 for agent in self.agents.keys()}

        # Setup the social network. Each agent starts with a score of 0 with all other agents
        scf.data_structures["social_networks"] = {agent: {other_agent: 0 for other_agent in self.agents.keys()} for agent in self.agents.keys()}

        # All agents choose a dinner group first
        for agent in self.agents.values():
            while agent.institutions == None:
                print(f"Agent {agent.agent_id} has no institution to dine with. Choosing a new one.")
                institution = agent.choose_institution_to_join(self.institutions)
                self.institutions[institution].add_member(agent.agent_id)

            agent.choose_dinner_group()



    def step(self): 
        # Updates reputation from the reported values by the agent in agent.step()
        scf = list(self.agents.values())[0].scf
        for agent in self.agents.keys(): 
            value = self.reputation_sources['agents_reputation'].get_reputation(agent)
            event = ReputationEvent("reputation", AGENT_REPUTATION_WEIGHT, agent, value)
            scf.update_data('trustworthiness', event)

        # This step must be done here so that the joining and leaving of institutions in the next lines can be recorded.
        for institution in self.institutions.values():
            institution.clear_events() # Clears the messages for them to be updated with the next rounds

        # JOIN OR LEAVE INSTITUTIONS
        for agent in self.agents.items():
            if random.random() > JOIN_INSTITUTION_THRESHOLD:
                # Join institution with probability p
                institution = agent[1].choose_institution_to_join(self.institutions)
                if not institution: # Skips if the agent didnt find any valid institutions to join
                    continue
                self.institutions[institution].add_member(agent[0]) # Adds the agent id to the institution

                # Evaluates the institutions the agent is a member of, and leaves if under threshold
                if hasattr(self.agents[agent[0]], 'evaluate_institutions'):
                    agent[1].evaluate_institutions()
        
        # Dinner groups are formed based on agents choice
        self.games = {}
        for agent in self.agents.items():
            chosen_institution_id = agent[1].choose_dinner_group() # Agent decides which institution to join
            if chosen_institution_id not in self.games:
                self.games[chosen_institution_id] = []  # Initialize list if not already present

            self.games[chosen_institution_id].append(agent[1].agent_id)  # Append agent to the chosen institution's list

        choices = {}
        for agent in self.agents.items():
            chosen_institution_id = agent[1].choose_dinner_group()
            choices[agent[0]] = agent[1].decide(chosen_institution_id)

        print("Agents have made their choices.")

        for dinner_group in self.games.items():
            # Initialize dictionary to store choices for this group

            groups_choices = {}
            institution_id = dinner_group[0]
            agents_in_group = dinner_group[1]
            
            # Iterate over choices to build choices for this specific dinner group
            for agent_id, choice in choices.items():
                if agent_id in agents_in_group:  # Ensure the agent is in the current dinner group
                    groups_choices[agent_id] = choice

            # Calculate the total bill for the dinner group
            bill_total = self.create_bill(groups_choices)

            # Calculate the cost each agent must bear
            if len(agents_in_group) > 0:  # Ensure division by zero does not occur
                individually_spent = bill_total / len(agents_in_group)
            else:
                individually_spent = 0

            print(f"Agents in institution {dinner_group[0]} have decided what to eat and the bill is {bill_total}.")
            print(f"Each agent must pay {individually_spent}.")
                
            for agent_id in agents_in_group:
                self.agents[agent_id].calculate_utility(groups_choices[agent_id], individually_spent)

            print(f"Agents in institution {dinner_group[0]} have dined and calculated their utility.")

            events = self.institutions[dinner_group[0]].update_institution(groups_choices) # Applies institution rules and sanctions
            self.institutions[dinner_group[0]].last_orders = groups_choices # Choices are saved to be processes by agent before next round
            
            # Update institutional reputation based on the events
            if events:
                for event in events:
                    if event.type == "Cooperated" or event.type == "Not Cooperated":
                        self.reputation_sources['institutional_reputation'].report_rule_compliance(dinner_group, event)
                
        print("Institutions have been updated.")
        for institution in self.institutions.values():
            institution.print_events()


    def create_bill(self, choices):
        bill_choices = {"expensive": 0, "inexpensive": 0}
        for choice in choices.items():
            meal_type = choice[1]
            bill_choices[meal_type] += 1

        bill_total = bill_choices["expensive"] * EXPENSIVE_PRICE + bill_choices["inexpensive"] * INEXPENSIVE_PRICE

        return bill_total
            

    

