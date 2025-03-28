from .base import Model


class Rumor(Model):
    """Rumor model representing a discoverable piece of information in a district."""
    
    table_name = "district_rumors"
    related_tables = ["faction_known_rumors"]
    
    def __init__(self, id=None, district_id=None, rumor_text=None, discovery_dc=15,
                 is_discovered=False, created_at=None, updated_at=None):
        """Initialize a new Rumor instance.
        
        Args:
            id (str, optional): Unique identifier. Defaults to None.
            district_id (str, optional): District ID where rumor is located. Defaults to None.
            rumor_text (str, optional): Text content of the rumor. Defaults to None.
            discovery_dc (int, optional): Difficulty to discover. Defaults to 15.
            is_discovered (bool, optional): Whether rumor is globally discovered. Defaults to False.
            created_at (str, optional): Creation timestamp. Defaults to None.
            updated_at (str, optional): Last update timestamp. Defaults to None.
        """
        super().__init__(id, created_at, updated_at)
        self.district_id = district_id
        self.rumor_text = rumor_text
        self.discovery_dc = discovery_dc
        self.initial_dc = discovery_dc  # Store the initial DC for reference
        self.is_discovered = is_discovered
        
        # Additional properties
        self.newspaper_hint = ""
        self.newspaper_weight = 1.0  # Higher means more likely to appear in newspaper
        self.known_by = []  # List of faction IDs that know this rumor
        self.discovery_turn = {}  # {faction_id: turn_number}
    
    def validate(self):
        """Validate rumor data.
        
        Returns:
            bool: True if validation passes, False otherwise.
        """
        self.errors = []
        
        if not self.district_id:
            self.errors.append("District ID is required")
            
        if not self.rumor_text:
            self.errors.append("Rumor text is required")
            
        if self.discovery_dc < 1:
            self.errors.append("Discovery DC must be at least 1")
        
        return len(self.errors) == 0
    
    def is_known_by(self, faction_id):
        """Check if a faction knows this rumor.
        
        Args:
            faction_id (str): The faction ID to check.
            
        Returns:
            bool: True if faction knows this rumor, False otherwise.
        """
        return faction_id in self.known_by
    
    def mark_as_known(self, faction_id, turn_number):
        """Mark this rumor as known by a faction.
        
        Args:
            faction_id (str): The faction ID.
            turn_number (int): The current turn number.
            
        Returns:
            bool: True if successful, False if already known.
        """
        if faction_id not in self.known_by:
            self.known_by.append(faction_id)
            self.discovery_turn[faction_id] = turn_number
            return True
        return False
    
    def decrease_dc(self, amount=1):
        """Decrease the discovery DC.
        
        Args:
            amount (int, optional): Amount to decrease DC by. Defaults to 1.
            
        Returns:
            int: The new DC value.
        """
        self.discovery_dc = max(1, self.discovery_dc - amount)
        return self.discovery_dc