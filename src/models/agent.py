from .base import Model


class Agent(Model):
    """Agent model representing an individual character controlled by a faction."""
    
    table_name = "agents"
    related_tables = []
    
    def __init__(self, id=None, name=None, faction_id=None, attunement=0, intellect=0, 
                 finesse=0, might=0, presence=0, created_at=None, updated_at=None):
        """Initialize a new Agent instance.
        
        Args:
            id (str, optional): Unique identifier. Defaults to None.
            name (str, optional): Agent name. Defaults to None.
            faction_id (str, optional): Owning faction ID. Defaults to None.
            attunement (int, optional): Attunement attribute (0-5). Defaults to 0.
            intellect (int, optional): Intellect attribute (0-5). Defaults to 0.
            finesse (int, optional): Finesse attribute (0-5). Defaults to 0.
            might (int, optional): Might attribute (0-5). Defaults to 0.
            presence (int, optional): Presence attribute (0-5). Defaults to 0.
            created_at (str, optional): Creation timestamp. Defaults to None.
            updated_at (str, optional): Last update timestamp. Defaults to None.
        """
        super().__init__(id, created_at, updated_at)
        self.name = name
        self.faction_id = faction_id
        
        # Primary attributes
        self.attunement = attunement
        self.intellect = intellect
        self.finesse = finesse
        self.might = might
        self.presence = presence
        
        # Skills (0-5 each)
        self.infiltration = 0
        self.persuasion = 0
        self.combat = 0
        self.streetwise = 0
        self.survival = 0
        self.artifice = 0
        self.arcana = 0
        
        # Current assignment
        self.district_id = None
        self.current_task = None
    
    def validate(self):
        """Validate agent data.
        
        Returns:
            bool: True if validation passes, False otherwise.
        """
        self.errors = []
        
        if not self.name:
            self.errors.append("Agent name is required")
        
        # Validate attribute ranges
        for attr in ["attunement", "intellect", "finesse", "might", "presence"]:
            value = getattr(self, attr)
            if not 0 <= value <= 5:
                self.errors.append(f"{attr.capitalize()} must be between 0 and 5")
        
        # Validate skill ranges
        for skill in ["infiltration", "persuasion", "combat", "streetwise", 
                      "survival", "artifice", "arcana"]:
            value = getattr(self, skill)
            if not 0 <= value <= 5:
                self.errors.append(f"{skill.capitalize()} must be between 0 and 5")
        
        return len(self.errors) == 0
    
    def get_attribute(self, attribute_name):
        """Get the value of a specific attribute.
        
        Args:
            attribute_name (str): The attribute name.
            
        Returns:
            int: The attribute value, or 0 if invalid name.
        """
        if attribute_name in ["attunement", "intellect", "finesse", "might", "presence"]:
            return getattr(self, attribute_name)
        return 0
    
    def get_skill(self, skill_name):
        """Get the value of a specific skill.
        
        Args:
            skill_name (str): The skill name.
            
        Returns:
            int: The skill value, or 0 if invalid name.
        """
        if skill_name in ["infiltration", "persuasion", "combat", "streetwise", 
                          "survival", "artifice", "arcana"]:
            return getattr(self, skill_name)
        return 0
    
    def assign_task(self, district_id, task_type, target_faction=None, 
                    attribute=None, skill=None, dc=None, monitoring=True):
        """Assign a task to this agent.
        
        Args:
            district_id (str): The district ID to assign to.
            task_type (str): Type of task (monitor, gain_influence, etc.).
            target_faction (str, optional): Target faction ID. Defaults to None.
            attribute (str, optional): Primary attribute to use. Defaults to None.
            skill (str, optional): Primary skill to use. Defaults to None.
            dc (int, optional): Difficulty class for the task. Defaults to None.
            monitoring (bool, optional): If the agent performs monitoring. Defaults to True.
            
        Returns:
            bool: True if successful.
        """
        self.district_id = district_id
        self.current_task = {
            "type": task_type,
            "target_faction": target_faction,
            "attribute": attribute,
            "skill": skill,
            "dc": dc,
            "performs_monitoring": monitoring
        }
        return True
    
    def clear_task(self):
        """Clear the agent's current task.
        
        Returns:
            bool: True if successful.
        """
        self.district_id = None
        self.current_task = None
        return True