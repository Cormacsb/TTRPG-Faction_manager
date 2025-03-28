from .base import Model


class District(Model):
    """District model representing a geographical area in the game."""
    
    table_name = "districts"
    related_tables = ["district_influence", "district_likeability", "district_rumors", 
                      "district_adjacency", "district_modifiers", "district_shapes"]
    
    def __init__(self, id=None, name=None, description=None, commerce_value=0, 
                 muster_value=0, aristocratic_value=0, created_at=None, updated_at=None):
        """Initialize a new District instance.
        
        Args:
            id (str, optional): Unique identifier. Defaults to None.
            name (str, optional): District name. Defaults to None.
            description (str, optional): District description. Defaults to None.
            commerce_value (int, optional): Economic value. Defaults to 0.
            muster_value (int, optional): Military value. Defaults to 0.
            aristocratic_value (int, optional): Political value. Defaults to 0.
            created_at (str, optional): Creation timestamp. Defaults to None.
            updated_at (str, optional): Last update timestamp. Defaults to None.
        """
        super().__init__(id, created_at, updated_at)
        self.name = name
        self.description = description
        self.commerce_value = commerce_value
        self.muster_value = muster_value
        self.aristocratic_value = aristocratic_value
        
        # District attributes for preferred actions
        self.preferred_gain_attribute = "presence"  # Default values
        self.preferred_gain_skill = "persuasion"
        self.preferred_gain_squadron_aptitude = "social"
        self.preferred_monitor_attribute = "intellect"
        self.preferred_monitor_skill = "streetwise"
        self.preferred_monitor_squadron_aptitude = "monitoring"
        
        # Relationships to other models (loaded separately)
        self.faction_influence = {}  # {faction_id: influence_value}
        self.influence_pool = 10  # Default available influence
        self.faction_likeability = {}  # {faction_id: likeability_value}
        self.weekly_dc_modifier = 0
        self.weekly_dc_modifier_history = []
        self.adjacent_districts = []
        self.strongholds = {}  # {faction_id: boolean}
        self.coordinates = {"x": 0, "y": 0}
        self.shape_data = None
        self.information = []  # List of rumor objects
    
    def validate(self):
        """Validate district data.
        
        Returns:
            bool: True if validation passes, False otherwise.
        """
        self.errors = []
        
        if not self.name:
            self.errors.append("District name is required")
        
        # Validate value ranges
        if not 0 <= self.commerce_value <= 10:
            self.errors.append("Commerce value must be between 0 and 10")
            
        if not 0 <= self.muster_value <= 10:
            self.errors.append("Muster value must be between 0 and 10")
            
        if not 0 <= self.aristocratic_value <= 10:
            self.errors.append("Aristocratic value must be between 0 and 10")
        
        # Validate influence total
        total_influence = sum(self.faction_influence.values())
        if total_influence > 10:
            self.errors.append("Total influence cannot exceed 10")
            
        # Calculate influence pool
        self.influence_pool = 10 - total_influence
        
        return len(self.errors) == 0
    
    def to_dict(self):
        """Convert district to dictionary.
        
        Returns:
            dict: Dictionary representation of the district.
        """
        district_dict = super().to_dict()
        return district_dict
    
    def calculate_total_influence(self):
        """Calculate the total influence in this district.
        
        Returns:
            int: The sum of all faction influence values.
        """
        return sum(self.faction_influence.values())
    
    def get_faction_influence(self, faction_id):
        """Get a faction's influence in this district.
        
        Args:
            faction_id (str): The faction ID to check.
            
        Returns:
            int: The faction's influence value, or 0 if none.
        """
        return self.faction_influence.get(faction_id, 0)
    
    def set_faction_influence(self, faction_id, value):
        """Set a faction's influence in this district.
        
        Args:
            faction_id (str): The faction ID.
            value (int): The influence value to set.
            
        Returns:
            bool: True if successful, False if would exceed 10 total.
        """
        # Calculate what total would be with this change
        current = self.get_faction_influence(faction_id)
        other_total = self.calculate_total_influence() - current
        
        if other_total + value > 10:
            return False
        
        if value <= 0:
            if faction_id in self.faction_influence:
                del self.faction_influence[faction_id]
            else:
                return True  # Nothing to delete
        else:
            self.faction_influence[faction_id] = value
            
        # Update the influence pool
        self.influence_pool = 10 - self.calculate_total_influence()
        return True
    
    def get_faction_likeability(self, faction_id):
        """Get a faction's likeability in this district.
        
        Args:
            faction_id (str): The faction ID to check.
            
        Returns:
            int: The faction's likeability value, or 0 if none.
        """
        return self.faction_likeability.get(faction_id, 0)
    
    def set_faction_likeability(self, faction_id, value):
        """Set a faction's likeability in this district.
        
        Args:
            faction_id (str): The faction ID.
            value (int): The likeability value to set (-5 to 5).
            
        Returns:
            bool: True if successful, False otherwise.
        """
        if not -5 <= value <= 5:
            return False
            
        self.faction_likeability[faction_id] = value
        return True
    
    def has_stronghold(self, faction_id):
        """Check if a faction has a stronghold in this district.
        
        Args:
            faction_id (str): The faction ID to check.
            
        Returns:
            bool: True if faction has a stronghold, False otherwise.
        """
        return self.strongholds.get(faction_id, False)
    
    def set_stronghold(self, faction_id, value):
        """Set a faction's stronghold status in this district.
        
        Args:
            faction_id (str): The faction ID.
            value (bool): True to set stronghold, False to remove.
            
        Returns:
            bool: True if successful.
        """
        self.strongholds[faction_id] = value
        return True
    
    def is_adjacent_to(self, district_id):
        """Check if this district is adjacent to another district.
        
        Args:
            district_id (str): The district ID to check.
            
        Returns:
            bool: True if districts are adjacent, False otherwise.
        """
        return district_id in self.adjacent_districts
    
    def add_adjacent_district(self, district_id):
        """Add an adjacent district.
        
        Args:
            district_id (str): The adjacent district ID.
            
        Returns:
            bool: True if successful, False if already adjacent.
        """
        if district_id not in self.adjacent_districts:
            self.adjacent_districts.append(district_id)
            return True
        return False
    
    def remove_adjacent_district(self, district_id):
        """Remove an adjacent district.
        
        Args:
            district_id (str): The adjacent district ID.
            
        Returns:
            bool: True if successful, False if not adjacent.
        """
        if district_id in self.adjacent_districts:
            self.adjacent_districts.remove(district_id)
            return True
        return False