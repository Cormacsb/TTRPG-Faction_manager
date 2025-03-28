import logging
import json
from datetime import datetime
import uuid

from .base import Repository
from ...models.squadron import Squadron


class SquadronRepository(Repository):
    """Repository for Squadron model operations."""
    
    def __init__(self, db_manager):
        """Initialize the repository.
        
        Args:
            db_manager: Database manager instance.
        """
        super().__init__(db_manager, Squadron)
    
    def find_by_faction(self, faction_id):
        """Find all squadrons belonging to a faction.
        
        Args:
            faction_id (str): Faction ID.
            
        Returns:
            list: List of Squadron instances.
        """
        try:
            query = "SELECT * FROM squadrons WHERE faction_id = :faction_id"
            results = self.db_manager.execute_query(query, {"faction_id": faction_id})
            
            return [self.model_class.from_dict(dict(row)) for row in results]
        except Exception as e:
            logging.error(f"Error finding squadrons for faction {faction_id}: {str(e)}")
            return []
    
    def find_by_district(self, district_id):
        """Find all squadrons in a district.
        
        Args:
            district_id (str): District ID.
            
        Returns:
            list: List of Squadron instances.
        """
        try:
            query = "SELECT * FROM squadrons WHERE district_id = :district_id"
            results = self.db_manager.execute_query(query, {"district_id": district_id})
            
            return [self.model_class.from_dict(dict(row)) for row in results]
        except Exception as e:
            logging.error(f"Error finding squadrons in district {district_id}: {str(e)}")
            return []
    
    def create(self, squadron):
        """Create a new squadron in the database.
        
        Args:
            squadron (Squadron): Squadron instance to create.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Validate the squadron
            if not squadron.validate():
                logging.error(f"Invalid squadron: {squadron.errors}")
                return False
                
            # Begin transaction using context manager
            with self.db_manager.connection:
                # Prepare squadron data
                data = {
                    'id': squadron.id,
                    'name': squadron.name,
                    'faction_id': squadron.faction_id,
                    'type': squadron.type,
                    'mobility': squadron.mobility,
                    'combat_aptitude': squadron.combat_aptitude,
                    'underworld_aptitude': squadron.underworld_aptitude,
                    'social_aptitude': squadron.social_aptitude,
                    'technical_aptitude': squadron.technical_aptitude,
                    'labor_aptitude': squadron.labor_aptitude,
                    'arcane_aptitude': squadron.arcane_aptitude,
                    'wilderness_aptitude': squadron.wilderness_aptitude,
                    'monitoring_aptitude': squadron.monitoring_aptitude,
                    'district_id': squadron.district_id,
                    'assignment': json.dumps(squadron.current_task) if squadron.current_task else None,
                    'created_at': squadron.created_at,
                    'updated_at': squadron.updated_at
                }
                
                query = """
                    INSERT INTO squadrons (
                        id, name, faction_id, type, mobility,
                        combat_aptitude, underworld_aptitude, social_aptitude,
                        technical_aptitude, labor_aptitude, arcane_aptitude,
                        wilderness_aptitude, monitoring_aptitude,
                        district_id, assignment, created_at, updated_at
                    )
                    VALUES (
                        :id, :name, :faction_id, :type, :mobility,
                        :combat_aptitude, :underworld_aptitude, :social_aptitude,
                        :technical_aptitude, :labor_aptitude, :arcane_aptitude,
                        :wilderness_aptitude, :monitoring_aptitude,
                        :district_id, :assignment, :created_at, :updated_at
                    )
                """
                
                self.db_manager.execute_update(query, data)
                
            return True
        except Exception as e:
            logging.error(f"Error creating squadron: {str(e)}")
            return False
    
    def update(self, squadron):
        """Update an existing squadron in the database.
        
        Args:
            squadron (Squadron): Squadron instance to update.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Validate the squadron
            if not squadron.validate():
                logging.error(f"Invalid squadron: {squadron.errors}")
                return False
                
            # Begin transaction using context manager
            with self.db_manager.connection:
                # Prepare squadron data
                data = {
                    'id': squadron.id,
                    'name': squadron.name,
                    'faction_id': squadron.faction_id,
                    'type': squadron.type,
                    'mobility': squadron.mobility,
                    'combat_aptitude': squadron.combat_aptitude,
                    'underworld_aptitude': squadron.underworld_aptitude,
                    'social_aptitude': squadron.social_aptitude,
                    'technical_aptitude': squadron.technical_aptitude,
                    'labor_aptitude': squadron.labor_aptitude,
                    'arcane_aptitude': squadron.arcane_aptitude,
                    'wilderness_aptitude': squadron.wilderness_aptitude,
                    'monitoring_aptitude': squadron.monitoring_aptitude,
                    'district_id': squadron.district_id,
                    'assignment': json.dumps(squadron.current_task) if squadron.current_task else None,
                    'updated_at': datetime.now().isoformat()
                }
                
                query = """
                    UPDATE squadrons SET
                        name = :name,
                        faction_id = :faction_id,
                        type = :type,
                        mobility = :mobility,
                        combat_aptitude = :combat_aptitude,
                        underworld_aptitude = :underworld_aptitude,
                        social_aptitude = :social_aptitude,
                        technical_aptitude = :technical_aptitude,
                        labor_aptitude = :labor_aptitude,
                        arcane_aptitude = :arcane_aptitude,
                        wilderness_aptitude = :wilderness_aptitude,
                        monitoring_aptitude = :monitoring_aptitude,
                        district_id = :district_id,
                        assignment = :assignment,
                        updated_at = :updated_at
                    WHERE id = :id
                """
                
                result = self.db_manager.execute_update(query, data)
                
                if result <= 0:
                    return False
                    
            return True
        except Exception as e:
            logging.error(f"Error updating squadron {squadron.id}: {str(e)}")
            return False
    
    def update_task(self, squadron_id, district_id, task_type, target_faction=None,
                   primary_aptitude=None, dc=None, monitoring=True, manual_modifier=0):
        """Update a squadron's task.
        
        Args:
            squadron_id (str): Squadron ID.
            district_id (str): District ID.
            task_type (str): Type of task.
            target_faction (str, optional): Target faction ID. Defaults to None.
            primary_aptitude (str, optional): Primary aptitude to use. Defaults to None.
            dc (int, optional): Difficulty class for the task. Defaults to None.
            monitoring (bool, optional): If the squadron performs monitoring. Defaults to True.
            manual_modifier (int, optional): Manual modifier for the task. Defaults to 0.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            with self.db_manager.connection:
                # Get squadron
                squadron = self.find_by_id(squadron_id)
                if not squadron:
                    logging.error(f"Squadron {squadron_id} not found")
                    return False
                    
                # Get current turn number
                turn_query = "SELECT current_turn FROM game_state WHERE id = 'current'"
                result = self.db_manager.execute_query(turn_query)
                if not result:
                    logging.error("Could not get current turn number")
                    return False
                    
                turn_number = result[0]["current_turn"]
                
                # Create task dictionary
                task = {
                    "type": task_type,
                    "target_faction": target_faction,
                    "primary_aptitude": primary_aptitude,
                    "dc": dc,
                    "performs_monitoring": monitoring,
                    "manual_modifier": manual_modifier
                }
                
                # Update squadron record
                update_query = """
                    UPDATE squadrons
                    SET district_id = :district_id,
                        assignment = :task,
                        updated_at = :updated_at
                    WHERE id = :id
                """
                
                now = datetime.now().isoformat()
                update_data = {
                    'id': squadron_id,
                    'district_id': district_id,
                    'task': json.dumps(task),
                    'updated_at': now
                }
                
                self.db_manager.execute_update(update_query, update_data)
                
                # Delete any existing action for this turn
                delete_query = """
                    DELETE FROM actions
                    WHERE piece_id = :piece_id
                    AND piece_type = 'squadron'
                    AND turn_number = :turn_number
                """
                
                self.db_manager.execute_update(delete_query, {
                    'piece_id': squadron_id,
                    'turn_number': turn_number
                })
                
                # Create new action record for the current turn
                action_query = """
                    INSERT INTO actions (
                        id, turn_number, piece_id, piece_type, faction_id, district_id,
                        action_type, target_faction_id, aptitude_used,
                        dc, manual_modifier, created_at, updated_at
                    )
                    VALUES (
                        :id, :turn_number, :piece_id, :piece_type, :faction_id, :district_id,
                        :action_type, :target_faction_id, :aptitude_used,
                        :dc, :manual_modifier, :created_at, :updated_at
                    )
                """
                
                action_data = {
                    'id': str(uuid.uuid4()),
                    'turn_number': turn_number,
                    'piece_id': squadron_id,
                    'piece_type': 'squadron',
                    'faction_id': squadron.faction_id,
                    'district_id': district_id,
                    'action_type': task_type,
                    'target_faction_id': target_faction,
                    'aptitude_used': primary_aptitude,
                    'dc': dc,
                    'manual_modifier': manual_modifier,
                    'created_at': now,
                    'updated_at': now
                }
                
                self.db_manager.execute_update(action_query, action_data)
                
                return True
                
        except Exception as e:
            logging.error(f"Error updating squadron task: {str(e)}")
            return False

    def assign_task(self, squadron_id, district_id, task_type, target_faction=None,
                   primary_aptitude=None, dc=None, monitoring=True, manual_modifier=0):
        """Assign a task to a squadron. This is now a wrapper for update_task for backwards compatibility.
        
        Args:
            squadron_id (str): Squadron ID.
            district_id (str): District ID.
            task_type (str): Type of task.
            target_faction (str, optional): Target faction ID. Defaults to None.
            primary_aptitude (str, optional): Primary aptitude to use. Defaults to None.
            dc (int, optional): Difficulty class for the task. Defaults to None.
            monitoring (bool, optional): If the squadron performs monitoring. Defaults to True.
            manual_modifier (int, optional): Manual modifier for the task. Defaults to 0.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        return self.update_task(squadron_id, district_id, task_type, target_faction,
                              primary_aptitude, dc, monitoring, manual_modifier)
    
    def clear_task(self, squadron_id):
        """Clear a squadron's current task.
        
        Args:
            squadron_id (str): Squadron ID.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            squadron = self.find_by_id(squadron_id)
            if not squadron:
                return False
                
            # Begin transaction using context manager
            with self.db_manager.connection:
                query = """
                    UPDATE squadrons SET
                        district_id = NULL,
                        assignment = NULL,
                        updated_at = :updated_at
                    WHERE id = :id
                """
                
                data = {
                    'id': squadron_id,
                    'updated_at': datetime.now().isoformat()
                }
                
                result = self.db_manager.execute_update(query, data)
                
                if result <= 0:
                    return False
                    
                # Update squadron model for consistency
                squadron.district_id = None
                squadron.current_task = None
                
            return True
        except Exception as e:
            logging.error(f"Error clearing task for squadron {squadron_id}: {str(e)}")
            return False