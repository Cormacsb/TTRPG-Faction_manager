import logging
import random
import json
import uuid
from datetime import datetime

class PenaltyTracker:
    """
    Tracks applied penalties across pieces throughout the action resolution phase.
    This ensures agents only apply one penalty total and squadrons respect their mobility limits.
    """
    def __init__(self):
        # Track which agents have already applied penalties
        self.agent_penalties = set()
        
        # Track squadron penalties by faction and squadron
        # Structure: {squadron_id: {'same_district': count, 'adjacent_district': count, 'either_district': count}}
        self.squadron_penalties = {}
        
        logging.info("Initialized penalty tracker for action resolution phase")
    
    def has_agent_applied_penalty(self, agent_id):
        """Check if agent has already applied a penalty."""
        return agent_id in self.agent_penalties
    
    def mark_agent_penalty_applied(self, agent_id):
        """Mark that an agent has applied a penalty."""
        self.agent_penalties.add(agent_id)
        logging.info(f"Agent {agent_id} has applied its penalty")
    
    def get_squadron_applied_penalties(self, squadron_id):
        """Get count of penalties already applied by a squadron."""
        if squadron_id not in self.squadron_penalties:
            self.squadron_penalties[squadron_id] = {
                'same_district': 0,
                'adjacent_district': 0,
                'either_district': 0
            }
        return self.squadron_penalties[squadron_id]
    
    def can_squadron_apply_penalty(self, squadron_id, is_adjacent, mobility):
        """
        Check if squadron can apply another penalty based on mobility and targets so far.
        
        Args:
            squadron_id: ID of the squadron
            is_adjacent: Whether target is in adjacent district
            mobility: Mobility value of the squadron
            
        Returns:
            (bool, str): Can apply penalty and which slot type to use
        """
        # Get max targets for this mobility
        max_targets = self._get_squadron_max_targets(mobility)
        
        # Get current applied penalties
        penalties = self.get_squadron_applied_penalties(squadron_id)
        
        # Check if this target can be affected based on district type and available slots
        if is_adjacent:
            # Check for adjacent-specific slot
            if penalties['adjacent_district'] < max_targets['adjacent_district']:
                return True, 'adjacent_district'
            # If no adjacent slots, check for either-district slot
            elif penalties['either_district'] < max_targets['either_district']:
                return True, 'either_district'
        else:
            # Check for same-specific slot
            if penalties['same_district'] < max_targets['same_district']:
                return True, 'same_district'
            # If no same-district slots, check for either-district slot
            elif penalties['either_district'] < max_targets['either_district']:
                return True, 'either_district'
        
        return False, None
    
    def mark_squadron_penalty_applied(self, squadron_id, slot_type):
        """Mark that a squadron has applied a penalty using a specific slot type."""
        if squadron_id not in self.squadron_penalties:
            self.squadron_penalties[squadron_id] = {
                'same_district': 0,
                'adjacent_district': 0,
                'either_district': 0
            }
        
        self.squadron_penalties[squadron_id][slot_type] += 1
        logging.info(f"Squadron {squadron_id} applied penalty using {slot_type} slot " 
                    f"(now at {self.squadron_penalties[squadron_id][slot_type]})")
    
    def _get_squadron_max_targets(self, mobility):
        """Get maximum number of targets a squadron can affect based on mobility."""
        result = {
            'same_district': 0,
            'adjacent_district': 0,
            'either_district': 0
        }
        
        if mobility == 0:
            return result
        elif mobility == 1:
            result['same_district'] = 1
        elif mobility == 2:
            result['same_district'] = 1
            result['adjacent_district'] = 1
        elif mobility == 3:
            result['same_district'] = 1
            result['either_district'] = 1
        elif mobility == 4:
            result['either_district'] = 2
        elif mobility == 5:
            result['same_district'] = 1
            result['either_district'] = 2
            
        return result

class ActionManager:
    """Manages action creation, resolution, and outcomes."""
    
    def __init__(self, db_manager, district_repository, faction_repository, 
                 agent_repository, squadron_repository):
        """Initialize the action manager.
        
        Args:
            db_manager: Database manager instance.
            district_repository: Repository for district operations.
            faction_repository: Repository for faction operations.
            agent_repository: Repository for agent operations.
            squadron_repository: Repository for squadron operations.
        """
        self.db_manager = db_manager
        self.district_repository = district_repository
        self.faction_repository = faction_repository
        self.agent_repository = agent_repository
        self.squadron_repository = squadron_repository
        # Initialize penalty tracker for the current turn
        self.penalty_tracker = None
    
    def reset_penalty_tracker(self):
        """Reset the penalty tracker for a new action resolution phase."""
        self.penalty_tracker = PenaltyTracker()
        logging.info("Penalty tracker has been reset for a new action resolution phase")
    
    def create_action(self, turn_number, piece_id, piece_type, faction_id, district_id,
                     action_type, action_description=None, target_faction_id=None,
                     attribute_used=None, skill_used=None, aptitude_used=None,
                     dc=None, manual_modifier=0):
        """Create a new action record.
        
        Args:
            turn_number (int): Current turn number.
            piece_id (str): Agent or squadron ID.
            piece_type (str): Type of piece ('agent' or 'squadron').
            faction_id (str): Faction ID.
            district_id (str): District ID.
            action_type (str): Type of action (monitor, gain_influence, etc.).
            action_description (str, optional): Description of action. Defaults to None.
            target_faction_id (str, optional): Target faction ID. Defaults to None.
            attribute_used (str, optional): Primary attribute used (for agents). Defaults to None.
            skill_used (str, optional): Skill used (for agents). Defaults to None.
            aptitude_used (str, optional): Aptitude used (for squadrons). Defaults to None.
            dc (int, optional): Difficulty class. Defaults to None.
            manual_modifier (int, optional): Manual modifier to roll. Defaults to 0.
            
        Returns:
            str: Action ID if successful, None otherwise.
        """
        try:
            # Validate action parameters
            if piece_type not in ['agent', 'squadron']:
                logging.error(f"Invalid piece type: {piece_type}")
                return None
            if action_type not in ['monitor', 'gain_influence', 'take_influence', 'freeform', 'initiate_conflict']:
                logging.error(f"Invalid action type: {action_type}")
                return None
                
            if manual_modifier < -10 or manual_modifier > 10:
                logging.error(f"Manual modifier out of range: {manual_modifier}")
                return None
                
            # For agent actions, both attribute and skill should be specified
            if piece_type == 'agent' and action_type != 'monitor':
                if not attribute_used or not skill_used:
                    logging.error("Agent actions require both attribute and skill")
                    return None
                    
            # For squadron actions, aptitude should be specified
            if piece_type == 'squadron' and action_type != 'monitor':
                if not aptitude_used:
                    logging.error("Squadron actions require aptitude")
                    return None
                    
            # Targeting a faction is required for take_influence and initiate_conflict
            if action_type in ['take_influence', 'initiate_conflict'] and not target_faction_id:
                logging.error(f"{action_type} action requires target_faction_id")
                return None
                
            # Generate a unique action ID
            action_id = str(uuid.uuid4())
            
            # Begin transaction
            with self.db_manager.connection:
                query = """
                    INSERT INTO actions (
                        id, turn_number, piece_id, piece_type, faction_id, district_id,
                        action_type, action_description, target_faction_id,
                        attribute_used, skill_used, aptitude_used, dc, manual_modifier,
                        created_at, updated_at
                    )
                    VALUES (
                        :id, :turn_number, :piece_id, :piece_type, :faction_id, :district_id,
                        :action_type, :action_description, :target_faction_id,
                        :attribute_used, :skill_used, :aptitude_used, :dc, :manual_modifier,
                        :created_at, :updated_at
                    )
                """
                
                now = datetime.now().isoformat()
                
                params = {
                    "id": action_id,
                    "turn_number": turn_number,
                    "piece_id": piece_id,
                    "piece_type": piece_type,
                    "faction_id": faction_id,
                    "district_id": district_id,
                    "action_type": action_type,
                    "action_description": action_description,
                    "target_faction_id": target_faction_id,
                    "attribute_used": attribute_used,
                    "skill_used": skill_used,
                    "aptitude_used": aptitude_used,
                    "dc": dc,
                    "manual_modifier": manual_modifier,
                    "created_at": now,
                    "updated_at": now
                }
                
                self.db_manager.execute_update(query, params)
                
            return action_id
        except Exception as e:
            logging.error(f"Error in create_action: {str(e)}")
            return None
    
    def detect_conflicts(self, turn_number):
        """Detect conflicts between factions for the current turn.
        
        Args:
            turn_number (int): Current turn number.
            
        Returns:
            list: List of detected conflicts.
        """
        try:
            conflicts = []
            
            # 1. Check for manually initiated conflicts
            self._detect_manual_conflicts(turn_number, conflicts)
            
            # 2. Check for relationship-based conflicts
            self._detect_relationship_conflicts(turn_number, conflicts)
            
            # 3. Check for target-based conflicts
            self._detect_target_conflicts(turn_number, conflicts)
            
            # 4. Check for adjacent participation
            self._detect_adjacent_participation(turn_number, conflicts)
            
            return conflicts
        except Exception as e:
            logging.error(f"Error in detect_conflicts: {str(e)}")
            return []
    
    def _detect_manual_conflicts(self, turn_number, conflicts):
        """Detect manually initiated conflicts.
        
        Args:
            turn_number (int): Current turn number.
            conflicts (list): List to append detected conflicts to.
        """
        try:
            # Find all initiate_conflict actions
            query = """
                SELECT a.id, a.piece_id, a.piece_type, a.faction_id, a.district_id, 
                       a.target_faction_id
                FROM actions a
                WHERE a.turn_number = :turn_number
                AND a.action_type = 'initiate_conflict'
            """
            
            results = self.db_manager.execute_query(query, {"turn_number": turn_number})
            
            for row in results:
                action = dict(row)
                
                # Check if the initiating piece is already in a conflict
                if self._is_piece_in_conflict(turn_number, action["piece_id"], action["piece_type"]):
                    logging.info(f"Skipping manual conflict initiation because initiating piece {action['piece_id']} is already in a conflict")
                    continue
                    
                # Check if the target faction has any available pieces in this district
                if not self._faction_has_available_pieces_in_district(turn_number, action["target_faction_id"], action["district_id"]):
                    logging.info(f"Skipping manual conflict because target faction {action['target_faction_id']} has no available pieces in district {action['district_id']}")
                    continue
                
                # Create a conflict record
                conflict_id = self._create_conflict(
                    turn_number,
                    action["district_id"],
                    "manual_initiate",
                    f"Action {action['id']}",
                    action["faction_id"],
                    action["target_faction_id"],
                    [{"piece_id": action["piece_id"], "piece_type": action["piece_type"], "faction_id": action["faction_id"]}]
                )
                
                if conflict_id:
                    # Find target faction pieces in the district
                    self._add_target_faction_pieces(conflict_id, turn_number, action["district_id"], action["target_faction_id"])
                    
                    # Mark action as in conflict
                    self._mark_action_in_conflict(action["id"], conflict_id)
                    
                    conflicts.append(conflict_id)
        except Exception as e:
            logging.error(f"Error in _detect_manual_conflicts: {str(e)}")
    
    def _detect_relationship_conflicts(self, turn_number, conflicts):
        """Detect conflicts based on negative relationships.
        
        Args:
            turn_number (int): Current turn number.
            conflicts (list): List to append detected conflicts to.
        """
        try:
            # Get all factions
            factions = self.faction_repository.find_all()
            
            # Check each district for potential conflicts
            districts = self.district_repository.find_all()
            
            for district in districts:
                # Get all pieces in this district
                query = """
                    SELECT 
                        a.piece_id, a.piece_type, a.faction_id, a.district_id, a.id as action_id
                    FROM 
                        (
                            SELECT id as piece_id, 'agent' as piece_type, faction_id, district_id
                            FROM agents
                            WHERE district_id = :district_id
                            
                            UNION
                            
                            SELECT id as piece_id, 'squadron' as piece_type, faction_id, district_id
                            FROM squadrons
                            WHERE district_id = :district_id
                        ) pieces
                    LEFT JOIN actions a ON 
                        a.piece_id = pieces.piece_id 
                        AND a.piece_type = pieces.piece_type
                        AND a.turn_number = :turn_number
                """
                
                pieces = self.db_manager.execute_query(query, {"district_id": district.id, "turn_number": turn_number})
                
                # Group pieces by faction
                pieces_by_faction = {}
                for row in pieces:
                    piece = dict(row)
                    faction_id = piece["faction_id"]
                    
                    if faction_id not in pieces_by_faction:
                        pieces_by_faction[faction_id] = []
                        
                    pieces_by_faction[faction_id].append(piece)
                
                # Skip if there are less than 2 factions with pieces in the district
                if len(pieces_by_faction) < 2:
                    continue
                
                # Create a list of faction pairs to check (each pair only once)
                faction_pairs = []
                faction_ids = list(pieces_by_faction.keys())
                
                # Generate unique faction pairs
                for i in range(len(faction_ids)):
                    for j in range(i + 1, len(faction_ids)):
                        faction_pairs.append((faction_ids[i], faction_ids[j]))
                
                logging.info(f"Checking {len(faction_pairs)} unique faction pairs in district {district.id}")
                
                # Check each unique faction pair for conflicts
                for faction_id, target_id in faction_pairs:
                    faction = self.faction_repository.find_by_id(faction_id)
                    if not faction:
                        continue
                    
                    faction_pieces = pieces_by_faction[faction_id]
                    target_pieces = pieces_by_faction[target_id]
                    
                    # Skip if both factions don't have available pieces
                    if not self._faction_has_available_pieces_in_district(turn_number, faction_id, district.id) or \
                       not self._faction_has_available_pieces_in_district(turn_number, target_id, district.id):
                        continue
                    
                    # Get the relationship between these factions
                    relationship = faction.get_relationship(target_id)
                    
                    # Check for potential conflict based on relationship - ONLY ONCE PER FACTION PAIR
                    if relationship == -1:  # Cold War
                        if random.random() < 0.10:  # 10% chance
                            logging.info(f"Triggered Cold War conflict between factions {faction_id} and {target_id} in district {district.id}")
                            self._create_relationship_conflict(
                                turn_number, district.id, faction_id, target_id, 
                                faction_pieces, target_pieces,
                                conflicts
                            )
                    elif relationship == -2:  # Hot War
                        if random.random() < 0.40:  # 40% chance
                            logging.info(f"Triggered Hot War conflict between factions {faction_id} and {target_id} in district {district.id}")
                            self._create_relationship_conflict(
                                turn_number, district.id, faction_id, target_id, 
                                faction_pieces, target_pieces,
                                conflicts
                            )
        except Exception as e:
            logging.error(f"Error in _detect_relationship_conflicts: {str(e)}")
    
    def _create_relationship_conflict(self, turn_number, district_id, faction_id, target_id, 
                                      faction_pieces, target_pieces, conflicts):
        """Create a relationship-based conflict.
        
        Args:
            turn_number (int): Current turn number.
            district_id (str): District ID.
            faction_id (str): Faction ID.
            target_id (str): Target faction ID.
            faction_pieces (list): List of pieces for the faction.
            target_pieces (list): List of pieces for the target faction.
            conflicts (list): List to append conflict ID to.
        """
        try:
            # Verify both factions have available pieces for conflict
            faction_has_available = False
            target_has_available = False
            
            # Filter out pieces already in conflicts
            available_faction_pieces = []
            for piece in faction_pieces:
                if not self._is_piece_in_conflict(turn_number, piece["piece_id"], piece["piece_type"]):
                    faction_has_available = True
                    available_faction_pieces.append(piece)
                    
            available_target_pieces = []
            for piece in target_pieces:
                if not self._is_piece_in_conflict(turn_number, piece["piece_id"], piece["piece_type"]):
                    target_has_available = True
                    available_target_pieces.append(piece)
            
            # Skip if either faction has no available pieces
            if not faction_has_available or not target_has_available:
                logging.info(f"Skipping relationship conflict creation - faction {faction_id} has available pieces: {faction_has_available}, " +
                             f"faction {target_id} has available pieces: {target_has_available}")
                return
            
            # Create conflict record
            conflict_id = self._create_conflict(
                turn_number,
                district_id,
                "relationship",
                f"Relationship conflict between {faction_id} and {target_id}",
                faction_id,
                target_id,
                available_faction_pieces + available_target_pieces
            )
            
            if conflict_id:
                # Mark all involved pieces' actions as in conflict
                for piece in available_faction_pieces + available_target_pieces:
                    if piece.get("action_id"):
                        self._mark_action_in_conflict(piece["action_id"], conflict_id)
                
                conflicts.append(conflict_id)
        except Exception as e:
            logging.error(f"Error in _create_relationship_conflict: {str(e)}")
    
    def _detect_target_conflicts(self, turn_number, conflicts):
        """Detect conflicts based on shared targets.
        
        Args:
            turn_number (int): Current turn number.
            conflicts (list): List to append detected conflicts to.
        """
        try:
            # Find take_influence actions targeting the same faction in the same district
            query = """
                SELECT 
                    a1.id as action1_id, a1.piece_id as piece1_id, a1.piece_type as piece1_type,
                    a1.faction_id as faction1_id, a1.district_id, a1.target_faction_id,
                    a2.id as action2_id, a2.piece_id as piece2_id, a2.piece_type as piece2_type,
                    a2.faction_id as faction2_id
                FROM actions a1
                JOIN actions a2 ON
                    a1.district_id = a2.district_id
                    AND a1.target_faction_id = a2.target_faction_id
                    AND a1.faction_id != a2.faction_id
                    AND a1.turn_number = a2.turn_number
                    AND a1.action_type = 'take_influence'
                    AND a2.action_type = 'take_influence'
                    AND a1.id < a2.id  -- Avoid duplicates
                WHERE a1.turn_number = :turn_number
            """
            
            results = self.db_manager.execute_query(query, {"turn_number": turn_number})
            
            for row in results:
                conflict = dict(row)
                
                # Check if either piece is already in a conflict
                piece1_in_conflict = self._is_piece_in_conflict(turn_number, conflict["piece1_id"], conflict["piece1_type"])
                piece2_in_conflict = self._is_piece_in_conflict(turn_number, conflict["piece2_id"], conflict["piece2_type"])
                
                if piece1_in_conflict or piece2_in_conflict:
                    logging.info(f"Skipping target conflict because at least one piece is already in a conflict: " +
                                 f"piece1 {conflict['piece1_id']} in conflict: {piece1_in_conflict}, " +
                                 f"piece2 {conflict['piece2_id']} in conflict: {piece2_in_conflict}")
                    continue
                
                # Create conflict record
                conflict_id = self._create_conflict(
                    turn_number,
                    conflict["district_id"],
                    "target",
                    f"Target conflict over {conflict['target_faction_id']}",
                    conflict["faction1_id"],
                    conflict["faction2_id"],
                    [
                        {"piece_id": conflict["piece1_id"], "piece_type": conflict["piece1_type"], "faction_id": conflict["faction1_id"]},
                        {"piece_id": conflict["piece2_id"], "piece_type": conflict["piece2_type"], "faction_id": conflict["faction2_id"]}
                    ]
                )
                
                if conflict_id:
                    # Mark actions as in conflict
                    self._mark_action_in_conflict(conflict["action1_id"], conflict_id)
                    self._mark_action_in_conflict(conflict["action2_id"], conflict_id)
                    
                    conflicts.append(conflict_id)
        except Exception as e:
            logging.error(f"Error in _detect_target_conflicts: {str(e)}")
    
    def _detect_adjacent_participation(self, turn_number, conflicts):
        """Detect potential adjacent district participation.
        
        Args:
            turn_number (int): Current turn number.
            conflicts (list): List of conflict IDs to check for adjacent participation.
        """
        try:
            for conflict_id in conflicts:
                # Verify this is a valid conflict with at least one piece from each side
                query = """
                    SELECT COUNT(DISTINCT faction_id) as faction_count, COUNT(*) as piece_count
                    FROM conflict_pieces
                    WHERE conflict_id = :conflict_id
                """
                
                result = self.db_manager.execute_query(query, {"conflict_id": conflict_id})
                
                # Skip if there aren't at least 2 factions or at least 2 pieces
                if not result or result[0]["faction_count"] < 2 or result[0]["piece_count"] < 2:
                    logging.info(f"Skipping adjacent participation for conflict {conflict_id} - " +
                                 f"insufficient factions ({result[0]['faction_count'] if result else 'unknown'}) or " +
                                 f"pieces ({result[0]['piece_count'] if result else 'unknown'})")
                    continue
                    
                # Get conflict information
                query = """
                    SELECT c.district_id, cf.faction_id, cf.role
                    FROM conflicts c
                    JOIN conflict_factions cf ON c.id = cf.conflict_id
                    WHERE c.id = :conflict_id
                """
                
                results = self.db_manager.execute_query(query, {"conflict_id": conflict_id})
                
                if not results:
                    continue
                    
                # Get the district ID
                district_id = results[0]["district_id"]
                
                # Get adjacent districts
                district = self.district_repository.find_by_id(district_id)
                
                if not district or not district.adjacent_districts:
                    continue
                    
                # For each faction in the conflict
                for row in results:
                    faction_id = row["faction_id"]
                    
                    # Look for squadrons in adjacent districts that belong to factions in the conflict
                    for adjacent_id in district.adjacent_districts:
                        query = """
                            SELECT 
                                s.id, s.name, s.faction_id, s.mobility,
                                a.id as action_id
                            FROM 
                                squadrons s
                            LEFT JOIN actions a ON 
                                a.piece_id = s.id 
                                AND a.piece_type = 'squadron'
                                AND a.turn_number = :turn_number
                            WHERE 
                                s.district_id = :district_id
                                AND s.faction_id = :faction_id
                        """
                        
                        squadrons = self.db_manager.execute_query(query, {
                            "district_id": adjacent_id,
                            "faction_id": faction_id,
                            "turn_number": turn_number
                        })
                        
                        for squad_row in squadrons:
                            squadron = dict(squad_row)
                            
                            # Check if squadron is already in a conflict
                            if self._is_piece_in_conflict(turn_number, squadron["id"], "squadron"):
                                logging.info(f"Skipping adjacent squadron {squadron['id']} as it's already in a conflict")
                                continue
                            
                            # Calculate if the squadron joins based on mobility
                            mobility = squadron["mobility"]
                            join_chance = mobility * 10  # 10% per mobility point
                            
                            if random.random() * 100 <= join_chance:
                                # Squadron joins the conflict
                                self._add_squadron_to_conflict(
                                    conflict_id, 
                                    squadron, 
                                    faction_id,
                                    turn_number
                                )
        except Exception as e:
            logging.error(f"Error in _detect_adjacent_participation: {str(e)}")

    # Helper method to add a squadron to a conflict
    def _add_squadron_to_conflict(self, conflict_id, squadron, faction_id, turn_number):
        """Add a squadron to a conflict as an adjacent participant.
        
        Args:
            conflict_id (str): Conflict ID.
            squadron (dict): Squadron data.
            faction_id (str): Faction ID.
            turn_number (int): Current turn number.
        """
        try:
            now = datetime.now().isoformat()
            
            # Add the squadron to the conflict
            original_action_id = squadron.get("action_id", "none")
            original_action_type = "unknown"
            
            if original_action_id and original_action_id != "none":
                action_query = """
                    SELECT action_type
                    FROM actions
                    WHERE id = :action_id
                """
                
                action_result = self.db_manager.execute_query(action_query, {
                    "action_id": original_action_id
                })
                
                if action_result:
                    original_action_type = action_result[0]["action_type"]
            
            query = """
                INSERT INTO conflict_pieces (
                    conflict_id, piece_id, piece_type, faction_id,
                    participation_type, original_action_type, original_action_id,
                    created_at, updated_at
                )
                VALUES (
                    :conflict_id, :piece_id, :piece_type, :faction_id,
                    :participation_type, :original_action_type, :original_action_id,
                    :created_at, :updated_at
                )
            """
            
            self.db_manager.execute_update(query, {
                "conflict_id": conflict_id,
                "piece_id": squadron["id"],
                "piece_type": "squadron",
                "faction_id": squadron["faction_id"],
                "participation_type": "adjacent",
                "original_action_type": original_action_type,
                "original_action_id": original_action_id,
                "created_at": now,
                "updated_at": now
            })
            
            # Mark action as in conflict if it exists
            if squadron.get("action_id"):
                self._mark_action_in_conflict(squadron["action_id"], conflict_id)
            
            return True
        except Exception as e:
            logging.error(f"Error in _add_squadron_to_conflict: {str(e)}")
            return False
    
    def _create_conflict(self, turn_number, district_id, conflict_type, detection_source, 
                         faction1_id, faction2_id, pieces=None):
        """Create a conflict record.
        
        Args:
            turn_number (int): Current turn number.
            district_id (str): District ID.
            conflict_type (str): Type of conflict.
            detection_source (str): Source of conflict detection.
            faction1_id (str): First faction ID.
            faction2_id (str): Second faction ID.
            pieces (list, optional): List of pieces involved in conflict. Defaults to None.
            
        Returns:
            str: Conflict ID if successful, None otherwise.
        """
        try:
            # Generate a unique conflict ID
            conflict_id = str(uuid.uuid4())
            
            now = datetime.now().isoformat()
            
            # Begin transaction
            with self.db_manager.connection:
                # Create conflict record
                query = """
                    INSERT INTO conflicts (
                        id, turn_number, district_id, conflict_type,
                        detection_source, resolution_status, created_at, updated_at
                    )
                    VALUES (
                        :id, :turn_number, :district_id, :conflict_type,
                        :detection_source, :resolution_status, :created_at, :updated_at
                    )
                """
                
                self.db_manager.execute_update(query, {
                    "id": conflict_id,
                    "turn_number": turn_number,
                    "district_id": district_id,
                    "conflict_type": conflict_type,
                    "detection_source": detection_source,
                    "resolution_status": "pending",
                    "created_at": now,
                    "updated_at": now
                })
                
                # Add factions to conflict
                for faction_id, role in [(faction1_id, "initiator"), (faction2_id, "target")]:
                    query = """
                        INSERT INTO conflict_factions (
                            conflict_id, faction_id, role,
                            created_at, updated_at
                        )
                        VALUES (
                            :conflict_id, :faction_id, :role,
                            :created_at, :updated_at
                        )
                    """
                    
                    self.db_manager.execute_update(query, {
                        "conflict_id": conflict_id,
                        "faction_id": faction_id,
                        "role": role,
                        "created_at": now,
                        "updated_at": now
                    })
                
                # Add pieces to conflict if provided
                if pieces:
                    for piece in pieces:
                        # Skip pieces that are already in a conflict
                        if self._is_piece_in_conflict(turn_number, piece["piece_id"], piece["piece_type"]):
                            logging.info(f"Skipping piece {piece['piece_id']} ({piece['piece_type']}) as it's already in a conflict")
                            continue
                        
                        query = """
                            INSERT INTO conflict_pieces (
                                conflict_id, piece_id, piece_type, faction_id,
                                participation_type, original_action_type, original_action_id,
                                created_at, updated_at
                            )
                            VALUES (
                                :conflict_id, :piece_id, :piece_type, :faction_id,
                                :participation_type, :original_action_type, :original_action_id,
                                :created_at, :updated_at
                            )
                        """
                        
                        # Get the piece's action details if available
                        original_action_type = "unknown"
                        original_action_id = piece.get("action_id", "none")
                        
                        if original_action_id and original_action_id != "none":
                            action_query = """
                                SELECT action_type
                                FROM actions
                                WHERE id = :action_id
                            """
                            
                            action_result = self.db_manager.execute_query(action_query, {
                                "action_id": original_action_id
                            })
                            
                            if action_result:
                                original_action_type = action_result[0]["action_type"]
                        
                        self.db_manager.execute_update(query, {
                            "conflict_id": conflict_id,
                            "piece_id": piece["piece_id"],
                            "piece_type": piece["piece_type"],
                            "faction_id": piece["faction_id"],
                            "participation_type": "direct",
                            "original_action_type": original_action_type,
                            "original_action_id": original_action_id,
                            "created_at": now,
                            "updated_at": now
                        })
                        
                        # Mark action as in conflict if it has one
                        if piece.get("action_id"):
                            self._mark_action_in_conflict(piece["action_id"], conflict_id)
            
            return conflict_id
        except Exception as e:
            logging.error(f"Error in _create_conflict: {str(e)}")
            return None
    
    def _add_target_faction_pieces(self, conflict_id, turn_number, district_id, target_faction_id):
        """Add pieces from target faction to a conflict.
        
        Args:
            conflict_id (str): Conflict ID.
            turn_number (int): Current turn number.
            district_id (str): District ID.
            target_faction_id (str): Target faction ID.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Find pieces from target faction in the district
            query = """
                SELECT 
                    a.piece_id, a.piece_type, a.id as action_id, a.action_type
                FROM 
                    (
                        SELECT id as piece_id, 'agent' as piece_type, faction_id, district_id
                        FROM agents
                        WHERE district_id = :district_id
                        AND faction_id = :faction_id
                        
                        UNION
                        
                        SELECT id as piece_id, 'squadron' as piece_type, faction_id, district_id
                        FROM squadrons
                        WHERE district_id = :district_id
                        AND faction_id = :faction_id
                    ) pieces
                LEFT JOIN actions a ON 
                    a.piece_id = pieces.piece_id 
                    AND a.piece_type = pieces.piece_type
                    AND a.turn_number = :turn_number
            """
            
            pieces = self.db_manager.execute_query(query, {
                "district_id": district_id, 
                "faction_id": target_faction_id,
                "turn_number": turn_number
            })
            
            if pieces:
                now = datetime.now().isoformat()
                
                # Add each piece to the conflict
                for row in pieces:
                    piece = dict(row)
                    
                    # Skip pieces that are already in a conflict
                    if self._is_piece_in_conflict(turn_number, piece["piece_id"], piece["piece_type"]):
                        logging.info(f"Skipping target piece {piece['piece_id']} ({piece['piece_type']}) as it's already in a conflict")
                        continue
                    
                    query = """
                        INSERT INTO conflict_pieces (
                            conflict_id, piece_id, piece_type, faction_id,
                            participation_type, original_action_type, original_action_id,
                            created_at, updated_at
                        )
                        VALUES (
                            :conflict_id, :piece_id, :piece_type, :faction_id,
                            :participation_type, :original_action_type, :original_action_id,
                            :created_at, :updated_at
                        )
                    """
                    
                    self.db_manager.execute_update(query, {
                        "conflict_id": conflict_id,
                        "piece_id": piece["piece_id"],
                        "piece_type": piece["piece_type"],
                        "faction_id": target_faction_id,
                        "participation_type": "direct",
                        "original_action_type": piece.get("action_type", "unknown"),
                        "original_action_id": piece.get("action_id", "none"),
                        "created_at": now,
                        "updated_at": now
                    })
                    
                    # Mark action as in conflict if it exists
                    if piece.get("action_id"):
                        self._mark_action_in_conflict(piece["action_id"], conflict_id)
                        
            return True
        except Exception as e:
            logging.error(f"Error in _add_target_faction_pieces: {str(e)}")
            return False
    
    def _mark_action_in_conflict(self, action_id, conflict_id):
        """Mark an action as involved in a conflict.
        
        Args:
            action_id (str): Action ID.
            conflict_id (str): Conflict ID.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            query = """
                UPDATE actions SET
                    in_conflict = 1,
                    conflict_id = :conflict_id,
                    updated_at = :updated_at
                WHERE id = :action_id
            """
            
            self.db_manager.execute_update(query, {
                "action_id": action_id,
                "conflict_id": conflict_id,
                "updated_at": datetime.now().isoformat()
            })
            
            return True
        except Exception as e:
            logging.error(f"Error in _mark_action_in_conflict: {str(e)}")
            return False
    
    def resolve_conflict(self, conflict_id, resolution_type, winning_factions=None, 
                        losing_factions=None, draw_factions=None, resolution_notes=None, 
                        resolved_by="DM"):
        """Resolve a conflict.
        
        Args:
            conflict_id (str): Conflict ID.
            resolution_type (str): Type of resolution ('win', 'loss', 'draw', 'special').
            winning_factions (list, optional): List of winning faction IDs. Defaults to None.
            losing_factions (list, optional): List of losing faction IDs. Defaults to None.
            draw_factions (list, optional): List of faction IDs that drew. Defaults to None.
            resolution_notes (str, optional): Notes about resolution. Defaults to None.
            resolved_by (str, optional): Who resolved the conflict. Defaults to "DM".
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Validate inputs
            if resolution_type not in ['win', 'loss', 'draw', 'special']:
                logging.error(f"Invalid resolution type: {resolution_type}")
                return False
                
            # Begin transaction
            with self.db_manager.connection:
                now = datetime.now().isoformat()
                
                # Update conflict record
                query = """
                    UPDATE conflicts SET
                        resolution_status = 'resolved',
                        updated_at = :updated_at
                    WHERE id = :conflict_id
                """
                
                self.db_manager.execute_update(query, {
                    "conflict_id": conflict_id,
                    "updated_at": now
                })
                
                # Create resolution record
                query = """
                    INSERT INTO conflict_resolutions (
                        conflict_id, resolution_type, resolution_notes,
                        resolved_by, resolved_at, created_at, updated_at
                    )
                    VALUES (
                        :conflict_id, :resolution_type, :resolution_notes,
                        :resolved_by, :resolved_at, :created_at, :updated_at
                    )
                """
                
                self.db_manager.execute_update(query, {
                    "conflict_id": conflict_id,
                    "resolution_type": resolution_type,
                    "resolution_notes": resolution_notes,
                    "resolved_by": resolved_by,
                    "resolved_at": now,
                    "created_at": now,
                    "updated_at": now
                })
                
                # Update faction outcomes
                if winning_factions:
                    for faction_id in winning_factions:
                        query = """
                            UPDATE conflict_factions SET
                                outcome = 'win',
                                updated_at = :updated_at
                            WHERE conflict_id = :conflict_id
                            AND faction_id = :faction_id
                        """
                        
                        self.db_manager.execute_update(query, {
                            "conflict_id": conflict_id,
                            "faction_id": faction_id,
                            "updated_at": now
                        })
                
                if losing_factions:
                    for faction_id in losing_factions:
                        query = """
                            UPDATE conflict_factions SET
                                outcome = 'loss',
                                updated_at = :updated_at
                            WHERE conflict_id = :conflict_id
                            AND faction_id = :faction_id
                        """
                        
                        self.db_manager.execute_update(query, {
                            "conflict_id": conflict_id,
                            "faction_id": faction_id,
                            "updated_at": now
                        })
                
                if draw_factions:
                    for faction_id in draw_factions:
                        query = """
                            UPDATE conflict_factions SET
                                outcome = 'draw',
                                updated_at = :updated_at
                            WHERE conflict_id = :conflict_id
                            AND faction_id = :faction_id
                        """
                        
                        self.db_manager.execute_update(query, {
                            "conflict_id": conflict_id,
                            "faction_id": faction_id,
                            "updated_at": now
                        })
                
                # Apply penalties based on outcome
                self._apply_conflict_penalties(conflict_id)
                
            return True
        except Exception as e:
            logging.error(f"Error in resolve_conflict: {str(e)}")
            return False
    
    def _apply_conflict_penalties(self, conflict_id):
        """Apply penalties to pieces based on conflict outcome.
        
        Args:
            conflict_id (str): Conflict ID.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Get conflict resolution information
            query = """
                SELECT cf.faction_id, cf.outcome
                FROM conflict_factions cf
                WHERE cf.conflict_id = :conflict_id
            """
            
            faction_outcomes = self.db_manager.execute_query(query, {"conflict_id": conflict_id})
            
            if not faction_outcomes:
                return False
                
            outcomes_by_faction = {row["faction_id"]: row["outcome"] for row in faction_outcomes}
            
            # Get pieces involved in the conflict
            query = """
                SELECT cp.piece_id, cp.piece_type, cp.faction_id, 
                       cp.original_action_id
                FROM conflict_pieces cp
                WHERE cp.conflict_id = :conflict_id
            """
            
            pieces = self.db_manager.execute_query(query, {"conflict_id": conflict_id})
            
            # Begin transaction
            with self.db_manager.connection:
                # Apply penalties based on outcome
                for row in pieces:
                    piece = dict(row)
                    faction_id = piece["faction_id"]
                    outcome = outcomes_by_faction.get(faction_id)
                    action_id = piece["original_action_id"]
                    
                    if not outcome or action_id == "none":
                        continue
                        
                    if outcome == "win":
                        # Winners proceed normally, no penalty
                        penalty = 0
                    elif outcome == "loss":
                        # Losers automatically fail their actions
                        # This is handled in action resolution
                        continue
                    elif outcome == "draw":
                        # Draws get -2 penalty
                        penalty = 2
                    
                    # Apply penalty to the action
                    query = """
                        UPDATE actions SET
                            conflict_penalty = :penalty,
                            updated_at = :updated_at
                        WHERE id = :action_id
                    """
                    
                    self.db_manager.execute_update(query, {
                        "action_id": action_id,
                        "penalty": penalty,
                        "updated_at": datetime.now().isoformat()
                    })
                    
                    # Also update the conflict piece record
                    query = """
                        UPDATE conflict_pieces SET
                            conflict_penalty = :penalty,
                            updated_at = :updated_at
                        WHERE conflict_id = :conflict_id
                        AND piece_id = :piece_id
                        AND piece_type = :piece_type
                    """
                    
                    self.db_manager.execute_update(query, {
                        "conflict_id": conflict_id,
                        "piece_id": piece["piece_id"],
                        "piece_type": piece["piece_type"],
                        "penalty": penalty,
                        "updated_at": datetime.now().isoformat()
                    })
            
            return True
        except Exception as e:
            logging.error(f"Error in _apply_conflict_penalties: {str(e)}")
            return False
    
    def _determine_quality_tier(self, roll_value):
        """Determine the quality tier based on roll value.
        
        Args:
            roll_value (int): Roll value.
            
        Returns:
            str: Quality tier.
        """
        if roll_value >= 30:
            return "legendary"
        elif roll_value >= 25:
            return "exceptional"
        elif roll_value >= 20:
            return "very_good"
        elif roll_value >= 15:
            return "good"
        elif roll_value >= 10:
            return "average"
        elif roll_value >= 5:
            return "poor"
        elif roll_value >= 1:
            return "very_poor"
        else:
            return "abysmal"

    def _is_piece_in_conflict(self, turn_number, piece_id, piece_type):
        """Check if a piece is already involved in a conflict for the given turn.
        
        Args:
            turn_number (int): Current turn number.
            piece_id (str): ID of the piece to check.
            piece_type (str): Type of the piece ('agent' or 'squadron').
            
        Returns:
            bool: True if the piece is already in a conflict, False otherwise.
        """
        try:
            query = """
                SELECT cp.conflict_id
                FROM conflict_pieces cp
                JOIN conflicts c ON cp.conflict_id = c.id
                WHERE c.turn_number = :turn_number
                AND cp.piece_id = :piece_id
                AND cp.piece_type = :piece_type
            """
            
            result = self.db_manager.execute_query(query, {
                "turn_number": turn_number,
                "piece_id": piece_id,
                "piece_type": piece_type
            })
            
            return bool(result)
        except Exception as e:
            logging.error(f"Error in _is_piece_in_conflict: {str(e)}")
            return False

    def _faction_has_available_pieces_in_district(self, turn_number, faction_id, district_id):
        """Check if a faction has any pieces in a district that aren't already in a conflict.
        
        Args:
            turn_number (int): Current turn number.
            faction_id (str): Faction ID to check.
            district_id (str): District ID to check.
            
        Returns:
            bool: True if faction has at least one available piece, False otherwise.
        """
        try:
            # Query for pieces in the district that belong to the faction
            query = """
                SELECT 
                    pieces.piece_id, pieces.piece_type
                FROM 
                    (
                        SELECT id as piece_id, 'agent' as piece_type, faction_id, district_id
                        FROM agents
                        WHERE district_id = :district_id
                        AND faction_id = :faction_id
                        
                        UNION
                        
                        SELECT id as piece_id, 'squadron' as piece_type, faction_id, district_id
                        FROM squadrons
                        WHERE district_id = :district_id
                        AND faction_id = :faction_id
                    ) pieces
            """
            
            pieces = self.db_manager.execute_query(query, {
                "district_id": district_id, 
                "faction_id": faction_id
            })
            
            # Check if any pieces are available (not already in a conflict)
            for piece in pieces:
                piece_data = dict(piece)
                if not self._is_piece_in_conflict(turn_number, piece_data["piece_id"], piece_data["piece_type"]):
                    return True
                
            return False
        except Exception as e:
            logging.error(f"Error in _faction_has_available_pieces_in_district: {str(e)}")
            return False
    
    def _calculate_enemy_piece_penalties(self, piece_id, piece_type, faction_id, district_id, turn_number):
        """Calculate penalties from enemy pieces based on relationships and proximity.
        
        Args:
            piece_id (str): ID of the piece to calculate penalties for.
            piece_type (str): Type of the piece ('agent' or 'squadron').
            faction_id (str): Faction ID of the piece.
            district_id (str): District ID where the piece is located.
            turn_number (int): Current turn number.
            
        Returns:
            tuple: Total penalty value and breakdown of penalties.
        """
        total_penalty = 0
        penalty_breakdown = []
        
        try:
            # Get district
            district = self.district_repository.find_by_id(district_id)
            if not district:
                logging.error(f"District {district_id} not found for penalty calculation")
                return total_penalty, penalty_breakdown
            
            # Get faction
            faction = self.faction_repository.find_by_id(faction_id)
            if not faction:
                logging.error(f"Faction {faction_id} not found for penalty calculation")
                return total_penalty, penalty_breakdown
            
            # Check if the piece is in a conflict (for logging purposes only, we still calculate penalties)
            is_in_conflict = self._is_piece_in_conflict(turn_number, piece_id, piece_type)
            if is_in_conflict:
                logging.info(f"Piece {piece_id} is in a conflict - will still receive enemy penalties")
            
            # ENHANCED DEBUGGING: Log faction name and district details
            logging.info(f"Calculating enemy penalties for piece {piece_id} of faction {faction.name} (ID: {faction_id}) in district {district.name} (ID: {district_id})")
            logging.info(f"District adjacent districts: {district.adjacent_districts}")
            
            # Get all factions with negative relationships
            negative_relationships = {}
            all_faction_ids = self.faction_repository.get_all_faction_ids()
            logging.info(f"Found {len(all_faction_ids)} total factions to check relationships with")
            
            for other_id in all_faction_ids:
                if other_id != faction_id:
                    other_faction = self.faction_repository.find_by_id(other_id)
                    relationship = faction.get_relationship(other_id)
                    relationship_inverse = other_faction.get_relationship(faction_id) if other_faction else None
                    logging.info(f"Relationship with {other_faction.name} (ID: {other_id}): {faction.name} → {other_faction.name} = {relationship}, {other_faction.name} → {faction.name} = {relationship_inverse}")
                    if relationship < 0:
                        negative_relationships[other_id] = relationship
            
            logging.info(f"Found {len(negative_relationships)} factions with negative relationships: {negative_relationships}")
            
            if not negative_relationships:
                logging.info(f"No negative faction relationships found, skipping enemy penalty calculation")
                return total_penalty, penalty_breakdown
            
            # Process agent penalties (agents target a single enemy piece in same district)
            # IMPORTANT: Capture the returned value from this method
            agent_penalty = self._calculate_enemy_agent_penalties(
                district_id, 
                faction_id, 
                piece_id, 
                piece_type, 
                negative_relationships, 
                turn_number, 
                total_penalty, 
                penalty_breakdown
            )
            
            # Update the total penalty with the value returned from agent penalties
            total_penalty = agent_penalty
            logging.info(f"After agent penalties: total_penalty = {total_penalty}")
            
            # Process squadron penalties (squadrons affect pieces based on mobility)
            # IMPORTANT: Capture the returned value from this method
            squadron_penalty = self._calculate_enemy_squadron_penalties(
                district, 
                faction_id, 
                piece_id, 
                piece_type, 
                negative_relationships, 
                turn_number, 
                total_penalty, 
                penalty_breakdown
            )
            
            # Update the total penalty with the value returned from squadron penalties
            total_penalty = squadron_penalty
            logging.info(f"After squadron penalties: total_penalty = {total_penalty}")
            
            # Final log of penalty calculation results
            logging.info(f"FINAL enemy penalty calculation for {piece_id}: total={total_penalty}, breakdown={penalty_breakdown}")
            logging.info(f"DEBUG: Reference check - penalty_breakdown object ID: {id(penalty_breakdown)}")
            logging.info(f"DEBUG: Final penalty values right before return: total_penalty={total_penalty}, has_penalties={len(penalty_breakdown) > 0}")
            
            return total_penalty, penalty_breakdown
        except Exception as e:
            logging.error(f"Error calculating enemy piece penalties: {str(e)}")
            logging.exception("Full traceback for enemy penalty calculation error:")
            return total_penalty, penalty_breakdown

    def _calculate_enemy_agent_penalties(self, district_id, faction_id, piece_id, piece_type, 
                                    negative_relationships, turn_number, total_penalty, penalty_breakdown):
        """Calculate penalties from enemy agents in the same district.
        
        Args:
            district_id (str): District ID where the piece is located.
            faction_id (str): Faction ID of the piece.
            piece_id (str): ID of the piece to calculate penalties for.
            piece_type (str): Type of the piece ('agent' or 'squadron').
            negative_relationships (dict): Dictionary of faction_id -> relationship value.
            turn_number (int): Current turn number.
            total_penalty (int): Running total of penalties (modified in place).
            penalty_breakdown (list): List of penalty details (modified in place).
            
        Returns:
            int: The updated total penalty amount (for verification only)
        """
        try:
            # Ensure penalty tracker is initialized
            if self.penalty_tracker is None:
                logging.warning("Penalty tracker was not initialized. Initializing now.")
                self.reset_penalty_tracker()
                
            # Record initial penalty value for verification
            initial_penalty = total_penalty
            logging.info(f"Initial agent penalty value: {initial_penalty}")
            
            # Find all enemy agents in this district that aren't in conflicts
            for enemy_id, relationship in negative_relationships.items():
                query = """
                    SELECT a.id, a.name, a.faction_id
                    FROM agents a
                    LEFT JOIN conflict_pieces cp ON
                        cp.piece_id = a.id 
                        AND cp.piece_type = 'agent'
                        AND cp.conflict_id IN (
                            SELECT id FROM conflicts WHERE turn_number = :turn_number
                        )
                    WHERE a.district_id = :district_id
                    AND a.faction_id = :enemy_id
                    AND cp.conflict_id IS NULL
                """
                
                results = self.db_manager.execute_query(query, {
                    "district_id": district_id,
                    "enemy_id": enemy_id,
                    "turn_number": turn_number
                })
                
                # Log the results for debugging
                enemy_faction = self.faction_repository.find_by_id(enemy_id)
                enemy_name = enemy_faction.name if enemy_faction else "Unknown"
                logging.info(f"Found {len(results)} enemy agents for faction {enemy_name} (ID: {enemy_id}) in district {district_id} with relationship {relationship}")
                
                # For each agent from this faction, apply penalty if not already applied
                for row in results:
                    agent = dict(row)
                    
                    # Skip if this agent already applied a penalty (using tracker)
                    if self.penalty_tracker.has_agent_applied_penalty(agent["id"]):
                        logging.info(f"Agent {agent['name']} (ID: {agent['id']}) already applied its penalty this turn, skipping")
                        continue
                    
                    # Apply penalty based on relationship
                    if relationship == -2:  # Hot war
                        penalty = 4
                        reason = "Hot War"
                    else:  # Cold war
                        penalty = 2
                        reason = "Cold War"
                    
                    # Add to running total
                    total_penalty += penalty
                    
                    # Mark this agent as having applied a penalty
                    self.penalty_tracker.mark_agent_penalty_applied(agent["id"])
                    
                    # Log the penalty being applied
                    logging.info(f"Applying {penalty} penalty from agent {agent['name']} (ID: {agent['id']}) to piece {piece_id} (relationship: {relationship})")
                    logging.info(f"Updated agent total_penalty value: {total_penalty}")
                    
                    # Add to breakdown
                    penalty_breakdown.append({
                        "source_type": "agent",
                        "source_id": agent["id"],
                        "source_name": agent["name"],
                        "faction_id": enemy_id,
                        "relationship": relationship,
                        "reason": reason,
                        "penalty": penalty
                    })
                    
                    # Agents only target one piece in total for the entire turn, so break after applying penalty
                    break
            
            # Log final penalties value for verification
            final_penalty = total_penalty
            penalty_delta = final_penalty - initial_penalty
            logging.info(f"Agent penalties summary: initial={initial_penalty}, final={final_penalty}, delta={penalty_delta}")
            
            return total_penalty  # Return updated total_penalty for verification
        except Exception as e:
            logging.error(f"Error calculating enemy agent penalties: {str(e)}")
            logging.exception("Full traceback for enemy agent penalty calculation error:")
            return total_penalty

    def _calculate_enemy_squadron_penalties(self, district, faction_id, piece_id, piece_type, 
                                    negative_relationships, turn_number, total_penalty, penalty_breakdown):
        """Calculate penalties from enemy squadrons based on mobility and proximity.
        
        Args:
            district (District): District object where the piece is located.
            faction_id (str): Faction ID of the piece.
            piece_id (str): ID of the piece to calculate penalties for.
            piece_type (str): Type of the piece ('agent' or 'squadron').
            negative_relationships (dict): Dictionary of faction_id -> relationship value.
            turn_number (int): Current turn number.
            total_penalty (int): Running total of penalties (modified in place).
            penalty_breakdown (list): List of penalty details (modified in place).
            
        Returns:
            int: The updated total penalty amount (for verification only)
        """
        try:
            # Ensure penalty tracker is initialized
            if self.penalty_tracker is None:
                logging.warning("Penalty tracker was not initialized. Initializing now.")
                self.reset_penalty_tracker()
                
            # Record initial penalty value for verification
            initial_penalty = total_penalty
            logging.info(f"Initial total_penalty value: {initial_penalty}")
            
            # Get all relevant districts (current and adjacent)
            relevant_districts = [district.id] + district.adjacent_districts
            logging.info(f"Checking for enemy squadrons in relevant districts: {relevant_districts}")
            
            # Find all enemy squadrons in relevant districts that aren't in conflicts
            for district_id in relevant_districts:
                is_adjacent = district_id != district.id
                district_name = self.district_repository.find_by_id(district_id).name if self.district_repository.find_by_id(district_id) else "Unknown"
                
                # If adjacent, need mobility 2+ to affect targets
                mobility_clause = "AND s.mobility >= 2" if is_adjacent else ""
                logging.info(f"Checking {district_name} (ID: {district_id}) - {'adjacent' if is_adjacent else 'same'} district with mobility clause: {mobility_clause}")
                
                for enemy_id, relationship in negative_relationships.items():
                    enemy_faction = self.faction_repository.find_by_id(enemy_id)
                    enemy_name = enemy_faction.name if enemy_faction else "Unknown"
                    logging.info(f"Looking for squadrons of faction {enemy_name} (ID: {enemy_id}) with relationship {relationship} in district {district_id}")
                    
                    query = f"""
                        SELECT s.id, s.name, s.faction_id, s.mobility, s.district_id
                        FROM squadrons s
                        LEFT JOIN conflict_pieces cp ON
                            cp.piece_id = s.id 
                            AND cp.piece_type = 'squadron'
                            AND cp.conflict_id IN (
                                SELECT id FROM conflicts WHERE turn_number = :turn_number
                            )
                        WHERE s.district_id = :district_id
                        AND s.faction_id = :enemy_id
                        {mobility_clause}
                        AND cp.conflict_id IS NULL
                    """
                    
                    results = self.db_manager.execute_query(query, {
                        "district_id": district_id,
                        "enemy_id": enemy_id,
                        "turn_number": turn_number
                    })
                    
                    # Log the results for debugging
                    district_type = "adjacent" if is_adjacent else "same"
                    logging.info(f"Found {len(results)} enemy squadrons for faction {enemy_name} (ID: {enemy_id}) in {district_type} district {district_name} (ID: {district_id}) with relationship {relationship}")
                    
                    for row in results:
                        squadron = dict(row)
                        logging.info(f"Squadron found: {squadron['name']} (ID: {squadron['id']}) with mobility {squadron['mobility']} in district {squadron['district_id']}")
                        
                        # Check if this squadron can still affect more pieces using the tracker
                        can_affect, slot_type = self.penalty_tracker.can_squadron_apply_penalty(
                            squadron["id"], is_adjacent, squadron["mobility"]
                        )
                        
                        # Skip if squadron can't affect this target
                        if not can_affect:
                            logging.info(f"Skipping squadron {squadron['name']} - no available slots for {'adjacent' if is_adjacent else 'same'} district")
                            continue
                            
                        logging.info(f"Squadron {squadron['name']} will use a {slot_type} slot")
                        
                        # Apply penalty based on relationship
                        if relationship == -2:  # Hot war
                            penalty = 2
                            reason = "Hot War"
                        else:  # Cold war
                            penalty = 1
                            reason = "Cold War"
                        
                        # Add to running total
                        total_penalty += penalty
                        
                        # Mark that this squadron has applied a penalty
                        self.penalty_tracker.mark_squadron_penalty_applied(squadron["id"], slot_type)
                        
                        # Log the penalty being applied
                        logging.info(f"Applying {penalty} penalty from squadron {squadron['name']} (ID: {squadron['id']}) to piece {piece_id} (relationship: {relationship})")
                        logging.info(f"Updated total_penalty value: {total_penalty}")
                        
                        # Add to breakdown
                        penalty_breakdown.append({
                            "source_type": "squadron",
                            "source_id": squadron["id"],
                            "source_name": squadron["name"],
                            "faction_id": enemy_id,
                            "relationship": relationship,
                            "reason": reason,
                            "penalty": penalty,
                            "is_adjacent": is_adjacent,
                            "mobility": squadron["mobility"],
                            "slot_type": slot_type
                        })
            
            # Log final penalties value for verification
            final_penalty = total_penalty
            penalty_delta = final_penalty - initial_penalty
            logging.info(f"Squadron penalties summary: initial={initial_penalty}, final={final_penalty}, delta={penalty_delta}")
            
            return total_penalty  # Return updated total_penalty for verification
            
        except Exception as e:
            logging.error(f"Error calculating enemy squadron penalties: {str(e)}")
            logging.exception("Full traceback for enemy squadron penalty calculation error:")
            return total_penalty

    def roll_for_action(self, action_id):
        """Roll dice for an action.
        
        Args:
            action_id (str): Action ID.
            
        Returns:
            dict: Roll results, including roll value and outcome tier.
        """
        try:
            # Get action details
            query = """
                SELECT * FROM actions
                WHERE id = :action_id
            """
            
            result = self.db_manager.execute_query(query, {"action_id": action_id})
            
            if not result:
                logging.error(f"Action {action_id} not found")
                return {"error": "Action not found"}
                
            action = dict(result[0])
            
            # Determine if this is a secondary monitoring action for a squadron
            # (squadron monitoring while assigned to a different primary action)
            roll_with_disadvantage = False
            if action["piece_type"] == "squadron" and action["action_type"] == "monitor":
                # Check if this squadron has another primary action
                squadron = self.squadron_repository.find_by_id(action["piece_id"])
                if squadron and squadron.current_task:
                    primary_action_type = squadron.current_task.get("type", "")
                    if primary_action_type and primary_action_type != "monitor":
                        roll_with_disadvantage = True
                        logging.info(f"Squadron {action['piece_id']} rolling with disadvantage for secondary monitoring")
            
            # Calculate base roll
            if roll_with_disadvantage:
                # Roll twice and take the lower result for disadvantage
                roll1 = random.randint(1, 20)  # d20
                roll2 = random.randint(1, 20)  # d20
                base_roll = min(roll1, roll2)
                logging.info(f"Rolling with disadvantage: {roll1} and {roll2}, taking {base_roll}")
            else:
                base_roll = random.randint(1, 20)  # d20
            
            # Calculate bonuses based on piece type
            if action["piece_type"] == "agent":
                # Get agent stats
                agent = self.agent_repository.find_by_id(action["piece_id"])
                if not agent:
                    logging.error(f"Agent {action['piece_id']} not found")
                    return {"error": "Agent not found"}
                    
                # Apply attribute and skill bonuses
                attribute_bonus = agent.get_attribute(action["attribute_used"]) if action["attribute_used"] else 0
                skill_bonus = agent.get_skill(action["skill_used"]) if action["skill_used"] else 0
                
                # Calculate enemy piece penalties
                enemy_penalty, penalty_breakdown = self._calculate_enemy_piece_penalties(
                    action["piece_id"],
                    action["piece_type"],
                    action["faction_id"],
                    action["district_id"],
                    action["turn_number"]
                )
                
                # Add explicit debugging logs for enemy penalties
                logging.info(f"ROLL DEBUG: Enemy penalty calculation result for agent: penalty={enemy_penalty}, has_breakdown={len(penalty_breakdown) > 0}")
                
                # Calculate roll without enemy penalty first
                roll_without_penalty = base_roll + attribute_bonus + skill_bonus + action["manual_modifier"]
                
                # Now subtract the enemy penalty
                total_roll = roll_without_penalty - enemy_penalty
                
                # Add debug log for roll components
                logging.info(f"ROLL DEBUG: Roll components for agent: base_roll={base_roll}, attribute_bonus={attribute_bonus}, skill_bonus={skill_bonus}, manual_modifier={action['manual_modifier']}, enemy_penalty={enemy_penalty}")
                logging.info(f"ROLL DEBUG: Total roll without enemy penalty: {roll_without_penalty}")
                logging.info(f"ROLL DEBUG: Final total roll after enemy penalty subtraction: {total_roll}")
                
                bonus_breakdown = {
                    "base_roll": base_roll,
                    "attribute_bonus": attribute_bonus,
                    "skill_bonus": skill_bonus,
                    "manual_modifier": action["manual_modifier"],
                    "conflict_penalty": -action["conflict_penalty"] if action["conflict_penalty"] else 0,
                    "enemy_penalty": -enemy_penalty if enemy_penalty else 0,
                    "enemy_penalty_breakdown": penalty_breakdown,
                    "with_disadvantage": roll_with_disadvantage
                }
                
            elif action["piece_type"] == "squadron":
                # Get squadron stats
                squadron = self.squadron_repository.find_by_id(action["piece_id"])
                if not squadron:
                    logging.error(f"Squadron {action['piece_id']} not found")
                    return {"error": "Squadron not found"}
                    
                # Apply aptitude bonus
                aptitude_bonus = squadron.get_aptitude(action["aptitude_used"]) if action["aptitude_used"] else 0
                
                # Calculate enemy piece penalties
                enemy_penalty, penalty_breakdown = self._calculate_enemy_piece_penalties(
                    action["piece_id"],
                    action["piece_type"],
                    action["faction_id"],
                    action["district_id"],
                    action["turn_number"]
                )
                
                # Add explicit debugging logs for enemy penalties
                logging.info(f"ROLL DEBUG: Enemy penalty calculation result for squadron: penalty={enemy_penalty}, has_breakdown={len(penalty_breakdown) > 0}")
                
                # Calculate roll without enemy penalty first
                roll_without_penalty = base_roll + aptitude_bonus + action["manual_modifier"]
                
                # Now subtract the enemy penalty
                total_roll = roll_without_penalty - enemy_penalty
                
                # Add debug log for roll components
                logging.info(f"ROLL DEBUG: Roll components for squadron: base_roll={base_roll}, aptitude_bonus={aptitude_bonus}, manual_modifier={action['manual_modifier']}, enemy_penalty={enemy_penalty}")
                logging.info(f"ROLL DEBUG: Total roll without enemy penalty: {roll_without_penalty}")
                logging.info(f"ROLL DEBUG: Final total roll after enemy penalty subtraction: {total_roll}")
                
                bonus_breakdown = {
                    "base_roll": base_roll,
                    "aptitude_bonus": aptitude_bonus,
                    "manual_modifier": action["manual_modifier"],
                    "conflict_penalty": -action["conflict_penalty"] if action["conflict_penalty"] else 0,
                    "enemy_penalty": -enemy_penalty if enemy_penalty else 0,
                    "enemy_penalty_breakdown": penalty_breakdown,
                    "with_disadvantage": roll_with_disadvantage
                }
            
            # Apply conflict penalty if any
            if action["conflict_penalty"]:
                total_roll -= action["conflict_penalty"]
            
            # For influence actions, calculate DC if not provided
            dc = action["dc"]
            if action["action_type"] in ["gain_influence", "take_influence"] and dc is None:
                from .influence import InfluenceManager
                influence_manager = InfluenceManager(
                    self.district_repository, 
                    self.faction_repository
                )
                dc = influence_manager.calculate_dc_for_gain_control(
                    action["district_id"], 
                    action["faction_id"], 
                    action["target_faction_id"]
                )
                
                # Update the action with the calculated DC
                with self.db_manager.connection:
                    update_query = """
                        UPDATE actions SET
                            dc = :dc,
                            updated_at = :updated_at
                        WHERE id = :action_id
                    """
                    self.db_manager.execute_update(update_query, {
                        "action_id": action_id,
                        "dc": dc,
                        "updated_at": datetime.now().isoformat()
                    })
            
            # Determine outcome tier based on DC (if applicable)
            if dc is not None:
                if total_roll >= (dc + 10):
                    outcome_tier = "critical_success"
                elif total_roll >= dc:
                    outcome_tier = "success"
                elif total_roll <= (dc - 10):
                    outcome_tier = "critical_failure"
                else:
                    outcome_tier = "failure"
            else:
                # For actions like monitoring with no DC
                outcome_tier = self._determine_quality_tier(total_roll)
            
            # Update action with roll result
            with self.db_manager.connection:
                query = """
                    UPDATE actions SET
                        roll_result = :roll_result,
                        outcome_tier = :outcome_tier,
                        updated_at = :updated_at
                    WHERE id = :action_id
                """
                
                self.db_manager.execute_update(query, {
                    "action_id": action_id,
                    "roll_result": total_roll,
                    "outcome_tier": outcome_tier,
                    "updated_at": datetime.now().isoformat()
                })
            
            return {
                "action_id": action_id,
                "roll_result": total_roll,
                "outcome_tier": outcome_tier,
                "bonus_breakdown": bonus_breakdown
            }
        except Exception as e:
            logging.error(f"Error in roll_for_action: {str(e)}")
            return {"error": str(e)}

    # Add helper method to the ActionManager class
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