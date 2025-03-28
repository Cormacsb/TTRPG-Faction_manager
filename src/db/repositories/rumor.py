import logging
from datetime import datetime

from .base import Repository
from ...models.rumor import Rumor


class RumorRepository(Repository):
    """Repository for Rumor model operations."""
    
    def __init__(self, db_manager):
        """Initialize the repository.
        
        Args:
            db_manager: Database manager instance.
        """
        super().__init__(db_manager, Rumor)
    
    def find_by_district(self, district_id):
        """Find all rumors in a district.
        
        Args:
            district_id (str): District ID.
            
        Returns:
            list: List of Rumor instances.
        """
        try:
            query = "SELECT * FROM district_rumors WHERE district_id = :district_id"
            results = self.db_manager.execute_query(query, {"district_id": district_id})
            
            rumors = [self.model_class.from_dict(dict(row)) for row in results]
            
            # Load faction knowledge for each rumor
            for rumor in rumors:
                self._load_faction_knowledge(rumor)
                
            return rumors
        except Exception as e:
            logging.error(f"Error finding rumors for district {district_id}: {str(e)}")
            return []
    
    def find_by_id(self, id):
        """Find a rumor by its ID.
        
        Args:
            id (str): Rumor ID to find.
            
        Returns:
            Rumor: Rumor instance if found, None otherwise.
        """
        rumor = super().find_by_id(id)
        if rumor:
            self._load_faction_knowledge(rumor)
        return rumor
    
    def _load_faction_knowledge(self, rumor):
        """Load faction knowledge for a rumor.
        
        Args:
            rumor (Rumor): Rumor instance to load data for.
        """
        try:
            query = """
                SELECT faction_id, discovered_on
                FROM faction_known_rumors
                WHERE rumor_id = :rumor_id
            """
            results = self.db_manager.execute_query(query, {"rumor_id": rumor.id})
            
            rumor.known_by = []
            rumor.discovery_turn = {}
            
            for row in results:
                rumor.known_by.append(row['faction_id'])
                
                # Parse the ISO-format datetime to get the turn number
                # This is a simplified approach - in a real system, we might store the turn directly
                rumor.discovery_turn[row['faction_id']] = row['discovered_on']
                
        except Exception as e:
            logging.error(f"Error loading faction knowledge for rumor {rumor.id}: {str(e)}")
    
    def create(self, rumor):
        """Create a new rumor in the database.
        
        Args:
            rumor (Rumor): Rumor instance to create.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Validate the rumor
            if not rumor.validate():
                logging.error(f"Invalid rumor: {rumor.errors}")
                return False
                
            # Begin transaction using context manager
            with self.db_manager.connection:
                # Save main rumor record
                main_data = {
                    'id': rumor.id,
                    'district_id': rumor.district_id,
                    'rumor_text': rumor.rumor_text,
                    'discovery_dc': rumor.discovery_dc,
                    'is_discovered': rumor.is_discovered,
                    'created_at': rumor.created_at,
                    'updated_at': rumor.updated_at
                }
                
                query = """
                    INSERT INTO district_rumors (
                        id, district_id, rumor_text, discovery_dc, is_discovered,
                        created_at, updated_at
                    )
                    VALUES (
                        :id, :district_id, :rumor_text, :discovery_dc, :is_discovered,
                        :created_at, :updated_at
                    )
                """
                
                self.db_manager.execute_update(query, main_data)
                
                # Save faction knowledge
                for faction_id in rumor.known_by:
                    discovered_on = rumor.discovery_turn.get(faction_id, datetime.now().isoformat())
                    
                    query = """
                        INSERT INTO faction_known_rumors (
                            faction_id, rumor_id, discovered_on,
                            created_at, updated_at
                        )
                        VALUES (
                            :faction_id, :rumor_id, :discovered_on,
                            :created_at, :updated_at
                        )
                    """
                    
                    params = {
                        'faction_id': faction_id,
                        'rumor_id': rumor.id,
                        'discovered_on': discovered_on,
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }
                    
                    self.db_manager.execute_update(query, params)
                
            return True
        except Exception as e:
            logging.error(f"Error creating rumor: {str(e)}")
            return False
    
    def update(self, rumor):
        """Update an existing rumor in the database.
        
        Args:
            rumor (Rumor): Rumor instance to update.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Validate the rumor
            if not rumor.validate():
                logging.error(f"Invalid rumor: {rumor.errors}")
                return False
                
            # Begin transaction using context manager
            with self.db_manager.connection:
                # Update main rumor record
                main_data = {
                    'id': rumor.id,
                    'district_id': rumor.district_id,
                    'rumor_text': rumor.rumor_text,
                    'discovery_dc': rumor.discovery_dc,
                    'is_discovered': rumor.is_discovered,
                    'updated_at': datetime.now().isoformat()
                }
                
                query = """
                    UPDATE district_rumors SET
                        district_id = :district_id,
                        rumor_text = :rumor_text,
                        discovery_dc = :discovery_dc,
                        is_discovered = :is_discovered,
                        updated_at = :updated_at
                    WHERE id = :id
                """
                
                self.db_manager.execute_update(query, main_data)
                
                # Update faction knowledge (delete existing and re-insert)
                self.db_manager.execute_update(
                    "DELETE FROM faction_known_rumors WHERE rumor_id = :rumor_id",
                    {"rumor_id": rumor.id}
                )
                
                for faction_id in rumor.known_by:
                    discovered_on = rumor.discovery_turn.get(faction_id, datetime.now().isoformat())
                    
                    query = """
                        INSERT INTO faction_known_rumors (
                            faction_id, rumor_id, discovered_on,
                            created_at, updated_at
                        )
                        VALUES (
                            :faction_id, :rumor_id, :discovered_on,
                            :created_at, :updated_at
                        )
                    """
                    
                    params = {
                        'faction_id': faction_id,
                        'rumor_id': rumor.id,
                        'discovered_on': discovered_on,
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }
                    
                    self.db_manager.execute_update(query, params)
                
            return True
        except Exception as e:
            logging.error(f"Error updating rumor {rumor.id}: {str(e)}")
            return False
    
    def decrease_dc(self, rumor_id, amount=1):
        """Decrease the discovery DC for a rumor.
        
        Args:
            rumor_id (str): Rumor ID.
            amount (int, optional): Amount to decrease DC by. Defaults to 1.
            
        Returns:
            int: The new DC value, or None if operation failed.
        """
        try:
            rumor = self.find_by_id(rumor_id)
            if not rumor:
                return None
                
            # Calculate new DC, ensuring it doesn't go below 1
            new_dc = max(1, rumor.discovery_dc - amount)
            
            # Begin transaction using context manager
            with self.db_manager.connection:
                query = """
                    UPDATE district_rumors SET
                        discovery_dc = :discovery_dc,
                        updated_at = :updated_at
                    WHERE id = :id
                """
                
                data = {
                    'id': rumor_id,
                    'discovery_dc': new_dc,
                    'updated_at': datetime.now().isoformat()
                }
                
                result = self.db_manager.execute_update(query, data)
                
                if result <= 0:
                    return None
                    
                # Update rumor model for consistency
                rumor.discovery_dc = new_dc
                
            return new_dc
        except Exception as e:
            logging.error(f"Error decreasing DC for rumor {rumor_id}: {str(e)}")
            return None
    
    def mark_as_known(self, rumor_id, faction_id, turn_number=None):
        """Mark a rumor as known by a faction.
        
        Args:
            rumor_id (str): Rumor ID.
            faction_id (str): Faction ID.
            turn_number (int, optional): Turn number when discovered. Defaults to None.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            rumor = self.find_by_id(rumor_id)
            if not rumor:
                return False
                
            # Check if already known
            if faction_id in rumor.known_by:
                return True
                
            # Use current time if turn number not provided
            discovered_on = str(turn_number) if turn_number else datetime.now().isoformat()
            
            # Begin transaction using context manager
            with self.db_manager.connection:
                query = """
                    INSERT INTO faction_known_rumors (
                        faction_id, rumor_id, discovered_on,
                        created_at, updated_at
                    )
                    VALUES (
                        :faction_id, :rumor_id, :discovered_on,
                        :created_at, :updated_at
                    )
                """
                
                data = {
                    'faction_id': faction_id,
                    'rumor_id': rumor_id,
                    'discovered_on': discovered_on,
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                
                self.db_manager.execute_update(query, data)
                
                # Update rumor model for consistency
                rumor.known_by.append(faction_id)
                rumor.discovery_turn[faction_id] = discovered_on
                
            return True
        except Exception as e:
            logging.error(f"Error marking rumor {rumor_id} as known by faction {faction_id}: {str(e)}")
            return False