from .base import Model


class Squadron(Model):
    """Squadron model representing a group controlled by a faction."""
    
    table_name = "squadrons"
    related_tables = []
    
    def __init__(self, id=None, name=None, faction_id=None, mobility=0,
                 created_at=None, updated_at=None):
        """Initialize a new Squadron instance.
        
        Args:
            id (str, optional): Unique identifier. Defaults to None.
            name (str, optional): Squadron name. Defaults to None.
            faction_id (str, optional): Owning faction ID. Defaults to None.
            mobility (int, optional): Mobility rating (0-5). Defaults to 0.
            created_at (str, optional): Creation timestamp. Defaults to None.
            updated_at (str, optional): Last update timestamp. Defaults to None.
        """
        super().__init__(id, created_at, updated_at)
        self.name = name
        self.faction_id = faction_id
        self.mobility = mobility
        
        # Squadron type
        self.type = "general"
        
        # Aptitudes (-3 to +5, default -1)
        self.combat_aptitude = -1
        self.underworld_aptitude = -1
        self.social_aptitude = -1
        self.technical_aptitude = -1
        self.labor_aptitude = -1
        self.arcane_aptitude = -1
        self.wilderness_aptitude = -1
        self.monitoring_aptitude = -1
        
        # Current assignment
        self.district_id = None
        self.current_task = None
    
    def validate(self):
        """Validate squadron data.
        
        Returns:
            bool: True if validation passes, False otherwise.
        """
        self.errors = []
        
        if not self.name:
            self.errors.append("Squadron name is required")
        
        if not self.type:
            self.errors.append("Squadron type is required")
        
        # Validate mobility range
        if not 0 <= self.mobility <= 5:
            self.errors.append("Mobility must be between 0 and 5")
        
        # Validate aptitude ranges
        aptitudes = ["combat_aptitude", "underworld_aptitude", "social_aptitude",
                     "technical_aptitude", "labor_aptitude", "arcane_aptitude",
                     "wilderness_aptitude", "monitoring_aptitude"]
                     
        for aptitude in aptitudes:
            value = getattr(self, aptitude)
            if not -3 <= value <= 5:
                self.errors.append(f"{aptitude.replace('_', ' ').capitalize()} must be between -3 and 5")
        
        return len(self.errors) == 0
    
    def get_aptitude(self, aptitude_name):
        """Get the value of a specific aptitude.
        
        Args:
            aptitude_name (str): The aptitude name.
            
        Returns:
            int: The aptitude value, or -1 if invalid name.
        """
        attribute_name = f"{aptitude_name}_aptitude"
        if hasattr(self, attribute_name):
            return getattr(self, attribute_name)
        return -1
    
    def assign_task(self, district_id, task_type, target_faction=None, 
                    primary_aptitude=None, dc=None, monitoring=True):
        """Assign a task to this squadron.
        
        Args:
            district_id (str): The district ID to assign to.
            task_type (str): Type of task (monitor, gain_influence, etc.).
            target_faction (str, optional): Target faction ID. Defaults to None.
            primary_aptitude (str, optional): Primary aptitude to use. Defaults to None.
            dc (int, optional): Difficulty class for the task. Defaults to None.
            monitoring (bool, optional): If the squadron performs monitoring. Defaults to True.
            
        Returns:
            bool: True if successful.
        """
        self.district_id = district_id
        self.current_task = {
            "type": task_type,
            "target_faction": target_faction,
            "primary_aptitude": primary_aptitude,
            "dc": dc,
            "performs_monitoring": monitoring
        }
        return True
    
    def clear_task(self):
        """Clear the squadron's current task.
        
        Returns:
            bool: True if successful.
        """
        self.district_id = None
        self.current_task = None
        return True
    
    def can_affect_adjacent_district(self):
        """Check if squadron can affect adjacent districts.
        
        Returns:
            bool: True if mobility >= 2, False otherwise.
        """
        return self.mobility >= 2
    
    def get_max_targets(self):
        """Get maximum number of targets squadron can affect.
        
        Returns:
            dict: Dictionary with keys 'same_district' and 'adjacent_district'.
        """
        result = {
            'same_district': 0,
            'adjacent_district': 0
        }
        
        if self.mobility == 0:
            return result
        elif self.mobility == 1:
            result['same_district'] = 1
        elif self.mobility == 2:
            result['same_district'] = 1
            result['adjacent_district'] = 1  # Either same or adjacent, not both
        elif self.mobility == 3:
            result['same_district'] = 1
            result['adjacent_district'] = 1
        elif self.mobility == 4:
            result['same_district'] = 2
            result['adjacent_district'] = 2  # Total of 2 targets in either location
        elif self.mobility == 5:
            result['same_district'] = 1
            result['adjacent_district'] = 2
            
        return result