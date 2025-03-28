import logging
import random
import json
import uuid
from datetime import datetime

from .influence import InfluenceManager
from .relationship import RelationshipManager


class TurnManager:
    """Manages the turn structure and phase transitions."""
    
    def __init__(self, db_manager, district_repository, faction_repository, 
                 agent_repository, squadron_repository, rumor_repository):
        """Initialize the turn manager.
        
        Args:
            db_manager: Database manager instance.
            district_repository: Repository for district operations.
            faction_repository: Repository for faction operations.
            agent_repository: Repository for agent operations.
            squadron_repository: Repository for squadron operations.
            rumor_repository: Repository for rumor operations.
        """
        self.db_manager = db_manager
        self.district_repository = district_repository
        self.faction_repository = faction_repository
        self.agent_repository = agent_repository
        self.squadron_repository = squadron_repository
        self.rumor_repository = rumor_repository
        
        # Initialize helper managers
        self.influence_manager = InfluenceManager(district_repository, faction_repository)
        self.relationship_manager = RelationshipManager(faction_repository)
    
    def get_current_turn(self):
        """Get the current turn information.
        
        Returns:
            dict: Turn information.
        """
        try:
            query = """
                SELECT current_turn, current_phase, campaign_name
                FROM game_state
                WHERE id = 'current'
            """
            
            result = self.db_manager.execute_query(query)
            logging.info(f"Turn query result: {result}")
            
            if result:
                # Convert sqlite3.Row to dictionary
                turn_info = {
                    'current_turn': result[0]['current_turn'],
                    'current_phase': result[0]['current_phase'],
                    'campaign_name': result[0]['campaign_name']
                }
                return turn_info
            else:
                # Default values if no turn information exists
                default_turn = {
                    'current_turn': 1,
                    'current_phase': 'preparation',
                    'campaign_name': 'New Campaign'
                }
                
                # Try to create the initial game state
                try:
                    with self.db_manager.connection:
                        self.db_manager.connection.execute("""
                            INSERT INTO game_state (id, current_turn, current_phase, campaign_name)
                            VALUES ('current', 1, 'preparation', 'New Campaign')
                        """)
                except Exception as e:
                    logging.error(f"Error creating initial game state: {str(e)}")
                
                return default_turn
        except Exception as e:
            logging.error(f"Error loading turns: {str(e)}")
            return {
                'current_turn': 1,
                'current_phase': 'preparation',
                'campaign_name': 'New Campaign'
            }
    
    def set_current_phase(self, phase):
        """Set the current phase of the turn.
        
        Args:
            phase (str): Phase name.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            with self.db_manager.connection:
                query = """
                    UPDATE game_state SET
                        current_phase = :phase,
                        last_updated = :now,
                        updated_at = :now
                    WHERE id = 'current'
                """
                
                self.db_manager.execute_update(query, {
                    "phase": phase,
                    "now": datetime.now().isoformat()
                })
                
                # Log phase change
                turn_info = self.get_current_turn()
                self.log_turn_history(
                    turn_info["current_turn"],
                    phase,
                    f"Phase changed to {phase}",
                    ""
                )
                
            return True
        except Exception as e:
            logging.error(f"Error in set_current_phase: {str(e)}")
            return False
    
    def advance_turn(self):
        """Advance to the next turn.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            turn_info = self.get_current_turn()
            new_turn = turn_info["current_turn"] + 1
            
            with self.db_manager.connection:
                query = """
                    UPDATE game_state SET
                        current_turn = :turn,
                        current_phase = 'preparation',
                        last_updated = :now,
                        updated_at = :now
                    WHERE id = 'current'
                """
                
                self.db_manager.execute_update(query, {
                    "turn": new_turn,
                    "now": datetime.now().isoformat()
                })
                
                # Log turn advancement
                self.log_turn_history(
                    new_turn,
                    "preparation",
                    f"Advanced to turn {new_turn}",
                    ""
                )
                
            return True
        except Exception as e:
            logging.error(f"Error in advance_turn: {str(e)}")
            return False
    
    def log_turn_history(self, turn_number, phase, action_description, result_description):
        """Log an event in the turn history.
        
        Args:
            turn_number (int): Turn number.
            phase (str): Phase name.
            action_description (str): Description of the action.
            result_description (str): Description of the result.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            with self.db_manager.connection:
                query = """
                    INSERT INTO turn_history (
                        turn_number, phase, action_description, result_description, created_at
                    )
                    VALUES (
                        :turn_number, :phase, :action_description, :result_description, :created_at
                    )
                """
                
                self.db_manager.execute_update(query, {
                    "turn_number": turn_number,
                    "phase": phase,
                    "action_description": action_description,
                    "result_description": result_description,
                    "created_at": datetime.now().isoformat()
                })
                
            return True
        except Exception as e:
            logging.error(f"Error in log_turn_history: {str(e)}")
            return False
    
    def process_influence_decay_phase(self):
        """Process the influence decay phase.
        
        Returns:
            dict: Results of decay processing.
        """
        try:
            turn_info = self.get_current_turn()
            districts = self.district_repository.find_all()
            
            results = {
                "processed_districts": 0,
                "total_influence_lost": 0,
                "affected_factions": set()
            }
            
            # Process decay for each district
            for district in districts:
                decay_results = self.influence_manager.calculate_decay(district.id, turn_info)
                
                if decay_results:
                    self.influence_manager.apply_decay(district.id, decay_results)
                    
                    # Update results
                    results["processed_districts"] += 1
                    
                    for faction_id, amount in decay_results.items():
                        results["total_influence_lost"] += amount
                        results["affected_factions"].add(faction_id)
                        
                        # Log decay event
                        self.log_turn_history(
                            turn_info["current_turn"],
                            "influence_decay",
                            f"Faction {faction_id} lost {amount} influence in district {district.id}",
                            f"New influence: {district.get_faction_influence(faction_id)}"
                        )
            
            # Convert affected_factions to list for JSON serialization
            results["affected_factions"] = list(results["affected_factions"])
            
            # Update phase
            self.set_current_phase("assignment")
            
            return results
        except Exception as e:
            logging.error(f"Error in process_influence_decay_phase: {str(e)}")
            return {"error": str(e)}
    
    def update_district_dc_modifiers(self):
        """Update the weekly DC modifiers for all districts.
        
        Returns:
            dict: Results of update.
        """
        try:
            districts = self.district_repository.find_all()
            turn_info = self.get_current_turn()
            
            results = {
                "updated_districts": [],
                "unchanged_districts": []
            }
            
            for district in districts:
                old_modifier = district.weekly_dc_modifier
                
                # Random walk: -1, 0, or +1 with constraints
                if old_modifier == -2:
                    change = random.choice([0, 1])  # Can only go up or stay
                elif old_modifier == 2:
                    change = random.choice([-1, 0])  # Can only go down or stay
                else:
                    change = random.choice([-1, 0, 1])  # Can go any direction
                
                new_modifier = old_modifier + change
                
                # Apply the change if any
                if old_modifier != new_modifier:
                    district.weekly_dc_modifier = new_modifier
                    self.district_repository.set_weekly_dc_modifier(district.id, new_modifier)
                    
                    results["updated_districts"].append({
                        "district_id": district.id,
                        "district_name": district.name,
                        "old_modifier": old_modifier,
                        "new_modifier": new_modifier
                    })
                    
                    # Log modifier change
                    self.log_turn_history(
                        turn_info["current_turn"],
                        "random_walk_update",
                        f"District {district.name} DC modifier changed from {old_modifier} to {new_modifier}",
                        "Affects all gain/take control DCs"
                    )
                else:
                    results["unchanged_districts"].append({
                        "district_id": district.id,
                        "district_name": district.name,
                        "modifier": old_modifier
                    })
            
            return results
        except Exception as e:
            logging.error(f"Error in update_district_dc_modifiers: {str(e)}")
            return {"error": str(e)}
    
    def decrease_rumor_dcs(self):
        """Decrease the discovery DC for all rumors by 1.
        
        Returns:
            dict: Results of update.
        """
        try:
            # Get all rumors
            query = "SELECT id, discovery_dc FROM district_rumors"
            results = self.db_manager.execute_query(query)
            
            updated_rumors = []
            
            for row in results:
                rumor_id = row['id']
                old_dc = row['discovery_dc']
                
                # Don't decrease below 1
                if old_dc > 1:
                    new_dc = self.rumor_repository.decrease_dc(rumor_id)
                    
                    if new_dc is not None:
                        updated_rumors.append({
                            "rumor_id": rumor_id,
                            "old_dc": old_dc,
                            "new_dc": new_dc
                        })
            
            return {"updated_rumors": updated_rumors}
        except Exception as e:
            logging.error(f"Error in decrease_rumor_dcs: {str(e)}")
            return {"error": str(e)}