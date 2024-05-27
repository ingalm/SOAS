
class Event():
    def __init__(self, type, weight, agent_id):
        self.type = type
        self.weight = weight
        self.agent_id = agent_id

class ReputationEvent(Event):
    def __init__(self, type, weight, agent_id, value):
        super().__init__(type, weight, agent_id)
        self.value = value

class SocialNetworkEvent(Event):
    def __init__(self, type, weight, agent_id, agent2):
        super().__init__(type, weight, agent_id)
        self.agent2 = agent2

class InstitutionEvent(Event):
    def __init__(self, type, weight, agent_id, institution_id):
        super().__init__(type, weight, agent_id)
        self.institution_id = institution_id