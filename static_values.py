# Chance for updating the reputation of an agent
# Simulates that not every action or event is known or made public. Simulates incomplete information
REPORT_REPUTATION_THRESHOLD = 0.7
COOPERATION_THRESHOLD = 0.5
LEAVE_INSTITUTION_THRESHOLD = 0.8
JOIN_INSTITUTION_THRESHOLD = 0.9
RULE_VIOLATION_THRESHOLD = 3 # Number of violations an agent can make before being expelled
EXPEL_FROM_INSTITUTION_THRESHOLD = 0.7 # The social capital of the agent must be lower than this value to be expelled
ADMIT_TO_INSTITUTION_THRESHOLD = 0.8  # The social capital of the agent must be higher than this value to be voted for admission

NUM_AGENTS = [20, 20, 20] # Social, Dominant, Random, Used during building the model
NUM_INSTITUTIONS = 9

AGENT_REPUTATION_WEIGHT = 0.3
INTITUTION_REPUTATION_WEIGHT = 0.3

DECISION_INDICATOR_WEIGHTS = {
    "agents_reputation": 0.3,
    "institutional_reputation": 0.3,
    "social_networks": 0.3,
    "institution": 0.1,
}

AGENT_EVENT_WEIGHTS = {
    "Cooperated": 0.3,
    "Not Cooperated": 0.6,
    }

INSTITUTION_EVENT_WEIGHTS = {
    "Joined": 0.1,
    "Left": 0.1,
    "Expelled": 0.3,
    "Sanctioned": 0.5,
    "Not Sanctioned": 0.5,
}



EXPENSIVE_PRICE = 3
INEXPENSIVE_PRICE = 1