from framework import SocialCapitalFramework
# Specific social capital framework for the UDD game
# Includes the metrics and update functions for the social capital framework
# Data structures are defined in the main simulation script

def create_complete_scf():
    # Defining and setting up the Social Capital Framework
    scf = SocialCapitalFramework()

    # Add data structures
    scf.add_data_structure('social_networks', {})
    scf.add_data_structure('trustworthiness', {})
    scf.add_data_structure('institutions', {})

    # Add update functions
    scf.add_update_function('social_networks', update_social_network)
    scf.add_update_function('trustworthiness', update_trustworthiness)
    scf.add_update_function('institutions', update_institutions)

    # Add metrics to evaluate the social capital
    scf.add_metric('social_networks', get_social_network_metrics)
    scf.add_metric('trustworthiness', get_trustworthiness_metrics)
    scf.add_metric('institutions', get_institutions_metrics)

    return scf

def update_trustworthiness(current_data, event):
    # Normalize the incoming reputation value

    normalized_value = max(0, min(event.value / 100, 1))
    
    # Check if there is existing data for this agent
    if event.agent_id in current_data:
        # Use a simple averaging method, you could choose other methods like exponential smoothing
        current_value = current_data[event.agent_id]
        # Assuming equal weight for simplicity, could be adjusted based on event weight or source
        updated_value = (current_value + normalized_value) / 2
    else:
        updated_value = normalized_value

    # Update the data structure
    current_data[event.agent_id] = updated_value
    return current_data

def update_social_network(current_data, event):
    agent1 = event.agent_id
    agent2 = event.agent2
    weight = event.weight
  
    # Get current score or default to 0
    current_score = current_data[agent1][agent2]
   
    # Check if the event is enhancing or diminishing cooperation
    if event.type == "Cooperated":
        new_score = current_score + weight * (1 - current_score)
    else:
        new_score = current_score * (1 - weight)
    
     # Update the score between agent1 and agent2
    current_data[agent1][agent2] = new_score
    current_data[agent2][agent1] = new_score

    return current_data

def update_institutions(current_data, event):
    current_score = current_data[event.institution_id]
    weight = event.weight

    cooperative_events = ["Join", "Expelled", "Sanctioned"]

    # Check if the event is enhancing or diminishing cooperation
    if event.type in cooperative_events:
        new_score = current_score + weight * (1 - current_score)
    else:
        new_score = current_score * (1 - weight)

    current_data[event.institution_id] = new_score

    return current_data

def get_institutions_metrics(scf, institution_id):
    return scf.data_structures["institutions"][institution_id]

def get_trustworthiness_metrics(scf, agent_id):
    trustworthiness = scf.data_structures["trustworthiness"][agent_id]
    return trustworthiness

def get_social_network_metrics(scf, agent_id):
    # Takes the graph saved in the data structure and calculates the average score of an agents connections
    social_network = scf.data_structures["social_networks"][agent_id]
    if not social_network:
        return 0

    return sum(social_network.values()) / len(social_network)

