import logging
import json
import uuid
from datetime import datetime

from .base import Repository
from ...models.faction import Faction


class FactionRepository(Repository):
    """Repository for Faction model operations."""
    
    def __init__(self, db_manager):
        """Initialize the repository.
        
        Args:
            db_manager: Database manager instance.
        """
        super().__init__(db_manager, Faction)
    
    def find_by_id(self, id):
        """Find a faction by its ID.
        
        Args:
            id (str): Faction ID to find.
            
        Returns:
            Faction: Faction instance if found, None otherwise.
        """
        faction = super().find_by_id(id)
        if faction:
            self._load_related_data(faction)
        return faction
    
    def find_all(self):
        """Find all factions.
        
        Returns:
            list: List of Faction instances.
        """
        factions = super().find_all()
        for faction in factions:
            self._load_related_data(faction)
        return factions
    
    def _load_related_data(self, faction):
        """Load related data for a faction.
        
        Args:
            faction (Faction): Faction instance to load data for.
        """
        try:
            # Load relationships
            query = """
                SELECT target_faction_id, relationship_value
                FROM faction_relationships
                WHERE faction_id = :faction_id
            """
            results = self.db_manager.execute_query(query, {"faction_id": faction.id})
            
            faction.relationships = {}
            
            for row in results:
                faction.relationships[row['target_faction_id']] = row['relationship_value']
            
            # Load resources
            query = """
                SELECT resource_type, resource_value
                FROM faction_resources
                WHERE faction_id = :faction_id
            """
            results = self.db_manager.execute_query(query, {"faction_id": faction.id})
            
            faction.resources = {}
            
            for row in results:
                faction.resources[row['resource_type']] = row['resource_value']
            
            # Load known rumors
            query = """
                SELECT rumor_id
                FROM faction_known_rumors
                WHERE faction_id = :faction_id
            """
            results = self.db_manager.execute_query(query, {"faction_id": faction.id})
            
            faction.known_information = [row['rumor_id'] for row in results]
            
        except Exception as e:
            logging.error(f"Error loading related data for faction {faction.id}: {str(e)}")
    
    def create(self, faction):
        """Create a new faction in the database.
        
        Args:
            faction (Faction): Faction instance to create.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Begin transaction using context manager
            with self.db_manager.connection:
                # Save main faction record
                main_data = {
                    'id': faction.id,
                    'name': faction.name,
                    'description': faction.description,
                    'color': faction.color,
                    'monitoring_bonus': faction.monitoring_bonus,
                    'created_at': faction.created_at,
                    'updated_at': faction.updated_at
                }
                
                query = """
                    INSERT INTO factions (
                        id, name, description, color, monitoring_bonus,
                        created_at, updated_at
                    )
                    VALUES (
                        :id, :name, :description, :color, :monitoring_bonus,
                        :created_at, :updated_at
                    )
                """
                
                self.db_manager.execute_update(query, main_data)
                
                # Save relationships
                for target_id, value in faction.relationships.items():
                    query = """
                        INSERT INTO faction_relationships (
                            faction_id, target_faction_id, relationship_value,
                            created_at, updated_at
                        )
                        VALUES (
                            :faction_id, :target_faction_id, :relationship_value,
                            :created_at, :updated_at
                        )
                    """
                    
                    params = {
                        'faction_id': faction.id,
                        'target_faction_id': target_id,
                        'relationship_value': value,
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }
                    
                    self.db_manager.execute_update(query, params)
                
                # Save resources
                for resource_type, value in faction.resources.items():
                    query = """
                        INSERT INTO faction_resources (
                            faction_id, resource_type, resource_value,
                            created_at, updated_at
                        )
                        VALUES (
                            :faction_id, :resource_type, :resource_value,
                            :created_at, :updated_at
                        )
                    """
                    
                    params = {
                        'faction_id': faction.id,
                        'resource_type': resource_type,
                        'resource_value': value,
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }
                    
                    self.db_manager.execute_update(query, params)
                
                # Save known rumors
                for rumor_id in faction.known_information:
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
                        'faction_id': faction.id,
                        'rumor_id': rumor_id,
                        'discovered_on': datetime.now().isoformat(),
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }
                    
                    self.db_manager.execute_update(query, params)
                
            return True
        except Exception as e:
            logging.error(f"Error creating faction: {str(e)}")
            return False
    
    def update(self, faction):
        """Update an existing faction in the database.
        
        Args:
            faction (Faction): Faction instance to update.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Begin transaction using context manager
            with self.db_manager.connection:
                # Update main faction record
                main_data = {
                    'id': faction.id,
                    'name': faction.name,
                    'description': faction.description,
                    'color': faction.color,
                    'monitoring_bonus': faction.monitoring_bonus,
                    'updated_at': datetime.now().isoformat()
                }
                
                query = """
                    UPDATE factions SET
                        name = :name,
                        description = :description,
                        color = :color,
                        monitoring_bonus = :monitoring_bonus,
                        updated_at = :updated_at
                    WHERE id = :id
                """
                
                self.db_manager.execute_update(query, main_data)
                
                # Update relationships (delete existing and re-insert)
                self.db_manager.execute_update(
                    "DELETE FROM faction_relationships WHERE faction_id = :faction_id",
                    {"faction_id": faction.id}
                )
                
                for target_id, value in faction.relationships.items():
                    query = """
                        INSERT INTO faction_relationships (
                            faction_id, target_faction_id, relationship_value,
                            created_at, updated_at
                        )
                        VALUES (
                            :faction_id, :target_faction_id, :relationship_value,
                            :created_at, :updated_at
                        )
                    """
                    
                    params = {
                        'faction_id': faction.id,
                        'target_faction_id': target_id,
                        'relationship_value': value,
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }
                    
                    self.db_manager.execute_update(query, params)
                
                # Update resources (delete existing and re-insert)
                self.db_manager.execute_update(
                    "DELETE FROM faction_resources WHERE faction_id = :faction_id",
                    {"faction_id": faction.id}
                )
                
                for resource_type, value in faction.resources.items():
                    query = """
                        INSERT INTO faction_resources (
                            faction_id, resource_type, resource_value,
                            created_at, updated_at
                        )
                        VALUES (
                            :faction_id, :resource_type, :resource_value,
                            :created_at, :updated_at
                        )
                    """
                    
                    params = {
                        'faction_id': faction.id,
                        'resource_type': resource_type,
                        'resource_value': value,
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }
                    
                    self.db_manager.execute_update(query, params)
                
                # Update known rumors (delete existing and re-insert)
                self.db_manager.execute_update(
                    "DELETE FROM faction_known_rumors WHERE faction_id = :faction_id",
                    {"faction_id": faction.id}
                )
                
                for rumor_id in faction.known_information:
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
                        'faction_id': faction.id,
                        'rumor_id': rumor_id,
                        'discovered_on': datetime.now().isoformat(),
                        'created_at': datetime.now().isoformat(),
                        'updated_at': datetime.now().isoformat()
                    }
                    
                    self.db_manager.execute_update(query, params)
                
            return True
        except Exception as e:
            logging.error(f"Error updating faction: {str(e)}")
            return False
    
    def set_relationship(self, faction_id, target_faction_id, value):
        """Set relationship between two factions.
        
        Args:
            faction_id (str): Faction ID.
            target_faction_id (str): Target faction ID.
            value (int): Relationship value (-2 to +2).
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            if not -2 <= value <= 2:
                logging.error(f"Invalid relationship value: {value} (must be between -2 and 2)")
                return False
                
            faction = self.find_by_id(faction_id)
            if not faction:
                logging.error(f"Cannot set relationship: faction {faction_id} not found")
                return False
                
            target_faction = self.find_by_id(target_faction_id)
            if not target_faction:
                logging.error(f"Cannot set relationship: target faction {target_faction_id} not found")
                return False
                
            if faction_id == target_faction_id:
                logging.error(f"Cannot set relationship with self: {faction_id}")
                return False  # Can't set relationship with self
                
            logging.info(f"Setting relationship: {faction.name} (ID: {faction_id}) → {target_faction.name} (ID: {target_faction_id}) = {value}")
            
            with self.db_manager.connection:
                # Check if record exists
                exists = self.db_manager.execute_query(
                    """
                    SELECT 1 FROM faction_relationships
                    WHERE faction_id = :faction_id AND target_faction_id = :target_faction_id
                    """,
                    {"faction_id": faction_id, "target_faction_id": target_faction_id}
                )
                
                if exists:
                    # Update existing record
                    logging.info(f"Updating existing relationship record for {faction.name} → {target_faction.name}")
                    self.db_manager.execute_update(
                        """
                        UPDATE faction_relationships SET
                            relationship_value = :value,
                            updated_at = :updated_at
                        WHERE faction_id = :faction_id AND target_faction_id = :target_faction_id
                        """,
                        {
                            "faction_id": faction_id,
                            "target_faction_id": target_faction_id,
                            "value": value,
                            "updated_at": datetime.now().isoformat()
                        }
                    )
                else:
                    # Insert new record
                    logging.info(f"Creating new relationship record for {faction.name} → {target_faction.name}")
                    self.db_manager.execute_update(
                        """
                        INSERT INTO faction_relationships (
                            faction_id, target_faction_id, relationship_value,
                            created_at, updated_at
                        )
                        VALUES (
                            :faction_id, :target_faction_id, :value,
                            :created_at, :updated_at
                        )
                        """,
                        {
                            "faction_id": faction_id,
                            "target_faction_id": target_faction_id,
                            "value": value,
                            "created_at": datetime.now().isoformat(),
                            "updated_at": datetime.now().isoformat()
                        }
                    )
                
                # Update faction model for consistency
                previous_value = faction.relationships.get(target_faction_id, None)
                faction.relationships[target_faction_id] = value
                logging.info(f"Updated in-memory faction model: {faction.name} relationship with {target_faction.name} from {previous_value} to {value}")
                
                # Check the updated model to verify
                logging.info(f"Verification - relationship after update: {faction.get_relationship(target_faction_id)}")
                
            return True
        except Exception as e:
            logging.error(f"Error setting faction relationship: {str(e)}")
            logging.exception("Full traceback for set_relationship error:")
            return False
    
    def set_resource(self, faction_id, resource_type, value):
        """Set a faction's resource value.
        
        Args:
            faction_id (str): Faction ID.
            resource_type (str): Resource type.
            value (int): Resource value.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            if value < 0:
                return False
                
            faction = self.find_by_id(faction_id)
            if not faction:
                return False
                
            with self.db_manager.connection:
                # Check if record exists
                exists = self.db_manager.execute_query(
                    """
                    SELECT 1 FROM faction_resources
                    WHERE faction_id = :faction_id AND resource_type = :resource_type
                    """,
                    {"faction_id": faction_id, "resource_type": resource_type}
                )
                
                if exists:
                    # Update existing record
                    self.db_manager.execute_update(
                        """
                        UPDATE faction_resources SET
                            resource_value = :value,
                            updated_at = :updated_at
                        WHERE faction_id = :faction_id AND resource_type = :resource_type
                        """,
                        {
                            "faction_id": faction_id,
                            "resource_type": resource_type,
                            "value": value,
                            "updated_at": datetime.now().isoformat()
                        }
                    )
                else:
                    # Insert new record
                    self.db_manager.execute_update(
                        """
                        INSERT INTO faction_resources (
                            faction_id, resource_type, resource_value,
                            created_at, updated_at
                        )
                        VALUES (
                            :faction_id, :resource_type, :value,
                            :created_at, :updated_at
                        )
                        """,
                        {
                            "faction_id": faction_id,
                            "resource_type": resource_type,
                            "value": value,
                            "created_at": datetime.now().isoformat(),
                            "updated_at": datetime.now().isoformat()
                        }
                    )
                
                # Update faction model for consistency
                faction.resources[resource_type] = value
                
            return True
        except Exception as e:
            logging.error(f"Error setting faction resource: {str(e)}")
            return False
    
    def learn_information(self, faction_id, rumor_id, turn_number=None):
        """Record that a faction has learned a piece of information.
        
        Args:
            faction_id (str): Faction ID.
            rumor_id (str): Rumor ID.
            turn_number (int, optional): Turn number when discovered. Defaults to None.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            faction = self.find_by_id(faction_id)
            if not faction:
                return False
                
            # Check if already known
            if rumor_id in faction.known_information:
                return True
                
            with self.db_manager.connection:
                # Insert new record
                self.db_manager.execute_update(
                    """
                    INSERT INTO faction_known_rumors (
                        faction_id, rumor_id, discovered_on,
                        created_at, updated_at
                    )
                    VALUES (
                        :faction_id, :rumor_id, :discovered_on,
                        :created_at, :updated_at
                    )
                    """,
                    {
                        "faction_id": faction_id,
                        "rumor_id": rumor_id,
                        "discovered_on": datetime.now().isoformat(),
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat()
                    }
                )
                
                # Update faction model for consistency
                faction.known_information.append(rumor_id)
                
            return True
        except Exception as e:
            logging.error(f"Error recording learned information: {str(e)}")
            return False
    
    def get_all_faction_ids(self):
        """Get all faction IDs in the system.
        
        Returns:
            list: List of faction IDs.
        """
        try:
            query = "SELECT id FROM factions"
            results = self.db_manager.execute_query(query)
            return [row["id"] for row in results]
        except Exception as e:
            logging.error(f"Error getting faction IDs: {str(e)}")
            return []