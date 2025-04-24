import logging
import json
from datetime import datetime
import uuid

from .base import Repository
from ...models.agent import Agent


class AgentRepository(Repository):
    """Repository for Agent model operations."""
    
    def __init__(self, db_manager):
        """Initialize the repository.
        
        Args:
            db_manager: Database manager instance.
        """
        super().__init__(db_manager, Agent)
    
    def find_by_faction(self, faction_id):
        """Find all agents belonging to a faction.
        
        Args:
            faction_id (str): Faction ID.
            
        Returns:
            list: List of Agent instances.
        """
        try:
            query = "SELECT * FROM agents WHERE faction_id = :faction_id"
            results = self.db_manager.execute_query(query, {"faction_id": faction_id})
            
            return [self.model_class.from_dict(dict(row)) for row in results]
        except Exception as e:
            logging.error(f"Error finding agents for faction {faction_id}: {str(e)}")
            return []
    
    def find_by_district(self, district_id):
        """Find all agents in a district.
        
        Args:
            district_id (str): District ID.
            
        Returns:
            list: List of Agent instances.
        """
        try:
            query = "SELECT * FROM agents WHERE district_id = :district_id"
            results = self.db_manager.execute_query(query, {"district_id": district_id})
            
            return [self.model_class.from_dict(dict(row)) for row in results]
        except Exception as e:
            logging.error(f"Error finding agents in district {district_id}: {str(e)}")
            return []
    
    def create(self, agent):
        """Create a new agent in the database.
        
        Args:
            agent (Agent): Agent instance to create.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Validate the agent
            if not agent.validate():
                logging.error(f"Invalid agent: {agent.errors}")
                return False
                
            # Begin transaction using context manager
            with self.db_manager.connection:
                # Prepare agent data
                data = {
                    'id': agent.id,
                    'name': agent.name,
                    'faction_id': agent.faction_id,
                    'attunement': agent.attunement,
                    'intellect': agent.intellect,
                    'finesse': agent.finesse,
                    'might': agent.might,
                    'presence': agent.presence,
                    'infiltration': agent.infiltration,
                    'persuasion': agent.persuasion,
                    'combat': agent.combat,
                    'streetwise': agent.streetwise,
                    'survival': agent.survival,
                    'artifice': agent.artifice,
                    'arcana': agent.arcana,
                    'district_id': agent.district_id,
                    'assignment': json.dumps(agent.current_task) if agent.current_task else None,
                    'created_at': agent.created_at,
                    'updated_at': agent.updated_at
                }
                
                query = """
                    INSERT INTO agents (
                        id, name, faction_id, attunement, intellect, finesse, might, presence,
                        infiltration, persuasion, combat, streetwise, survival, artifice, arcana,
                        district_id, assignment, created_at, updated_at
                    )
                    VALUES (
                        :id, :name, :faction_id, :attunement, :intellect, :finesse, :might, :presence,
                        :infiltration, :persuasion, :combat, :streetwise, :survival, :artifice, :arcana,
                        :district_id, :assignment, :created_at, :updated_at
                    )
                """
                
                self.db_manager.execute_update(query, data)
                
            return True
        except Exception as e:
            logging.error(f"Error creating agent: {str(e)}")
            return False
    
    def update(self, agent):
        """Update an existing agent in the database.
        
        Args:
            agent (Agent): Agent instance to update.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Validate the agent
            if not agent.validate():
                logging.error(f"Invalid agent: {agent.errors}")
                return False
                
            # Begin transaction using context manager
            with self.db_manager.connection:
                # Prepare agent data
                data = {
                    'id': agent.id,
                    'name': agent.name,
                    'faction_id': agent.faction_id,
                    'attunement': agent.attunement,
                    'intellect': agent.intellect,
                    'finesse': agent.finesse,
                    'might': agent.might,
                    'presence': agent.presence,
                    'infiltration': agent.infiltration,
                    'persuasion': agent.persuasion,
                    'combat': agent.combat,
                    'streetwise': agent.streetwise,
                    'survival': agent.survival,
                    'artifice': agent.artifice,
                    'arcana': agent.arcana,
                    'district_id': agent.district_id,
                    'assignment': json.dumps(agent.current_task) if agent.current_task else None,
                    'updated_at': datetime.now().isoformat()
                }
                
                query = """
                    UPDATE agents SET
                        name = :name,
                        faction_id = :faction_id,
                        attunement = :attunement,
                        intellect = :intellect,
                        finesse = :finesse,
                        might = :might,
                        presence = :presence,
                        infiltration = :infiltration,
                        persuasion = :persuasion,
                        combat = :combat,
                        streetwise = :streetwise,
                        survival = :survival,
                        artifice = :artifice,
                        arcana = :arcana,
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
            logging.error(f"Error updating agent {agent.id}: {str(e)}")
            return False
    
    def update_task(self, agent_id, district_id, task_type, target_faction=None,
                   attribute=None, skill=None, dc=None, monitoring=True, manual_modifier=0, description=None):
        """Update an agent's task.
        
        Args:
            agent_id (str): Agent ID.
            district_id (str): District ID.
            task_type (str): Type of task.
            target_faction (str, optional): Target faction ID. Defaults to None.
            attribute (str, optional): Attribute to use. Defaults to None.
            skill (str, optional): Skill to use. Defaults to None.
            dc (int, optional): Difficulty class for the task. Defaults to None.
            monitoring (bool, optional): If the agent performs monitoring. Defaults to True.
            manual_modifier (int, optional): Manual modifier for the task. Defaults to 0.
            description (str, optional): Description of the task. Defaults to None.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            with self.db_manager.connection:
                # Get agent
                agent = self.find_by_id(agent_id)
                if not agent:
                    logging.error(f"Agent {agent_id} not found")
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
                    "attribute": attribute,
                    "skill": skill,
                    "dc": dc,
                    "performs_monitoring": monitoring,
                    "manual_modifier": manual_modifier,
                    "description": description
                }
                
                # Update agent record
                update_query = """
                    UPDATE agents
                    SET district_id = :district_id,
                        assignment = :task,
                        updated_at = :updated_at
                    WHERE id = :id
                """
                
                now = datetime.now().isoformat()
                update_data = {
                    'id': agent_id,
                    'district_id': district_id,
                    'task': json.dumps(task),
                    'updated_at': now
                }
                
                self.db_manager.execute_update(update_query, update_data)
                
                # Delete any existing action for this turn
                delete_query = """
                    DELETE FROM actions
                    WHERE piece_id = :piece_id
                    AND piece_type = 'agent'
                    AND turn_number = :turn_number
                """
                
                self.db_manager.execute_update(delete_query, {
                    'piece_id': agent_id,
                    'turn_number': turn_number
                })
                
                # Create new action record for the current turn
                action_query = """
                    INSERT INTO actions (
                        id, turn_number, piece_id, piece_type, faction_id, district_id,
                        action_type, action_description, target_faction_id, attribute_used, skill_used,
                        dc, manual_modifier, created_at, updated_at
                    )
                    VALUES (
                        :id, :turn_number, :piece_id, :piece_type, :faction_id, :district_id,
                        :action_type, :action_description, :target_faction_id, :attribute_used, :skill_used,
                        :dc, :manual_modifier, :created_at, :updated_at
                    )
                """
                
                action_data = {
                    'id': str(uuid.uuid4()),
                    'turn_number': turn_number,
                    'piece_id': agent_id,
                    'piece_type': 'agent',
                    'faction_id': agent.faction_id,
                    'district_id': district_id,
                    'action_type': task_type,
                    'action_description': description,
                    'target_faction_id': target_faction,
                    'attribute_used': attribute,
                    'skill_used': skill,
                    'dc': dc,
                    'manual_modifier': manual_modifier,
                    'created_at': now,
                    'updated_at': now
                }
                
                self.db_manager.execute_update(action_query, action_data)
                
                return True
                
        except Exception as e:
            logging.error(f"Error updating agent task: {str(e)}")
            return False

    def assign_task(self, agent_id, district_id, task_type, target_faction=None,
                   attribute=None, skill=None, dc=None, monitoring=True, manual_modifier=0, description=None):
        """Assign a task to an agent. This is now a wrapper for update_task for backwards compatibility.
        
        Args:
            agent_id (str): Agent ID.
            district_id (str): District ID.
            task_type (str): Type of task.
            target_faction (str, optional): Target faction ID. Defaults to None.
            attribute (str, optional): Attribute to use. Defaults to None.
            skill (str, optional): Skill to use. Defaults to None.
            dc (int, optional): Difficulty class for the task. Defaults to None.
            monitoring (bool, optional): If the agent performs monitoring. Defaults to True.
            manual_modifier (int, optional): Manual modifier for the task. Defaults to 0.
            description (str, optional): Description of the task. Defaults to None.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        return self.update_task(agent_id, district_id, task_type, target_faction,
                              attribute, skill, dc, monitoring, manual_modifier, description)
    
    def clear_task(self, agent_id):
        """Clear an agent's current task.
        
        Args:
            agent_id (str): Agent ID.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            agent = self.find_by_id(agent_id)
            if not agent:
                return False
                
            # Begin transaction using context manager
            with self.db_manager.connection:
                query = """
                    UPDATE agents SET
                        district_id = NULL,
                        assignment = NULL,
                        updated_at = :updated_at
                    WHERE id = :id
                """
                
                data = {
                    'id': agent_id,
                    'updated_at': datetime.now().isoformat()
                }
                
                result = self.db_manager.execute_update(query, data)
                
                if result <= 0:
                    return False
                    
                # Update agent model for consistency
                agent.district_id = None
                agent.current_task = None
                
            return True
        except Exception as e:
            logging.error(f"Error clearing task for agent {agent_id}: {str(e)}")
            return False