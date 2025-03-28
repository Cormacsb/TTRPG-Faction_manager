import logging
import random


class RelationshipManager:
    """Manages faction relationship mechanics."""
    
    def __init__(self, faction_repository):
        """Initialize the relationship manager.
        
        Args:
            faction_repository: Repository for faction operations.
        """
        self.faction_repository = faction_repository
    
    def set_relationship(self, faction_id, target_faction_id, value):
        """Set the relationship value between two factions.
        
        Args:
            faction_id (str): Source faction ID.
            target_faction_id (str): Target faction ID.
            value (int): Relationship value (-2 to +2).
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Validate relationship value
            if not -2 <= value <= 2:
                logging.error(f"Invalid relationship value: {value}")
                return False
            
            # Ensure factions exist
            faction = self.faction_repository.find_by_id(faction_id)
            target_faction = self.faction_repository.find_by_id(target_faction_id)
            
            if not faction or not target_faction:
                logging.error(f"Faction not found: {faction_id if not faction else target_faction_id}")
                return False
            
            # Set relationship
            success = self.faction_repository.set_relationship(faction_id, target_faction_id, value)
            
            return success
        except Exception as e:
            logging.error(f"Error in set_relationship: {str(e)}")
            return False
    
    def adjust_relationship(self, faction_id, target_faction_id, adjustment):
        """Adjust the relationship value between two factions.
        
        Args:
            faction_id (str): Source faction ID.
            target_faction_id (str): Target faction ID.
            adjustment (int): Amount to adjust relationship by.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Ensure factions exist
            faction = self.faction_repository.find_by_id(faction_id)
            target_faction = self.faction_repository.find_by_id(target_faction_id)
            
            if not faction or not target_faction:
                logging.error(f"Faction not found: {faction_id if not faction else target_faction_id}")
                return False
            
            # Get current relationship
            current = faction.get_relationship(target_faction_id)
            
            # Calculate new value, clamped to valid range
            new_value = max(-2, min(2, current + adjustment))
            
            # Set new relationship
            success = self.faction_repository.set_relationship(faction_id, target_faction_id, new_value)
            
            return success
        except Exception as e:
            logging.error(f"Error in adjust_relationship: {str(e)}")
            return False
    
    def get_support_status(self, db_manager, turn_number, declaring_faction_id, target_faction_id):
        """Get the support status between two factions.
        
        Args:
            db_manager: Database manager instance.
            turn_number (int): Current turn number.
            declaring_faction_id (str): Faction ID declaring support.
            target_faction_id (str): Faction ID to support.
            
        Returns:
            bool: True if faction supports target, False otherwise.
        """
        try:
            # Ensure factions exist
            declaring_faction = self.faction_repository.find_by_id(declaring_faction_id)
            target_faction = self.faction_repository.find_by_id(target_faction_id)
            
            if not declaring_faction or not target_faction:
                logging.error(f"Faction not found: {declaring_faction_id if not declaring_faction else target_faction_id}")
                return False
            
            # Check relationship - only allowed if Allied (+2)
            relationship = declaring_faction.get_relationship(target_faction_id)
            if relationship < 2:
                return False  # Not allied, cannot support
            
            # Query support status
            query = """
                SELECT will_support
                FROM faction_support_status
                WHERE turn_number = :turn_number
                AND declaring_faction_id = :declaring_faction_id
                AND target_faction_id = :target_faction_id
            """
            
            params = {
                "turn_number": turn_number,
                "declaring_faction_id": declaring_faction_id,
                "target_faction_id": target_faction_id
            }
            
            results = db_manager.execute_query(query, params)
            
            if results:
                return bool(results[0]['will_support'])
            
            return False  # Default to not supporting
            
        except Exception as e:
            logging.error(f"Error in get_support_status: {str(e)}")
            return False
    
    def set_support_status(self, db_manager, turn_number, declaring_faction_id, target_faction_id, will_support):
        """Set the support status between two factions.
        
        Args:
            db_manager: Database manager instance.
            turn_number (int): Current turn number.
            declaring_faction_id (str): Faction ID declaring support.
            target_faction_id (str): Faction ID to support.
            will_support (bool): Whether to support.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Ensure factions exist
            declaring_faction = self.faction_repository.find_by_id(declaring_faction_id)
            target_faction = self.faction_repository.find_by_id(target_faction_id)
            
            if not declaring_faction or not target_faction:
                logging.error(f"Faction not found: {declaring_faction_id if not declaring_faction else target_faction_id}")
                return False
            
            # Check relationship - only allowed if Allied (+2)
            relationship = declaring_faction.get_relationship(target_faction_id)
            if relationship < 2 and will_support:
                logging.error(f"Cannot set support status: relationship is {relationship}, not Allied (+2)")
                return False
            
            # Begin transaction
            with db_manager.connection:
                # Check if record exists
                query = """
                    SELECT 1
                    FROM faction_support_status
                    WHERE turn_number = :turn_number
                    AND declaring_faction_id = :declaring_faction_id
                    AND target_faction_id = :target_faction_id
                """
                
                params = {
                    "turn_number": turn_number,
                    "declaring_faction_id": declaring_faction_id,
                    "target_faction_id": target_faction_id
                }
                
                exists = db_manager.execute_query(query, params)
                
                if exists:
                    # Update existing record
                    query = """
                        UPDATE faction_support_status SET
                            will_support = :will_support,
                            updated_at = :updated_at
                        WHERE turn_number = :turn_number
                        AND declaring_faction_id = :declaring_faction_id
                        AND target_faction_id = :target_faction_id
                    """
                    
                    params = {
                        "turn_number": turn_number,
                        "declaring_faction_id": declaring_faction_id,
                        "target_faction_id": target_faction_id,
                        "will_support": will_support,
                        "updated_at": datetime.now().isoformat()
                    }
                    
                    db_manager.execute_update(query, params)
                else:
                    # Insert new record
                    query = """
                        INSERT INTO faction_support_status (
                            turn_number, declaring_faction_id, target_faction_id,
                            will_support, created_at, updated_at
                        )
                        VALUES (
                            :turn_number, :declaring_faction_id, :target_faction_id,
                            :will_support, :created_at, :updated_at
                        )
                    """
                    
                    params = {
                        "turn_number": turn_number,
                        "declaring_faction_id": declaring_faction_id,
                        "target_faction_id": target_faction_id,
                        "will_support": will_support,
                        "created_at": datetime.now().isoformat(),
                        "updated_at": datetime.now().isoformat()
                    }
                    
                    db_manager.execute_update(query, params)
            
            return True
            
        except Exception as e:
            logging.error(f"Error in set_support_status: {str(e)}")
            return False
    
    def calculate_relationship_penalty(self, agent_id, squadron_id, db_manager):
        """Calculate the penalty for a piece based on relationship with other factions.
        
        Args:
            agent_id (str): Agent ID or None.
            squadron_id (str): Squadron ID or None.
            db_manager: Database manager instance.
            
        Returns:
            int: Penalty value to apply.
        """
        try:
            # Only one of agent_id or squadron_id should be provided
            if agent_id and squadron_id:
                logging.error("Both agent_id and squadron_id provided")
                return 0
            
            if not agent_id and not squadron_id:
                logging.error("Neither agent_id nor squadron_id provided")
                return 0
            
            piece_type = "agent" if agent_id else "squadron"
            piece_id = agent_id if agent_id else squadron_id
            
            # Get piece information
            if piece_type == "agent":
                query = "SELECT faction_id, district_id FROM agents WHERE id = :id"
            else:
                query = "SELECT faction_id, district_id, mobility FROM squadrons WHERE id = :id"
            
            result = db_manager.execute_query(query, {"id": piece_id})
            
            if not result:
                logging.error(f"{piece_type.capitalize()} {piece_id} not found")
                return 0
            
            piece_data = dict(result[0])
            faction_id = piece_data["faction_id"]
            district_id = piece_data["district_id"]
            
            if not district_id:
                return 0  # Not assigned to a district
            
            # Get mobility for squadrons
            mobility = piece_data.get("mobility", 0) if piece_type == "squadron" else 0
            
            # Get all factions with negative relationships
            faction = self.faction_repository.find_by_id(faction_id)
            if not faction:
                logging.error(f"Faction {faction_id} not found")
                return 0
            
            enemy_factions = {}
            for target_id, value in faction.relationships.items():
                if value < 0:
                    enemy_factions[target_id] = value
            
            if not enemy_factions:
                return 0  # No negative relationships
            
            # Get enemy pieces that could affect this piece
            penalty = 0
            
            # For agents, only affected by pieces in same district
            if piece_type == "agent":
                # Get enemy agents in same district
                query = """
                    SELECT a.id, a.faction_id
                    FROM agents a
                    WHERE a.district_id = :district_id
                    AND a.faction_id IN ({})
                    ORDER BY RANDOM()
                """.format(",".join(f"'{f}'" for f in enemy_factions.keys()))
                
                enemy_agents = db_manager.execute_query(query, {"district_id": district_id})
                
                # Apply penalty from a single enemy agent if present
                if enemy_agents:
                    enemy_agent = dict(enemy_agents[0])
                    relationship = enemy_factions[enemy_agent["faction_id"]]
                    
                    if relationship == -1:  # Cold War
                        penalty += 2  # -2 penalty
                    elif relationship == -2:  # Hot War
                        penalty += 4  # -4 penalty
                
                # Get enemy squadrons in same district
                query = """
                    SELECT s.id, s.faction_id
                    FROM squadrons s
                    WHERE s.district_id = :district_id
                    AND s.faction_id IN ({})
                    AND s.mobility > 0
                    ORDER BY RANDOM()
                """.format(",".join(f"'{f}'" for f in enemy_factions.keys()))
                
                enemy_squadrons = db_manager.execute_query(query, {"district_id": district_id})
                
                # Apply penalties from enemy squadrons if agents not present
                if not enemy_agents and enemy_squadrons:
                    enemy_squadron = dict(enemy_squadrons[0])
                    relationship = enemy_factions[enemy_squadron["faction_id"]]
                    
                    if relationship == -1:  # Cold War
                        penalty += 1  # -1 penalty
                    elif relationship == -2:  # Hot War
                        penalty += 2  # -2 penalty
            
            # For squadrons, affected by pieces in same and adjacent districts based on mobility
            else:
                # Get enemy squadrons in same or adjacent districts
                # Complexity increases with mobility, so this is simplified
                district = self.district_repository.find_by_id(district_id)
                if not district:
                    logging.error(f"District {district_id} not found")
                    return 0
                
                # Get all relevant districts based on mobility
                relevant_districts = [district_id] + district.adjacent_districts
                
                # Get enemy squadrons in relevant districts
                relevant_districts_str = ",".join(f"'{d}'" for d in relevant_districts)
                query = f"""
                    SELECT s.id, s.faction_id, s.district_id, s.mobility
                    FROM squadrons s
                    WHERE s.district_id IN ({relevant_districts_str})
                    AND s.faction_id IN ({",".join(f"'{f}'" for f in enemy_factions.keys())})
                    AND s.mobility > 0
                    ORDER BY RANDOM()
                """
                
                enemy_squadrons = db_manager.execute_query(query, {})
                
                # Apply penalties based on squadron mobility rules
                for enemy in enemy_squadrons:
                    enemy = dict(enemy)
                    relationship = enemy_factions[enemy["faction_id"]]
                    
                    # Skip if mobility doesn't allow affecting this squadron
                    enemy_mobility = enemy["mobility"]
                    same_district = enemy["district_id"] == district_id
                    
                    if not same_district and enemy_mobility < 2:
                        continue
                    
                    # Apply penalty
                    if relationship == -1:  # Cold War
                        penalty += 1  # -1 penalty
                    elif relationship == -2:  # Hot War
                        penalty += 2  # -2 penalty
                    
                    # Simplified: only apply one penalty per enemy faction
                    # In a full implementation, would need to track applied penalties by mobility rules
                    break
            
            return penalty
            
        except Exception as e:
            logging.error(f"Error in calculate_relationship_penalty: {str(e)}")
            return 0