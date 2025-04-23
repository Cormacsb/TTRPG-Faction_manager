import logging
import random
import json
import uuid
from datetime import datetime


class MonitoringManager:
    """Manages information gathering and monitoring activities."""
    
    def __init__(self, db_manager, district_repository, faction_repository, 
                 agent_repository, squadron_repository, rumor_repository):
        """Initialize the monitoring manager.
        
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
    
    def process_monitoring(self, turn_number):
        """Process all monitoring activities for the current turn.
        
        Args:
            turn_number (int): Current turn number.
            
        Returns:
            dict: Results of monitoring processing.
        """
        try:
            logging.info(f"[MONITOR_MAIN] Starting monitoring processing for turn {turn_number}")
            results = {
                "agent_monitoring": self.process_agent_monitoring(turn_number),
                "squadron_monitoring": self.process_squadron_monitoring(turn_number)
                # Passive monitoring is handled separately in the turn resolution process
            }
            logging.info(f"[MONITOR_MAIN] Monitoring results: {results}")
            return results
        except Exception as e:
            logging.error(f"Error in process_monitoring: {str(e)}")
            return {"error": str(e)}
    
    def process_agent_monitoring(self, turn_number):
        """Process monitoring by agents.
        
        Args:
            turn_number (int): Current turn number.
            
        Returns:
            dict: Results of agent monitoring.
        """
        try:
            # Find all monitoring actions by agents
            query = """
                SELECT a.id, a.piece_id, a.faction_id, a.district_id, 
                       a.manual_modifier, a.roll_result
                FROM actions a
                WHERE a.turn_number = :turn_number
                AND a.piece_type = 'agent'
                AND a.action_type = 'monitor'
            """
            
            actions = self.db_manager.execute_query(query, {"turn_number": turn_number})
            
            results = []
            
            for row in actions:
                action = dict(row)
                
                # Skip if already rolled
                if action["roll_result"] is not None:
                    continue
                    
                # Get agent
                agent = self.agent_repository.find_by_id(action["piece_id"])
                if not agent:
                    logging.error(f"Agent {action['piece_id']} not found")
                    continue
                    
                # Get district
                district = self.district_repository.find_by_id(action["district_id"])
                if not district:
                    logging.error(f"District {action['district_id']} not found")
                    continue
                
                # Determine roll modifiers based on district preferences
                attribute = district.preferred_monitor_attribute
                skill = district.preferred_monitor_skill
                
                # Update action with preferred attributes/skills
                with self.db_manager.connection:
                    query = """
                        UPDATE actions SET
                            attribute_used = :attribute,
                            skill_used = :skill,
                            updated_at = :updated_at
                        WHERE id = :action_id
                    """
                    
                    self.db_manager.execute_update(query, {
                        "action_id": action["id"],
                        "attribute": attribute,
                        "skill": skill,
                        "updated_at": datetime.now().isoformat()
                    })
                
                # Calculate roll
                roll_result = self._roll_for_monitoring(
                    action["id"], 
                    "agent", 
                    agent, 
                    attribute, 
                    skill, 
                    action["manual_modifier"]
                )
                
                if roll_result:
                    # Process monitoring results
                    monitoring_result = self._process_monitoring_result(
                        turn_number, 
                        action["faction_id"], 
                        action["district_id"], 
                        roll_result["roll_result"]
                    )
                    
                    results.append({
                        "action_id": action["id"],
                        "agent_id": action["piece_id"],
                        "faction_id": action["faction_id"],
                        "district_id": action["district_id"],
                        "roll_result": roll_result,
                        "monitoring_result": monitoring_result
                    })
            
            return results
        except Exception as e:
            logging.error(f"Error in process_agent_monitoring: {str(e)}")
            return {"error": str(e)}
    
    def process_squadron_monitoring(self, turn_number):
        """Process monitoring by squadrons.
        
        Args:
            turn_number (int): Current turn number.
            
        Returns:
            dict: Results of squadron monitoring.
        """
        try:
            # Find all squadrons with monitoring actions or in districts
            query = """
                SELECT 
                    s.id, s.faction_id, s.district_id, 
                    s.monitoring_aptitude,
                    a.id as action_id, a.action_type, a.manual_modifier,
                    a.roll_result,
                    s.assignment,
                    (SELECT COUNT(*) FROM actions a2 
                     WHERE a2.piece_id = s.id 
                     AND a2.piece_type = 'squadron'
                     AND a2.turn_number = :turn_number
                     AND a2.action_type = 'monitor'
                     AND a2.roll_result IS NOT NULL) as has_monitoring_roll
                FROM squadrons s
                LEFT JOIN actions a ON
                    a.piece_id = s.id
                    AND a.piece_type = 'squadron'
                    AND a.turn_number = :turn_number
                WHERE s.district_id IS NOT NULL
            """
            
            squadrons = self.db_manager.execute_query(query, {"turn_number": turn_number})
            
            results = []
            
            for squadron_data in squadrons:
                # Get squadron
                squadron = self.squadron_repository.find_by_id(squadron_data["id"])
                if not squadron:
                    logging.error(f"Squadron {squadron_data['id']} not found")
                    continue
                
                # Skip if already rolled for monitoring
                if squadron_data["has_monitoring_roll"] > 0:
                    continue
                
                # Get monitoring aptitude
                aptitude = squadron.monitoring_aptitude
                
                # Check if squadron has a non-monitor task
                has_non_monitor_task = False
                if squadron_data["assignment"]:
                    try:
                        assignment = json.loads(squadron_data["assignment"])
                        has_non_monitor_task = assignment.get("type") != "monitor"
                    except json.JSONDecodeError:
                        logging.error(f"Failed to parse assignment JSON for squadron {squadron_data['id']}")
                        continue
                
                # Handle primary monitoring (specific monitoring action)
                if squadron_data["action_type"] == "monitor":
                    action_id = squadron_data["action_id"]
                    manual_modifier = squadron_data["manual_modifier"] or 0
                    
                    # Update action with preferred aptitude
                    with self.db_manager.connection:
                        query = """
                            UPDATE actions SET
                                aptitude_used = :aptitude,
                                updated_at = :updated_at
                            WHERE id = :action_id
                        """
                        
                        self.db_manager.execute_update(query, {
                            "action_id": action_id,
                            "aptitude": aptitude,
                            "updated_at": datetime.now().isoformat()
                        })
                    
                    # Calculate roll
                    roll_result = self._roll_for_monitoring(
                        action_id, 
                        "squadron", 
                        squadron, 
                        None, 
                        None, 
                        manual_modifier,
                        aptitude,
                        False  # No disadvantage for primary monitoring
                    )
                    
                    if roll_result:
                        # Process monitoring results
                        monitoring_result = self._process_monitoring_result(
                            turn_number, 
                            squadron_data["faction_id"], 
                            squadron_data["district_id"], 
                            roll_result["roll_result"]
                        )
                        
                        results.append({
                            "action_id": action_id,
                            "squadron_id": squadron_data["id"],
                            "faction_id": squadron_data["faction_id"],
                            "district_id": squadron_data["district_id"],
                            "monitoring_type": "primary",
                            "roll_result": roll_result,
                            "monitoring_result": monitoring_result
                        })
                
                # Handle secondary monitoring (for squadrons with non-monitor tasks)
                if has_non_monitor_task:
                    # For secondary monitoring, create a virtual action
                    monitoring_action_id = str(uuid.uuid4())
                    
                    # Calculate roll with disadvantage
                    roll_result = self._roll_for_monitoring(
                        monitoring_action_id, 
                        "squadron", 
                        squadron, 
                        None, 
                        None, 
                        0,  # No manual modifier for secondary monitoring
                        aptitude,
                        True  # Use disadvantage for secondary monitoring
                    )
                    
                    if roll_result:
                        # Process monitoring results
                        monitoring_result = self._process_monitoring_result(
                            turn_number, 
                            squadron_data["faction_id"], 
                            squadron_data["district_id"], 
                            roll_result["roll_result"]
                        )
                        
                        result_entry = {
                            "action_id": monitoring_action_id,
                            "squadron_id": squadron_data["id"],
                            "faction_id": squadron_data["faction_id"],
                            "district_id": squadron_data["district_id"],
                            "monitoring_type": "secondary",
                            "roll_result": roll_result,
                            "monitoring_result": monitoring_result
                        }
                        
                        results.append(result_entry)
            
            return results
        except Exception as e:
            logging.error(f"Error in process_squadron_monitoring: {str(e)}")
            return {"error": str(e)}
    
    def process_passive_monitoring(self, turn_number):
        """Process passive monitoring for factions with significant influence.
        
        Args:
            turn_number (int): Current turn number.
            
        Returns:
            dict: Results of passive monitoring.
        """
        try:
            # Get all districts
            districts = self.district_repository.find_all()
            
            results = []
            
            for district in districts:
                # Find factions with ≥4 influence in this district
                qualifying_factions = []
                
                for faction_id, influence in district.faction_influence.items():
                    if influence >= 4:
                        qualifying_factions.append(faction_id)
                
                # Process passive monitoring for each qualifying faction
                for faction_id in qualifying_factions:
                    # Get faction
                    faction = self.faction_repository.find_by_id(faction_id)
                    if not faction:
                        logging.error(f"Faction {faction_id} not found")
                        continue
                    
                    # Calculate influence bonus: (Influence ÷ 2) + Faction monitoring bonus
                    influence = district.get_faction_influence(faction_id)
                    influence_bonus = (influence // 2) + faction.monitoring_bonus
                    
                    # Roll for passive monitoring
                    base_roll = random.randint(1, 20)  # d20
                    total_roll = base_roll + influence_bonus
                    
                    # Determine quality tier
                    quality_tier = self._determine_quality_tier(total_roll)
                    
                    # Process monitoring results
                    monitoring_result = self._process_monitoring_result(
                        turn_number, 
                        faction_id, 
                        district.id, 
                        total_roll
                    )
                    
                    results.append({
                        "faction_id": faction_id,
                        "district_id": district.id,
                        "influence": influence,
                        "influence_bonus": influence_bonus,
                        "base_roll": base_roll,
                        "total_roll": total_roll,
                        "quality_tier": quality_tier,
                        "monitoring_result": monitoring_result
                    })
            
            return results
        except Exception as e:
            logging.error(f"Error in process_passive_monitoring: {str(e)}")
            return {"error": str(e)}
    
    def _roll_for_monitoring(self, action_id, piece_type, piece, attribute=None, skill=None, 
                        manual_modifier=0, aptitude=None, with_disadvantage=False):
        try:
            # For monitoring actions that are registered in the database, use ActionManager
            action_exists = self.db_manager.execute_query(
                "SELECT 1 FROM actions WHERE id = :action_id",
                {"action_id": action_id}
            )
            
            if action_exists:
                # Get action details to ensure all penalties and modifiers are applied
                from .action import ActionManager
                action_manager = ActionManager(
                    self.db_manager,
                    self.district_repository,
                    self.faction_repository,
                    self.agent_repository,
                    self.squadron_repository
                )
                
                # Use the roll_for_action method which applies all modifiers
                roll_result = action_manager.roll_for_action(action_id)
                if "error" not in roll_result:
                    return roll_result
            
            # Fallback or for virtual monitoring actions
            # Calculate base roll
            if with_disadvantage:
                # Roll twice and take the lower result for disadvantage
                roll1 = random.randint(1, 20)  # d20
                roll2 = random.randint(1, 20)  # d20
                base_roll = min(roll1, roll2)
            else:
                base_roll = random.randint(1, 20)  # d20
            
            # Calculate bonuses based on piece type
            if piece_type == "agent":
                # Apply attribute and skill bonuses
                attribute_bonus = piece.get_attribute(attribute) if attribute else 0
                skill_bonus = piece.get_skill(skill) if skill else 0
                
                # Calculate total roll
                total_roll = base_roll + attribute_bonus + skill_bonus + manual_modifier
                
                bonus_breakdown = {
                    "base_roll": base_roll,
                    "attribute_bonus": attribute_bonus,
                    "skill_bonus": skill_bonus,
                    "manual_modifier": manual_modifier,
                    "with_disadvantage": with_disadvantage
                }
                
            elif piece_type == "squadron":
                # Apply aptitude bonus
                aptitude_bonus = piece.get_aptitude(aptitude) if aptitude else 0
                
                # Calculate total roll
                total_roll = base_roll + aptitude_bonus + manual_modifier
                
                bonus_breakdown = {
                    "base_roll": base_roll,
                    "aptitude_bonus": aptitude_bonus,
                    "manual_modifier": manual_modifier,
                    "with_disadvantage": with_disadvantage
                }
            
            # Determine quality tier
            quality_tier = self._determine_quality_tier(total_roll)
            
            # Update action with roll result if it exists
            if action_exists:
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
                        "outcome_tier": quality_tier,
                        "updated_at": datetime.now().isoformat()
                    })
            
            return {
                "action_id": action_id,
                "roll_result": total_roll,
                "quality_tier": quality_tier,
                "bonus_breakdown": bonus_breakdown
            }
        except Exception as e:
            logging.error(f"Error in _roll_for_monitoring: {str(e)}")
            return None
    
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
    
    def _process_monitoring_result(self, turn_number, faction_id, district_id, roll_result):
        """Process the results of a monitoring action.
        
        Args:
            turn_number (int): Current turn number.
            faction_id (str): Faction ID.
            district_id (str): District ID.
            roll_result (int): Roll result.
            
        Returns:
            dict: Monitoring results.
        """
        try:
            logging.info(f"[MONITOR_RESULT] Processing monitoring result - Turn: {turn_number}, Faction: {faction_id}, District: {district_id}, Roll: {roll_result}")
            # Get district and faction
            district = self.district_repository.find_by_id(district_id)
            faction = self.faction_repository.find_by_id(faction_id)
            
            if not district or not faction:
                logging.error(f"District {district_id} or faction {faction_id} not found")
                return {"error": "District or faction not found"}
            
            # Determine quality tier from roll result
            quality_tier = self._determine_quality_tier(roll_result)
            
            # Initialize RNG seed based on roll result for deterministic randomization
            random.seed(f"{turn_number}-{faction_id}-{district_id}-{roll_result}")
            
            # Process faction detection and influence accuracy
            perceived_influences = self._process_faction_detection(district, quality_tier)
            
            # Process stronghold detection
            perceived_strongholds = self._process_stronghold_detection(district, quality_tier, perceived_influences)
            
            # Process phantom faction detection
            phantom_detections = self._process_phantom_detection(district, quality_tier)
            
            # Adjust total influence to not exceed 10
            perceived_influences = self._adjust_total_influence(perceived_influences, phantom_detections)
            
            # Process district modifier discovery
            district_modifier = self._process_district_modifier_discovery(district, roll_result)
            
            # Process rumor discovery
            discovered_rumors = self._process_rumor_discovery(district, faction_id, roll_result, turn_number)
            
            # Calculate confidence rating
            confidence_rating = self._calculate_confidence_rating(roll_result, quality_tier)
            
            # Create monitoring report
            report_id = self._create_monitoring_report(
                turn_number, faction_id, district_id, 
                perceived_influences, phantom_detections, 
                district_modifier, discovered_rumors, 
                confidence_rating, perceived_strongholds
            )
            
            logging.info(f"[MONITOR_RESULT] Created monitoring report {report_id}")
            
            # Update faction's perceived influence
            for target_faction_id, value in perceived_influences.items():
                faction.set_perceived_influence(district_id, target_faction_id, value, turn_number)
                logging.info(f"[MONITOR_RESULT] Updated perceived influence for faction {target_faction_id}: {value}")
            
            # Update faction's perceived strongholds
            for target_faction_id, has_stronghold in perceived_strongholds.items():
                faction.set_perceived_stronghold(district_id, target_faction_id, has_stronghold, turn_number)
                logging.info(f"[MONITOR_RESULT] Updated perceived stronghold for faction {target_faction_id}: {has_stronghold}")
            
            for phantom in phantom_detections:
                faction.set_perceived_influence(district_id, phantom["faction_id"], phantom["perceived_influence"], turn_number)
                logging.info(f"[MONITOR_RESULT] Updated phantom influence for faction {phantom['faction_id']}: {phantom['perceived_influence']}")
            
            # Return monitoring results
            result = {
                "report_id": report_id,
                "perceived_influences": perceived_influences,
                "perceived_strongholds": perceived_strongholds,
                "phantom_detections": phantom_detections,
                "district_modifier": district_modifier,
                "discovered_rumors": discovered_rumors,
                "confidence_rating": confidence_rating
            }
            logging.info(f"[MONITOR_RESULT] Returning result: {result}")
            return result
        except Exception as e:
            logging.error(f"Error in _process_monitoring_result: {str(e)}")
            return {"error": str(e)}
    
    def _process_faction_detection(self, district, quality_tier):
        """Process faction detection based on quality tier.
        
        Args:
            district: District instance.
            quality_tier (str): Quality tier of monitoring roll.
            
        Returns:
            dict: Perceived influence values by faction ID.
        """
        try:
            perceived_influences = {}
            
            # Process each faction in district based on quality tier rules
            for faction_id, actual_influence in district.faction_influence.items():
                # Check if faction is detected based on quality tier
                detected = False
                
                if quality_tier == "legendary" or quality_tier == "exceptional":
                    # Always detect all factions
                    detected = True
                elif quality_tier == "very_good":
                    # 100% detection for factions with influence ≥2
                    # 95% detection for factions with influence 1
                    if actual_influence >= 2:
                        detected = True
                    elif actual_influence == 1:
                        detected = random.random() < 0.95
                elif quality_tier == "good":
                    # 100% detection for factions with influence ≥4
                    # 90% detection for factions with influence 2-3
                    # 75% detection for factions with influence 1
                    if actual_influence >= 4:
                        detected = True
                    elif actual_influence in [2, 3]:
                        detected = random.random() < 0.90
                    elif actual_influence == 1:
                        detected = random.random() < 0.75
                elif quality_tier == "average":
                    # 95% detection for factions with influence ≥6
                    # 80% detection for factions with influence 3-5
                    # 60% detection for factions with influence 2
                    # 0% detection for factions with influence 1
                    if actual_influence >= 6:
                        detected = random.random() < 0.95
                    elif actual_influence in [3, 4, 5]:
                        detected = random.random() < 0.80
                    elif actual_influence == 2:
                        detected = random.random() < 0.60
                elif quality_tier == "poor":
                    # 90% detection for factions with influence ≥7
                    # 70% detection for factions with influence 4-6
                    # 50% detection for factions with influence 2-3
                    # 0% detection for factions with influence 1
                    if actual_influence >= 7:
                        detected = random.random() < 0.90
                    elif actual_influence in [4, 5, 6]:
                        detected = random.random() < 0.70
                    elif actual_influence in [2, 3]:
                        detected = random.random() < 0.50
                elif quality_tier == "very_poor":
                    # 80% detection for factions with influence ≥8
                    # 60% detection for factions with influence 5-7
                    # 40% detection for factions with influence 3-4
                    # 0% detection for factions with influence 1-2
                    if actual_influence >= 8:
                        detected = random.random() < 0.80
                    elif actual_influence in [5, 6, 7]:
                        detected = random.random() < 0.60
                    elif actual_influence in [3, 4]:
                        detected = random.random() < 0.40
                elif quality_tier == "abysmal":
                    # 60% detection for factions with influence ≥9
                    # 40% detection for factions with influence 6-8
                    # 20% detection for factions with influence 4-5
                    # 0% detection for factions with influence 1-3
                    if actual_influence >= 9:
                        detected = random.random() < 0.60
                    elif actual_influence in [6, 7, 8]:
                        detected = random.random() < 0.40
                    elif actual_influence in [4, 5]:
                        detected = random.random() < 0.20
                
                # If detected, calculate perceived influence
                if detected:
                    perceived_value = self._calculate_perceived_influence(actual_influence, quality_tier)
                    perceived_influences[faction_id] = perceived_value
            
            return perceived_influences
        except Exception as e:
            logging.error(f"Error in _process_faction_detection: {str(e)}")
            return {}
    
    def _calculate_perceived_influence(self, actual_influence, quality_tier):
        """Calculate perceived influence based on quality tier.
        
        Args:
            actual_influence (int): Actual influence value.
            quality_tier (str): Quality tier of monitoring roll.
            
        Returns:
            int: Perceived influence value.
        """
        try:
            # Error distribution based on quality tier
            if quality_tier == "legendary":
                # 100% accuracy (exact values)
                perceived_value = actual_influence
            
            elif quality_tier == "exceptional":
                # 90% chance of exact value
                # Remainder: ±1 error (weighted toward true value)
                if random.random() < 0.90:
                    perceived_value = actual_influence
                else:
                    error = random.choice([-1, 1])
                    # Ensure result is valid (1-10)
                    perceived_value = max(1, min(10, actual_influence + error))
            
            elif quality_tier == "very_good":
                # Accuracy depends on influence level
                if actual_influence >= 5:
                    if random.random() < 0.80:
                        perceived_value = actual_influence
                    else:
                        error = random.choice([-1, 1])
                        perceived_value = max(1, min(10, actual_influence + error))
                elif actual_influence in [2, 3, 4]:
                    if random.random() < 0.75:
                        perceived_value = actual_influence
                    else:
                        error = random.choice([-1, 1])
                        perceived_value = max(1, min(10, actual_influence + error))
                else:  # influence 1
                    if random.random() < 0.70:
                        perceived_value = actual_influence
                    else:
                        perceived_value = 2  # Only can go up
            
            elif quality_tier == "good":
                # More error, still weighted toward true value
                if actual_influence >= 5:
                    exact_chance = 0.65
                    small_error_chance = 0.30
                    # Remainder is larger error
                elif actual_influence in [2, 3, 4]:
                    exact_chance = 0.55
                    small_error_chance = 0.35
                    # Remainder is larger error
                else:  # influence 1
                    exact_chance = 0.45
                    small_error_chance = 0.45
                    # Remainder is larger error
                
                roll = random.random()
                if roll < exact_chance:
                    perceived_value = actual_influence
                elif roll < (exact_chance + small_error_chance):
                    error = random.choice([-1, 1])
                    perceived_value = max(1, min(10, actual_influence + error))
                else:
                    error = random.choice([-2, 2])
                    perceived_value = max(1, min(10, actual_influence + error))
            
            elif quality_tier == "average":
                # Significant error possible
                if actual_influence >= 6:
                    exact_chance = 0.40
                    small_error_chance = 0.35
                    medium_error_chance = 0.20
                    # Remainder is larger error
                elif actual_influence in [3, 4, 5]:
                    exact_chance = 0.30
                    small_error_chance = 0.40
                    medium_error_chance = 0.25
                    # Remainder is larger error
                else:  # influence 2
                    exact_chance = 0.20
                    small_error_chance = 0.45
                    medium_error_chance = 0.30
                    # Remainder is larger error
                
                roll = random.random()
                if roll < exact_chance:
                    perceived_value = actual_influence
                elif roll < (exact_chance + small_error_chance):
                    error = random.choice([-1, 1])
                    perceived_value = max(1, min(10, actual_influence + error))
                elif roll < (exact_chance + small_error_chance + medium_error_chance):
                    error = random.choice([-2, 2])
                    perceived_value = max(1, min(10, actual_influence + error))
                else:
                    error = random.choice([-3, 3])
                    perceived_value = max(1, min(10, actual_influence + error))
            
            elif quality_tier == "poor":
                # Major magnitude errors possible
                if actual_influence >= 7:
                    exact_chance = 0.20
                    small_error_chance = 0.30
                    # Remainder is larger error
                elif actual_influence in [4, 5, 6]:
                    exact_chance = 0.10
                    small_error_chance = 0.30
                    # Remainder is larger error
                else:  # influence 2-3
                    exact_chance = 0.05
                    small_error_chance = 0.25
                    # Remainder is larger error
                
                roll = random.random()
                if roll < exact_chance:
                    perceived_value = actual_influence
                elif roll < (exact_chance + small_error_chance):
                    error = random.randint(-2, 2)  # Larger range for small error
                    perceived_value = max(1, min(10, actual_influence + error))
                else:
                    error = random.randint(-4, 4)  # Potentially major error
                    perceived_value = max(1, min(10, actual_influence + error))
                
                # Additional chance for high influence to appear low or vice versa
                if actual_influence >= 6 and random.random() < 0.40:
                    perceived_value = random.randint(1, 4)
                elif actual_influence <= 4 and random.random() < 0.40:
                    perceived_value = random.randint(6, 10)
            
            elif quality_tier == "very_poor":
                # Severe magnitude errors common
                exact_chance = 0.05
                small_error_chance = 0.15
                medium_error_chance = 0.30
                # Remainder is extreme error
                
                roll = random.random()
                if roll < exact_chance:
                    perceived_value = actual_influence
                elif roll < (exact_chance + small_error_chance):
                    error = random.randint(-2, 2)
                    perceived_value = max(1, min(10, actual_influence + error))
                elif roll < (exact_chance + small_error_chance + medium_error_chance):
                    error = random.randint(-4, 4)
                    perceived_value = max(1, min(10, actual_influence + error))
                else:
                    error = random.randint(-5, 5)
                    perceived_value = max(1, min(10, actual_influence + error))
                
                # Higher chance for high influence to appear low or vice versa
                if actual_influence >= 6 and random.random() < 0.60:
                    perceived_value = random.randint(1, 4)
                elif actual_influence <= 4 and random.random() < 0.60:
                    perceived_value = random.randint(6, 10)
            
            elif quality_tier == "abysmal":
                # Information is effectively random
                # Very small chance of being close to accurate
                if random.random() < 0.05:
                    error = random.randint(-3, 3)
                    perceived_value = max(1, min(10, actual_influence + error))
                elif random.random() < 0.15:
                    error = random.randint(-5, 5)
                    perceived_value = max(1, min(10, actual_influence + error))
                else:
                    perceived_value = random.randint(1, 10)
            
            else:
                # Default case
                perceived_value = actual_influence
            
            return perceived_value
        except Exception as e:
            logging.error(f"Error in _calculate_perceived_influence: {str(e)}")
            return actual_influence
    
    def _process_phantom_detection(self, district, quality_tier):
        """Process phantom faction detection.
        
        Args:
            district: District instance.
            quality_tier (str): Quality tier of monitoring roll.
            
        Returns:
            list: List of phantom detections.
        """
        try:
            phantom_detections = []
            
            # Determine if phantom faction(s) will be detected
            phantom_chance = self._get_phantom_detection_chance(quality_tier)
            
            if random.random() >= phantom_chance:
                return []  # No phantom detections
            
            # Determine number of phantom factions
            num_phantoms = 1  # Default
            phantom_num_roll = random.random()
            if phantom_num_roll > 0.70:  # 30% chance for more phantoms
                if phantom_num_roll > 0.95:  # 5% chance for 3
                    num_phantoms = 3
                else:  # 25% chance for 2
                    num_phantoms = 2
            
            # Get all factions
            query = "SELECT id FROM factions"
            all_factions = self.db_manager.execute_query(query)
            all_faction_ids = [row["id"] for row in all_factions]
            
            # Filter out factions already in the district
            present_faction_ids = list(district.faction_influence.keys())
            eligible_faction_ids = [f for f in all_faction_ids if f not in present_faction_ids]
            
            if not eligible_faction_ids:
                return []  # No eligible factions for phantom detection
            
            # Weight factions in adjacent districts higher
            adjacent_faction_ids = set()
            for adjacent_id in district.adjacent_districts:
                adjacent_district = self.district_repository.find_by_id(adjacent_id)
                if adjacent_district:
                    adjacent_faction_ids.update(adjacent_district.faction_influence.keys())
            
            # Generate phantom detections
            for _ in range(num_phantoms):
                if not eligible_faction_ids:
                    break  # No more eligible factions
                
                # Weight adjacent factions higher
                weights = []
                for faction_id in eligible_faction_ids:
                    if faction_id in adjacent_faction_ids:
                        weight = self._get_adjacent_weight_multiplier(quality_tier)
                    else:
                        weight = 1.0
                    weights.append(weight)
                
                # Select a phantom faction with weighted probability
                phantom_faction_id = random.choices(eligible_faction_ids, weights=weights, k=1)[0]
                
                # Determine phantom influence value
                phantom_influence = self._get_phantom_influence_value(quality_tier)
                
                # Add phantom detection
                phantom_detections.append({
                    "faction_id": phantom_faction_id,
                    "perceived_influence": phantom_influence
                })
                
                # Remove from eligible factions for next phantom
                eligible_faction_ids.remove(phantom_faction_id)
            
            return phantom_detections
        except Exception as e:
            logging.error(f"Error in _process_phantom_detection: {str(e)}")
            return []
    
    def _get_phantom_detection_chance(self, quality_tier):
        """Get the chance of detecting a phantom faction.
        
        Args:
            quality_tier (str): Quality tier of monitoring roll.
            
        Returns:
            float: Chance of phantom detection (0.0-1.0).
        """
        if quality_tier == "legendary" or quality_tier == "exceptional":
            return 0.0  # No phantom detections
        elif quality_tier == "very_good":
            return 0.05
        elif quality_tier == "good":
            return 0.15
        elif quality_tier == "average":
            return 0.25
        elif quality_tier == "poor":
            return 0.35
        elif quality_tier == "very_poor":
            return 0.45
        elif quality_tier == "abysmal":
            return 0.60
        else:
            return 0.0
    
    def _get_adjacent_weight_multiplier(self, quality_tier):
        """Get the weight multiplier for adjacent district factions.
        
        Args:
            quality_tier (str): Quality tier of monitoring roll.
            
        Returns:
            float: Weight multiplier.
        """
        if quality_tier == "good":
            return 3.0  # Heavily weighted toward adjacent factions
        elif quality_tier == "average":
            return 2.0  # Moderately weighted
        elif quality_tier == "poor":
            return 1.5  # Slightly weighted
        elif quality_tier == "very_poor" or quality_tier == "abysmal":
            return 1.1  # Negligibly weighted
        else:
            return 1.0  # No weighting
    
    def _get_phantom_influence_value(self, quality_tier):
        """Get a phantom influence value based on quality tier.
        
        Args:
            quality_tier (str): Quality tier of monitoring roll.
            
        Returns:
            int: Phantom influence value (1-10).
        """
        if quality_tier == "very_good":
            # If phantom detected, influence value is 1 (80% chance) or 2 (20% chance)
            return 1 if random.random() < 0.80 else 2
        
        elif quality_tier == "good":
            # If phantom detected, influence values: 1 (70% chance), 2 (25% chance), or 3 (5% chance)
            roll = random.random()
            if roll < 0.70:
                return 1
            elif roll < 0.95:
                return 2
            else:
                return 3
        
        elif quality_tier == "average":
            # If phantom detected, influence values: 1 (50% chance), 2 (30% chance), 3 (15% chance), or 4 (5% chance)
            roll = random.random()
            if roll < 0.50:
                return 1
            elif roll < 0.80:
                return 2
            elif roll < 0.95:
                return 3
            else:
                return 4
        
        elif quality_tier == "poor":
            # If phantom detected, influence values: 1-2 (60% chance), 3-4 (30% chance), or 5-6 (10% chance)
            roll = random.random()
            if roll < 0.60:
                return random.randint(1, 2)
            elif roll < 0.90:
                return random.randint(3, 4)
            else:
                return random.randint(5, 6)
        
        elif quality_tier == "very_poor":
            # If phantom detected, influence values: 1-3 (50% chance), 4-6 (40% chance), or 7-8 (10% chance)
            roll = random.random()
            if roll < 0.50:
                return random.randint(1, 3)
            elif roll < 0.90:
                return random.randint(4, 6)
            else:
                return random.randint(7, 8)
        
        elif quality_tier == "abysmal":
            # If phantom detected, influence values uniformly random between 1-10
            return random.randint(1, 10)
        
        else:
            return 1  # Default case
    
    def _adjust_total_influence(self, perceived_influences, phantom_detections):
        """Adjust total perceived influence to not exceed 10.
        
        Args:
            perceived_influences (dict): Perceived influence values by faction ID.
            phantom_detections (list): List of phantom detections.
            
        Returns:
            dict: Adjusted perceived influence values.
        """
        try:
            # Add phantom detections to perceived influences
            adjusted_influences = perceived_influences.copy()
            for phantom in phantom_detections:
                adjusted_influences[phantom["faction_id"]] = phantom["perceived_influence"]
            
            # Calculate total influence
            total_influence = sum(adjusted_influences.values())
            
            # If total exceeds 10, adjust values
            if total_influence > 10:
                excess = total_influence - 10
                
                # Randomly select factions to reduce, weighted by their influence
                while excess > 0:
                    # Create weighted list of faction IDs
                    weighted_factions = []
                    for faction_id, influence in adjusted_influences.items():
                        if influence > 1:  # Ensure no reduction below 1
                            weighted_factions.extend([faction_id] * influence)
                    
                    if not weighted_factions:
                        break  # No more factions can be reduced
                    
                    # Select random faction to reduce
                    faction_to_reduce = random.choice(weighted_factions)
                    
                    # Reduce influence by 1
                    adjusted_influences[faction_to_reduce] -= 1
                    excess -= 1
            
            return adjusted_influences
        except Exception as e:
            logging.error(f"Error in _adjust_total_influence: {str(e)}")
            return perceived_influences
    
    def _process_district_modifier_discovery(self, district, roll_result):
        """Process the discovery of district DC modifiers.
        
        Args:
            district: District instance.
            roll_result (int): Roll result.
            
        Returns:
            dict: District modifier discovery result.
        """
        try:
            modifier = district.weekly_dc_modifier
            
            # No modifier to discover
            if modifier == 0:
                # Special case for neutral state
                if roll_result >= 30:
                    chance_exact = 0.95
                elif roll_result >= 25:
                    chance_exact = 0.85
                elif roll_result >= 20:
                    chance_exact = 0.70
                elif roll_result >= 15:
                    chance_exact = 0.50
                elif roll_result >= 10:
                    chance_exact = 0.30
                elif roll_result >= 5:
                    chance_exact = 0.15
                elif roll_result >= 1:
                    chance_exact = 0.05
                else:
                    chance_exact = 0.0
                
                if random.random() < chance_exact:
                    return {
                        "value": 0,
                        "direction_only": False
                    }
                else:
                    return None  # No discovery
            
            # Modifier magnitude affects discovery chance
            modifier_magnitude = abs(modifier)
            
            # For ±2 modifiers (strongest effect, most noticeable)
            if modifier_magnitude == 2:
                if roll_result >= 15:
                    chance_exact = 1.0  # 100% chance for exact value
                    chance_direction = 0.0
                elif roll_result >= 10:
                    chance_exact = 0.60
                    chance_direction = 0.30
                elif roll_result >= 5:
                    chance_exact = 0.0
                    chance_direction = 0.40
                elif roll_result >= 1:
                    chance_exact = 0.0
                    chance_direction = 0.20
                else:
                    chance_exact = 0.0
                    chance_direction = 0.10
            
            # For ±1 modifiers (moderate effect, somewhat subtle)
            else:  # modifier_magnitude == 1
                if roll_result >= 30:
                    chance_exact = 1.0
                    chance_direction = 0.0
                elif roll_result >= 25:
                    chance_exact = 0.95
                    chance_direction = 0.05
                elif roll_result >= 20:
                    chance_exact = 0.90
                    chance_direction = 0.10
                elif roll_result >= 15:
                    chance_exact = 0.70
                    chance_direction = 0.20
                elif roll_result >= 10:
                    chance_exact = 0.40
                    chance_direction = 0.40
                elif roll_result >= 5:
                    chance_exact = 0.0
                    chance_direction = 0.20
                elif roll_result >= 1:
                    chance_exact = 0.0
                    chance_direction = 0.10
                else:
                    chance_exact = 0.0
                    chance_direction = 0.05
            
            # Roll for discovery
            roll = random.random()
            
            if roll < chance_exact:
                # Discovered exact value
                return {
                    "value": modifier,
                    "direction_only": False
                }
            elif roll < (chance_exact + chance_direction):
                # Discovered direction only
                direction = "positive" if modifier > 0 else "negative"
                
                # Check for false information
                false_info_chance = 0.0
                if roll_result >= 15:
                    false_info_chance = 0.0
                elif roll_result >= 10:
                    false_info_chance = 0.05
                elif roll_result >= 5:
                    false_info_chance = 0.15
                elif roll_result >= 1:
                    false_info_chance = 0.30
                else:
                    false_info_chance = 0.50
                
                if random.random() < false_info_chance:
                    # Generate false direction
                    direction = "negative" if modifier > 0 else "positive"
                
                return {
                    "direction": direction,
                    "direction_only": True
                }
            else:
                # No discovery
                return None
        except Exception as e:
            logging.error(f"Error in _process_district_modifier_discovery: {str(e)}")
            return None
    
    def _process_rumor_discovery(self, district, faction_id, roll_result, turn_number):
        """Process the discovery of rumors in a district.
        
        Args:
            district: District instance.
            faction_id (str): Faction ID.
            roll_result (int): Roll result.
            turn_number (int): Current turn number.
            
        Returns:
            list: List of discovered rumor IDs.
        """
        try:
            logging.info(f"Processing rumor discovery for district {district.id}, faction {faction_id}, roll {roll_result}")
            
            # Get all rumors in the district
            query = """
                SELECT id, discovery_dc, rumor_text
                FROM district_rumors
                WHERE district_id = :district_id
            """
            
            rumors = self.db_manager.execute_query(query, {"district_id": district.id})
            
            if not rumors:
                logging.info(f"No rumors found in district {district.id}")
                return []
            
            # Get list of rumors already known by the faction
            query = """
                SELECT rumor_id
                FROM faction_known_rumors
                WHERE faction_id = :faction_id
            """
            
            known_rumors = self.db_manager.execute_query(query, {"faction_id": faction_id})
            known_rumor_ids = [row["rumor_id"] for row in known_rumors]
            
            logging.info(f"Found {len(known_rumors)} rumors already known by faction {faction_id}")
            
            # Filter out already known rumors
            unknown_rumors = [rumor for rumor in rumors if rumor["id"] not in known_rumor_ids]
            
            if not unknown_rumors:
                logging.info(f"All rumors already known by faction {faction_id}")
                return []  # All rumors already known
                
            logging.info(f"Found {len(unknown_rumors)} unknown rumors")
            
            discovered_rumor_ids = []
            
            # Check for high-beat discoveries (roll beats DC by 7+)
            high_beat_rumors = []
            for rumor in unknown_rumors:
                dc = rumor["discovery_dc"]
                margin = roll_result - dc
                if margin >= 7:
                    logging.info(f"Roll {roll_result} beats rumor DC {dc} by {margin} (≥7), marking as discovered: {rumor['id']}")
                    high_beat_rumors.append(rumor)
                    
                    # Mark as discovered
                    self.rumor_repository.mark_as_known(rumor["id"], faction_id, turn_number)
                    discovered_rumor_ids.append(rumor["id"])
            
            logging.info(f"Discovered {len(high_beat_rumors)} high-beat rumors: {discovered_rumor_ids}")
            
            # Look for beatable rumors with margin <7 (excluding already discovered high-beat rumors)
            remaining_ids = [rumor["id"] for rumor in high_beat_rumors]
            beatable_rumors = []
            
            for rumor in unknown_rumors:
                # Skip rumors already discovered with high beat
                if rumor["id"] in discovered_rumor_ids:
                    continue
                    
                dc = rumor["discovery_dc"]
                if roll_result >= dc:
                    margin = roll_result - dc
                    logging.info(f"Roll {roll_result} beats rumor DC {dc} by {margin} (<7), adding to beatable rumors")
                    beatable_rumors.append(rumor)
            
            if beatable_rumors:
                # Select one random rumor weighted by how much the roll exceeds the DC
                weights = []
                for rumor in beatable_rumors:
                    dc = rumor["discovery_dc"]
                    weight = roll_result - dc + 1  # +1 to ensure positive weight
                    weights.append(weight)
                
                selected_rumor = random.choices(beatable_rumors, weights=weights, k=1)[0]
                logging.info(f"Selected one random rumor from {len(beatable_rumors)} beatable rumors: {selected_rumor['id']}")
                
                # Mark as discovered
                self.rumor_repository.mark_as_known(selected_rumor["id"], faction_id, turn_number)
                discovered_rumor_ids.append(selected_rumor["id"])
            
            logging.info(f"Total discovered rumors: {len(discovered_rumor_ids)} - IDs: {discovered_rumor_ids}")
            return discovered_rumor_ids
        except Exception as e:
            logging.error(f"Error in _process_rumor_discovery: {str(e)}")
            return []
    
    def _calculate_confidence_rating(self, roll_result, quality_tier):
        """Calculate the confidence rating for a monitoring report.
        
        Args:
            roll_result (int): Roll result.
            quality_tier (str): Quality tier of monitoring roll.
            
        Returns:
            int: Confidence rating (1-10).
        """
        try:
            # Base confidence value determined by highest monitoring roll
            if roll_result >= 30:
                base_confidence = 10
            elif roll_result >= 25:
                base_confidence = 9
            elif roll_result >= 20:
                base_confidence = 8
            elif roll_result >= 15:
                base_confidence = 7
            elif roll_result >= 10:
                base_confidence = 5
            elif roll_result >= 5:
                base_confidence = 3
            elif roll_result >= 1:
                base_confidence = 2
            else:
                base_confidence = 1
            
            # Apply possible error to confidence rating
            if roll_result >= 20:
                # Exact confidence rating
                return base_confidence
            elif roll_result >= 15:
                # ±0-1 error
                error = random.randint(0, 1)
            elif roll_result >= 10:
                # ±0-2 error
                error = random.randint(0, 2)
            elif roll_result >= 5:
                # ±1-3 error
                error = random.randint(1, 3)
            elif roll_result >= 1:
                # ±2-4 error
                error = random.randint(2, 4)
            else:
                # ±3-5 error
                error = random.randint(3, 5)
            
            # 50% chance error is higher than actual confidence
            if random.random() < 0.5:
                confidence = min(10, base_confidence + error)
            else:
                confidence = max(1, base_confidence - error)
            
            return confidence
        except Exception as e:
            logging.error(f"Error in _calculate_confidence_rating: {str(e)}")
            return 5  # Default medium confidence
    
    def _process_stronghold_detection(self, district, quality_tier, perceived_influences):
        """Process stronghold detection based on quality tier.
        
        Args:
            district: District instance.
            quality_tier (str): Quality tier of monitoring roll.
            perceived_influences (dict): Perceived influence values by faction ID.
            
        Returns:
            dict: Perceived stronghold status by faction ID (only for detected factions).
        """
        try:
            perceived_strongholds = {}
            
            # Process stronghold detection according to quality tiers from specification
            for faction_id, actual_stronghold in district.strongholds.items():
                # Skip factions that weren't detected
                if faction_id not in perceived_influences:
                    continue
                
                # Skip if no actual stronghold (except for potential false positives)
                if not actual_stronghold and quality_tier not in ["poor", "very_poor", "abysmal"]:
                    perceived_strongholds[faction_id] = False
                    continue
                
                # Set detection probabilities based on quality tier
                correctly_identified = False
                falsely_identified = False
                
                if quality_tier == "legendary" or quality_tier == "exceptional":
                    # 100% accurate stronghold detection
                    correctly_identified = True
                elif quality_tier == "very_good":
                    # 95% chance to correctly identify stronghold
                    correctly_identified = random.random() < 0.95
                elif quality_tier == "good":
                    # 85% chance to correctly identify stronghold
                    correctly_identified = random.random() < 0.85
                elif quality_tier == "average":
                    # 70% chance to correctly identify stronghold
                    correctly_identified = random.random() < 0.70
                elif quality_tier == "poor":
                    # 50% chance to correctly identify stronghold, 10% chance to falsely identify
                    correctly_identified = random.random() < 0.50
                    falsely_identified = random.random() < 0.10
                elif quality_tier == "very_poor":
                    # 30% chance to correctly identify stronghold, 25% chance to falsely identify
                    correctly_identified = random.random() < 0.30
                    falsely_identified = random.random() < 0.25
                elif quality_tier == "abysmal":
                    # 20% chance to correctly identify stronghold, 40% chance to falsely identify
                    correctly_identified = random.random() < 0.20
                    falsely_identified = random.random() < 0.40
                
                # Set perceived stronghold based on detection results
                if actual_stronghold:
                    # Faction actually has a stronghold
                    perceived_strongholds[faction_id] = correctly_identified
                else:
                    # Faction doesn't have a stronghold, but might be falsely identified
                    perceived_strongholds[faction_id] = falsely_identified
            
            return perceived_strongholds
        except Exception as e:
            logging.error(f"Error in _process_stronghold_detection: {str(e)}")
            return {}
    
    def _create_monitoring_report(self, turn_number, faction_id, district_id, 
                               perceived_influences, phantom_detections, 
                               district_modifier, discovered_rumors, confidence_rating,
                               perceived_strongholds=None):
        """Create a monitoring report in the database.
        
        Args:
            turn_number (int): Current turn number.
            faction_id (str): Faction ID.
            district_id (str): District ID.
            perceived_influences (dict): Perceived influence values by faction ID.
            phantom_detections (list): List of phantom detections.
            district_modifier (dict): District modifier discovery result.
            discovered_rumors (list): List of discovered rumor IDs.
            confidence_rating (int): Confidence rating.
            perceived_strongholds (dict, optional): Perceived stronghold status by faction ID.
            
        Returns:
            str: Report ID if successful, None otherwise.
        """
        try:
            # Generate a unique report ID
            report_id = str(uuid.uuid4())
            
            # Create report JSON
            report_data = {
                "perceived_influences": perceived_influences,
                "phantom_detections": phantom_detections,
                "district_modifier": district_modifier,
                "discovered_rumors": discovered_rumors,
                "confidence_rating": confidence_rating,
                "perceived_strongholds": perceived_strongholds or {},
                "turn_number": turn_number,
                "report_time": datetime.now().isoformat()
            }
            
            report_json = json.dumps(report_data)
            
            # Create report record
            with self.db_manager.connection:
                query = """
                    INSERT INTO faction_monitoring_reports (
                        id, faction_id, district_id, turn_number,
                        report_json, confidence_rating, created_at
                    )
                    VALUES (
                        :id, :faction_id, :district_id, :turn_number,
                        :report_json, :confidence_rating, :created_at
                    )
                """
                
                self.db_manager.execute_update(query, {
                    "id": report_id,
                    "faction_id": faction_id,
                    "district_id": district_id,
                    "turn_number": turn_number,
                    "report_json": report_json,
                    "confidence_rating": confidence_rating,
                    "created_at": datetime.now().isoformat()
                })
                return report_id
        except Exception as e:
            logging.error(f"Error in _create_monitoring_report: {str(e)}")
            return None
    
    def get_monitoring_report(self, report_id):
        """Get a monitoring report by ID.
        
        Args:
            report_id (str): Report ID.
            
        Returns:
            dict: Monitoring report data.
        """
        try:
            query = """
                SELECT report_json, faction_id, district_id, turn_number, confidence_rating
                FROM faction_monitoring_reports
                WHERE id = :report_id
            """
            
            result = self.db_manager.execute_query(query, {"report_id": report_id})
            
            if not result:
                return None
                
            report = dict(result[0])
            report_data = json.loads(report["report_json"])
            
            # Add faction and district information
            report_data["faction_id"] = report["faction_id"]
            report_data["district_id"] = report["district_id"]
            report_data["turn_number"] = report["turn_number"]
            report_data["confidence_rating"] = report["confidence_rating"]
            
            return report_data
        except Exception as e:
            logging.error(f"Error in get_monitoring_report: {str(e)}")
            return None
    
    def get_faction_reports(self, faction_id, turn_number=None):
        """Get all monitoring reports for a faction.
        
        Args:
            faction_id (str): Faction ID.
            turn_number (int, optional): Turn number to filter by. Defaults to None.
            
        Returns:
            list: List of monitoring report summaries.
        """
        try:
            if turn_number:
                query = """
                    SELECT id, district_id, turn_number, confidence_rating, created_at
                    FROM faction_monitoring_reports
                    WHERE faction_id = :faction_id
                    AND turn_number = :turn_number
                    ORDER BY created_at DESC
                """
                
                params = {"faction_id": faction_id, "turn_number": turn_number}
            else:
                query = """
                    SELECT id, district_id, turn_number, confidence_rating, created_at
                    FROM faction_monitoring_reports
                    WHERE faction_id = :faction_id
                    ORDER BY turn_number DESC, created_at DESC
                """
                
                params = {"faction_id": faction_id}
            
            results = self.db_manager.execute_query(query, params)
            
            reports = []
            for row in results:
                report = dict(row)
                
                # Get district name
                district = self.district_repository.find_by_id(report["district_id"])
                district_name = district.name if district else "Unknown District"
                
                reports.append({
                    "id": report["id"],
                    "district_id": report["district_id"],
                    "district_name": district_name,
                    "turn_number": report["turn_number"],
                    "confidence_rating": report["confidence_rating"],
                    "created_at": report["created_at"]
                })
            
            return reports
        except Exception as e:
            logging.error(f"Error in get_faction_reports: {str(e)}")
            return []
    
    def generate_weekly_intelligence_summary(self, faction_id, turn_number):
        """Generate a summary of all intelligence gathered by a faction in a turn.
        
        Args:
            faction_id (str): Faction ID.
            turn_number (int): Turn number.
            
        Returns:
            dict: Intelligence summary.
        """
        try:
            # Get all reports for the faction this turn
            reports = self.get_faction_reports(faction_id, turn_number)
            
            # Get detailed data for each report
            detailed_reports = []
            for report_summary in reports:
                report_data = self.get_monitoring_report(report_summary["id"])
                if report_data:
                    detailed_reports.append(report_data)
            
            # Get faction
            faction = self.faction_repository.find_by_id(faction_id)
            if not faction:
                return {"error": "Faction not found"}
            
            # Get all districts
            districts = self.district_repository.find_all()
            district_map = {d.id: d for d in districts}
            
            # Organize reports by district
            district_reports = {}
            for report in detailed_reports:
                district_id = report["district_id"]
                if district_id not in district_reports:
                    district_reports[district_id] = []
                district_reports[district_id].append(report)
            
            # Generate summary
            summary = {
                "faction_id": faction_id,
                "faction_name": faction.name,
                "turn_number": turn_number,
                "report_time": datetime.now().isoformat(),
                "districts": []
            }
            
            # Process each district
            for district_id, reports in district_reports.items():
                district = district_map.get(district_id)
                if not district:
                    continue
                
                # Find highest confidence report
                best_report = max(reports, key=lambda r: r["confidence_rating"])
                
                # Combine all discovered rumors
                discovered_rumors = set()
                for report in reports:
                    if "discovered_rumors" in report:
                        discovered_rumors.update(report["discovered_rumors"])
                
                # Get rumor details
                rumor_details = []
                for rumor_id in discovered_rumors:
                    rumor = self.rumor_repository.find_by_id(rumor_id)
                    if rumor:
                        rumor_details.append({
                            "id": rumor.id,
                            "rumor_text": rumor.rumor_text
                        })
                
                # Process faction information
                factions_detected = []
                if "perceived_influences" in best_report:
                    for faction_id, influence in best_report["perceived_influences"].items():
                        # Get faction name
                        detected_faction = self.faction_repository.find_by_id(faction_id)
                        if not detected_faction:
                            continue
                            
                        # Check if phantom
                        is_phantom = False
                        if "phantom_detections" in best_report and faction_id in best_report["phantom_detections"]:
                            is_phantom = True
                            
                        factions_detected.append({
                            "faction_id": faction_id,
                            "faction_name": detected_faction.name,
                            "influence": influence,
                            "is_phantom": is_phantom
                        })
                
                # Add district summary
                summary["districts"].append({
                    "district_id": district_id,
                    "district_name": district.name,
                    "factions_detected": factions_detected,
                    "district_modifier": best_report.get("district_modifier"),
                    "confidence_rating": best_report["confidence_rating"],
                    "discovered_rumors": rumor_details
                })
            
            return summary
        except Exception as e:
            logging.error(f"Error in generate_weekly_intelligence_summary: {str(e)}")
            return {"error": str(e)}
            
    def generate_weekly_report(self, faction_id, turn_number):
        """Alias for generate_weekly_intelligence_summary for backward compatibility.
        
        Args:
            faction_id (str): Faction ID.
            turn_number (int): Turn number.
            
        Returns:
            dict: Intelligence summary.
        """
        return self.generate_weekly_intelligence_summary(faction_id, turn_number)
        
    def generate_consolidated_report(self, faction_id, turn_number):
        """Generate a simplified consolidated report showing only key information across all districts.
        
        This report focuses only on confidence ratings, district modifiers, and newly discovered rumors
        for the current turn, without including detailed influence information.
        
        Args:
            faction_id (str): Faction ID.
            turn_number (int): Turn number.
            
        Returns:
            dict: Consolidated report containing only essential information.
        """
        try:
            # Get all reports for the faction this turn
            reports = self.get_faction_reports(faction_id, turn_number)
            
            # Get detailed data for each report
            detailed_reports = []
            for report_summary in reports:
                report_data = self.get_monitoring_report(report_summary["id"])
                if report_data:
                    detailed_reports.append(report_data)
            
            # Get faction
            faction = self.faction_repository.find_by_id(faction_id)
            if not faction:
                return {"error": "Faction not found"}
            
            # Get all districts
            districts = self.district_repository.find_all()
            district_map = {d.id: d for d in districts}
            
            # Initialize consolidated report
            consolidated_report = {
                "faction_id": faction_id,
                "faction_name": faction.name,
                "turn_number": turn_number,
                "report_time": datetime.now().isoformat(),
                "districts": []
            }
            
            # Process each report to extract only the information we need
            for report in detailed_reports:
                district_id = report["district_id"]
                district = district_map.get(district_id)
                
                if not district:
                    continue
                
                # Get confident rating
                confidence_rating = report.get("confidence_rating", 0)
                
                # Get district modifier
                district_modifier = report.get("district_modifier")
                
                # Get discovered rumors
                discovered_rumors = []
                if "discovered_rumors" in report and report["discovered_rumors"]:
                    for rumor_id in report["discovered_rumors"]:
                        rumor = self.rumor_repository.find_by_id(rumor_id)
                        if rumor:
                            discovered_rumors.append({
                                "id": rumor.id,
                                "rumor_text": rumor.rumor_text
                            })
                
                # Add district to consolidated report if it has any relevant information
                if confidence_rating > 0 or district_modifier or discovered_rumors:
                    consolidated_report["districts"].append({
                        "district_id": district_id,
                        "district_name": district.name,
                        "confidence_rating": confidence_rating,
                        "district_modifier": district_modifier,
                        "discovered_rumors": discovered_rumors
                    })
            
            # Sort districts by confidence rating (highest first)
            consolidated_report["districts"].sort(key=lambda d: d.get("confidence_rating", 0), reverse=True)
            
            return consolidated_report
        except Exception as e:
            logging.error(f"Error in generate_consolidated_report: {str(e)}")
            return {"error": str(e)}