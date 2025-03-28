from .base import Model
import logging


class Faction(Model):
    """Faction model representing a player-controlled organization."""
    
    table_name = "factions"
    related_tables = ["faction_relationships", "district_influence", 
                      "district_likeability", "faction_resources", 
                      "agents", "squadrons", "faction_known_rumors"]
    
    def __init__(self, id=None, name=None, description=None, color="#3498db",
                 monitoring_bonus=0, created_at=None, updated_at=None):
        """Initialize a new Faction instance.
        
        Args:
            id (str, optional): Unique identifier. Defaults to None.
            name (str, optional): Faction name. Defaults to None.
            description (str, optional): Faction description. Defaults to None.
            color (str, optional): Hex color code for faction. Defaults to blue.
            monitoring_bonus (int, optional): Bonus to information gathering. Defaults to 0.
            created_at (str, optional): Creation timestamp. Defaults to None.
            updated_at (str, optional): Last update timestamp. Defaults to None.
        """
        super().__init__(id, created_at, updated_at)
        self.name = name
        self.description = description
        self.color = color
        self.monitoring_bonus = monitoring_bonus
        
        # Relationships to other models (loaded separately)
        self.relationships = {}  # {faction_id: relationship_value}
        self.resources = {}  # {resource_type: resource_value}
        self.modifiers = []  # List of modifier objects
        self.known_information = []  # List of known rumor IDs
        
        # Perception data
        self.perceived_influence = {}  # {district_id: {faction_id: {value: int, last_updated: int}}}
        self.perceived_strongholds = {}  # {district_id: {faction_id: {has_stronghold: bool, last_updated: int}}}
        self.district_history = {}  # {district_id: {last_detected_turn: int, historical_presence: bool}}
    
    def validate(self):
        """Validate faction data.
        
        Returns:
            bool: True if validation passes, False otherwise.
        """
        self.errors = []
        
        if not self.name:
            self.errors.append("Faction name is required")
        
        # Validate color is a valid hex code
        if not self.color.startswith('#') or len(self.color) != 7:
            self.errors.append("Color must be a valid hex code (e.g. #3498db)")
        
        return len(self.errors) == 0
    
    def get_relationship(self, faction_id):
        """Get relationship value with another faction.
        
        Args:
            faction_id (str): The faction ID to check.
            
        Returns:
            int: Relationship value (-2 to +2), or 0 if not set.
        """
        relationship_value = self.relationships.get(faction_id, 0)
        logging.info(f"Faction {self.name} (ID: {self.id}) has relationship {relationship_value} with faction ID {faction_id}")
        logging.debug(f"All relationships for {self.name}: {self.relationships}")
        return relationship_value
    
    def set_relationship(self, faction_id, value):
        """Set relationship value with another faction.
        
        Args:
            faction_id (str): The faction ID.
            value (int): The relationship value to set (-2 to +2).
            
        Returns:
            bool: True if successful, False otherwise.
        """
        if not -2 <= value <= 2:
            return False
            
        self.relationships[faction_id] = value
        return True
    
    def get_resource(self, resource_type):
        """Get a resource value.
        
        Args:
            resource_type (str): The resource type to check.
            
        Returns:
            int: Resource value, or 0 if not set.
        """
        return self.resources.get(resource_type, 0)
    
    def set_resource(self, resource_type, value):
        """Set a resource value.
        
        Args:
            resource_type (str): The resource type.
            value (int): The resource value to set.
            
        Returns:
            bool: True if successful, False if negative value.
        """
        if value < 0:
            return False
            
        self.resources[resource_type] = value
        return True
    
    def add_modifier(self, name, modifier_type, value):
        """Add a faction modifier.
        
        Args:
            name (str): Modifier name.
            modifier_type (str): Type of modifier (e.g., "commerce", "muster").
            value (int): Modifier value.
            
        Returns:
            dict: The created modifier.
        """
        modifier = {
            "id": str(len(self.modifiers) + 1),
            "name": name,
            "type": modifier_type,
            "value": value
        }
        self.modifiers.append(modifier)
        return modifier
    
    def remove_modifier(self, modifier_id):
        """Remove a faction modifier.
        
        Args:
            modifier_id (str): The modifier ID to remove.
            
        Returns:
            bool: True if successful, False if not found.
        """
        for i, modifier in enumerate(self.modifiers):
            if modifier["id"] == modifier_id:
                self.modifiers.pop(i)
                return True
        return False
    
    def knows_information(self, information_id):
        """Check if faction knows a specific piece of information.
        
        Args:
            information_id (str): The information ID to check.
            
        Returns:
            bool: True if faction knows the information, False otherwise.
        """
        return information_id in self.known_information
    
    def learn_information(self, information_id):
        """Add information to faction's known information.
        
        Args:
            information_id (str): The information ID to learn.
            
        Returns:
            bool: True if successful, False if already known.
        """
        if information_id not in self.known_information:
            self.known_information.append(information_id)
            return True
        return False
    
    def get_perceived_influence(self, district_id, faction_id):
        """Get a faction's perceived influence in a district.
        
        Args:
            district_id (str): The district ID to check.
            faction_id (str): The faction ID to check.
            
        Returns:
            dict: Dict with value and last_updated, or None if unknown.
        """
        if district_id in self.perceived_influence:
            return self.perceived_influence[district_id].get(faction_id)
        return None
    
    def set_perceived_influence(self, district_id, faction_id, value, turn_number):
        """Set a faction's perceived influence in a district.
        
        Args:
            district_id (str): The district ID.
            faction_id (str): The faction ID.
            value (int): The perceived influence value.
            turn_number (int): The current turn number.
            
        Returns:
            bool: True if successful.
        """
        if district_id not in self.perceived_influence:
            self.perceived_influence[district_id] = {}
            
        self.perceived_influence[district_id][faction_id] = {
            "value": value,
            "last_updated": turn_number
        }
        
        # Update district history
        if district_id not in self.district_history:
            self.district_history[district_id] = {
                "last_detected_turn": turn_number,
                "historical_presence": True
            }
        else:
            self.district_history[district_id]["last_detected_turn"] = turn_number
            self.district_history[district_id]["historical_presence"] = True
            
        return True
    
    def get_perceived_stronghold(self, district_id, faction_id):
        """Get a faction's perceived stronghold status in a district.
        
        Args:
            district_id (str): The district ID to check.
            faction_id (str): The faction ID to check.
            
        Returns:
            dict: Dict with has_stronghold and last_updated, or None if unknown.
        """
        if district_id in self.perceived_strongholds:
            return self.perceived_strongholds[district_id].get(faction_id)
        return None
    
    def set_perceived_stronghold(self, district_id, faction_id, has_stronghold, turn_number):
        """Set a faction's perceived stronghold status in a district.
        
        Args:
            district_id (str): The district ID.
            faction_id (str): The faction ID.
            has_stronghold (bool): Whether the faction has a stronghold.
            turn_number (int): The current turn number.
            
        Returns:
            bool: True if successful.
        """
        if district_id not in self.perceived_strongholds:
            self.perceived_strongholds[district_id] = {}
            
        self.perceived_strongholds[district_id][faction_id] = {
            "has_stronghold": has_stronghold,
            "last_updated": turn_number
        }
        
        # Update district history
        if district_id not in self.district_history:
            self.district_history[district_id] = {
                "last_detected_turn": turn_number,
                "historical_presence": True
            }
        else:
            self.district_history[district_id]["last_detected_turn"] = turn_number
            self.district_history[district_id]["historical_presence"] = True
            
        return True