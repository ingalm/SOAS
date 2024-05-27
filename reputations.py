# Agents reputation class
# Not aggregated over time, but used to update trustworthiness
class AgentsReputation():
    def __init__(self):
        self.records = {}  # Stores feedback for each agent
    
    def report_meal_success(self, agent_id, success):
        """Agents report whether their meal was successful with agent(agent_id) based on cost and price paid."""

        if agent_id not in self.records:
            self.records[agent_id] = {'success_count': 0, 'total_meals': 0}
        
        self.records[agent_id]['total_meals'] += 1
        
        if success:
            self.records[agent_id]['success_count'] += 1

        # Records now contain how many agents had a successful meal with agent x and how many meals they had in total
    
    # Calculate the reputation of an agent, sent to the SCF
    def get_reputation(self, agent_id):
        """Calculate the percentage of successful meals for an agent."""
        records = self.records.get(agent_id, {'success_count': 0, 'total_meals': 0})
        if records['total_meals'] == 0:
            return 0
        return (records['success_count'] / records['total_meals']) * 100
        

# Institutional reputation class
# Reputation is aggregated over time
class InstitutionalReputation():
    def __init__(self):
        self.records = {}  # Stores rule following data for each institution

    def report_rule_compliance(self, institution_id, event):
        """Institutions report whether agents followed rules during a meal."""
        if institution_id not in self.records:
            self.records[institution_id] = {'compliance_count': 0, 'total_reports': 0}
        
        self.records[institution_id]['total_reports'] += 1
        if event.type == "Cooperated":
            self.records[institution_id]['compliance_count'] += 1

    def get_reputation(self, institution_id):
        """Calculate the percentage of times rules were followed in an institution."""
        records = self.records.get(institution_id, {'compliance_count': 0, 'total_reports': 0})
        if records['total_reports'] == 0:
            return 0
        return (records['compliance_count'] / records['total_reports']) * 100
