import logging
import random
import json
import uuid
from datetime import datetime

from .action import ActionManager
from .monitoring import MonitoringManager
from .influence import InfluenceManager
from .relationship import RelationshipManager


class TurnResolutionManager:
    """Manages the complete turn resolution process."""
    
    def __init__(self, db_manager, district_repository, faction_repository, 
                 agent_repository, squadron_repository, rumor_repository, turn_manager):
        """Initialize the turn resolution manager.
        
        Args:
            db_manager: Database manager instance.
            district_repository: Repository for district operations.
            faction_repository: Repository for faction operations.
            agent_repository: Repository for agent operations.
            squadron_repository: Repository for squadron operations.
            rumor_repository: Repository for rumor operations.
            turn_manager: Turn manager instance.
        """
        self.db_manager = db_manager
        self.district_repository = district_repository
        self.faction_repository = faction_repository
        self.agent_repository = agent_repository
        self.squadron_repository = squadron_repository
        self.rumor_repository = rumor_repository
        self.turn_manager = turn_manager
        
        # Initialize component managers
        self.action_manager = ActionManager(
            db_manager, 
            district_repository, 
            faction_repository, 
            agent_repository, 
            squadron_repository
        )
        
        self.monitoring_manager = MonitoringManager(
            db_manager, 
            district_repository, 
            faction_repository, 
            agent_repository, 
            squadron_repository, 
            rumor_repository
        )
        
        self.influence_manager = InfluenceManager(
            district_repository, 
            faction_repository
        )
        
        self.relationship_manager = RelationshipManager(
            faction_repository
        )
    
    def process_turn_part1(self):
        """Process part 1 of the turn (up to conflict resolution).
        
        Returns:
            dict: Results of part 1 processing.
        """
        try:
            # Get current turn information
            turn_info = self.turn_manager.get_current_turn()
            turn_number = turn_info["current_turn"]
            
            # Log start of turn processing
            logging.info(f"Beginning turn {turn_number} processing - Part 1")
            self.turn_manager.log_turn_history(
                turn_number,
                "preparation",
                f"Beginning turn {turn_number} processing - Part 1",
                ""
            )
            
            # Phase 1: Preparation Phase
            self.turn_manager.set_current_phase("preparation")
            logging.info("Phase 1: Preparation Phase")
            
            # Phase 2: Influence Decay Phase
            self.turn_manager.set_current_phase("influence_decay")
            logging.info("Phase 2: Influence Decay Phase")
            decay_results = self.turn_manager.process_influence_decay_phase()
            
            # Phase 3: Assignment Phase (handled by UI, not automated)
            self.turn_manager.set_current_phase("assignment")
            logging.info("Phase 3: Assignment Phase")
            
            # Phase 4: Conflict Detection Phase
            self.turn_manager.set_current_phase("conflict_detection")
            logging.info("Phase 4: Conflict Detection Phase")
            conflicts = self.action_manager.detect_conflicts(turn_number)
            
            # Phase 5: Action Roll Phase
            self.turn_manager.set_current_phase("action_roll")
            logging.info("Phase 5: Action Roll Phase")
            roll_results = self._process_action_rolls(turn_number)
            
            # Log completion of Part 1
            logging.info(f"Completed turn {turn_number} processing - Part 1")
            self.turn_manager.log_turn_history(
                turn_number,
                "manual_conflict_resolution",
                f"Turn {turn_number} Part 1 completed",
                "Paused for manual conflict resolution"
            )
            
            # Set phase to manual conflict resolution
            logging.info(f"[PHASE_DEBUG] Current phase before setting to manual_conflict_resolution: {self.turn_manager.get_current_turn()['current_phase']}")
            self.turn_manager.set_current_phase("manual_conflict_resolution")
            logging.info(f"[PHASE_DEBUG] Current phase after setting to manual_conflict_resolution: {self.turn_manager.get_current_turn()['current_phase']}")
            
            return {
                "turn_number": turn_number,
                "decay_results": decay_results,
                "conflicts": conflicts,
                "roll_results": roll_results,
                "status": "part1_complete"
            }
        except Exception as e:
            logging.error(f"Error in process_turn_part1: {str(e)}")
            return {"error": str(e)}
    
    def process_turn_part2(self):
        """Process part 2 of the turn (after conflict resolution).
        
        Returns:
            dict: Results of part 2 processing.
        """
        try:
            # Get current turn information
            turn_info = self.turn_manager.get_current_turn()
            turn_number = turn_info["current_turn"]
            
            # Check if conflicts have been resolved
            if not self._all_conflicts_resolved(turn_number):
                return {
                    "error": "Not all conflicts have been resolved",
                    "status": "conflicts_pending"
                }
            
            # Log start of part 2
            logging.info(f"Beginning turn {turn_number} processing - Part 2")
            self.turn_manager.log_turn_history(
                turn_number,
                "action_resolution",
                f"Beginning turn {turn_number} processing - Part 2",
                ""
            )
            
            # Phase 6: Action Resolution Phase
            self.turn_manager.set_current_phase("action_resolution")
            logging.info("Phase 6: Action Resolution Phase")
            action_results = self._process_action_resolution(turn_number)
            
            # Phase 7: Random Walk Update Phase
            self.turn_manager.set_current_phase("random_walk_update")
            logging.info("Phase 7: Random Walk Update Phase")
            random_walk_results = self.turn_manager.update_district_dc_modifiers()
            
            # Phase 8: Monitoring Phase
            self.turn_manager.set_current_phase("monitoring")
            logging.info("Phase 8: Monitoring Phase")
            monitoring_results = self.monitoring_manager.process_monitoring(turn_number)
            
            # Phase 9: Faction Passive Monitoring Phase
            self.turn_manager.set_current_phase("faction_passive_monitoring")
            logging.info("Phase 9: Faction Passive Monitoring Phase")
            passive_monitoring_results = self.monitoring_manager.process_passive_monitoring(turn_number)
            
            # Phase 10: Rumor DC Update Phase
            self.turn_manager.set_current_phase("rumor_dc_update")
            logging.info("Phase 10: Rumor DC Update Phase")
            rumor_update_results = self.turn_manager.decrease_rumor_dcs()
            
            # Phase 11: Map Update Phase
            self.turn_manager.set_current_phase("map_update")
            logging.info("Phase 11: Map Update Phase")
        
            # Generate maps
            map_results = self._generate_faction_maps(turn_number)
            
            # Phase 12: Turn Completion Phase
            self.turn_manager.set_current_phase("turn_completion")
            logging.info("Phase 12: Turn Completion Phase")
            
            # Log completion of turn
            logging.info(f"Completed turn {turn_number} processing")
            self.turn_manager.log_turn_history(
                turn_number,
                "turn_completion",
                f"Turn {turn_number} completed",
                "All phases processed successfully"
            )
            
            # Advance to next turn
            self.turn_manager.advance_turn()
            
            return {
                "turn_number": turn_number,
                "action_results": action_results,
                "random_walk_results": random_walk_results,
                "monitoring_results": monitoring_results,
                "passive_monitoring_results": passive_monitoring_results,
                "rumor_update_results": rumor_update_results,
                "status": "turn_complete",
                "map_results": map_results
            }
        except Exception as e:
            logging.error(f"Error in process_turn_part2: {str(e)}")
            return {"error": str(e)}
    
    def _process_action_rolls(self, turn_number):
        """Process all action rolls for the current turn.
        
        Args:
            turn_number (int): Current turn number.
            
        Returns:
            dict: Results of action rolls.
        """
        try:
            # Log the beginning of action roll processing
            logging.info(f"[TURN_DEBUG] Starting _process_action_rolls for turn {turn_number}")
            
            # Reset the penalty tracker to ensure fresh tracking for this turn's action resolution phase
            self.action_manager.reset_penalty_tracker()
            logging.info(f"[TURN_DEBUG] Reset penalty tracker for fresh penalty application in turn {turn_number}")
            
            # Get all actions for this turn
            query = """
                SELECT id, piece_id, piece_type, faction_id, district_id, 
                       action_type, target_faction_id, in_conflict
                FROM actions
                WHERE turn_number = :turn_number
                AND roll_result IS NULL
            """
            
            logging.info(f"[TURN_DEBUG] Executing query to get actions for turn {turn_number}")
            actions = self.db_manager.execute_query(query, {"turn_number": turn_number})
            logging.info(f"[TURN_DEBUG] Retrieved {len(actions)} actions")
            
            roll_results = {
                "total_actions": len(actions),
                "processed_actions": 0,
                "results": []
            }
            
            # Log a few sample actions for debugging
            for idx, action in enumerate(actions[:5]):  # Log up to 5 actions for debugging
                logging.info(f"[TURN_DEBUG] Sample action {idx+1}: {json.dumps(dict(action))}")
            
            # Randomize the order of actions to avoid bias in penalty application
            action_list = [dict(row) for row in actions]
            random.shuffle(action_list)
            logging.info(f"[TURN_DEBUG] Randomized action processing order for fair enemy penalty distribution")
            
            # Process each action roll in random order
            for action in action_list:
                logging.info(f"[TURN_DEBUG] Processing action ID {action['id']}, type: {action['action_type']}")
                
                try:
                    # Roll for the action
                    result = self.action_manager.roll_for_action(action["id"])
                    
                    # Add to results
                    roll_results["results"].append({
                        "action_id": action["id"],
                        "piece_id": action["piece_id"],
                        "piece_type": action["piece_type"],
                        "faction_id": action["faction_id"],
                        "district_id": action["district_id"],
                        "action_type": action["action_type"],
                        "roll_result": result
                    })
                    
                    roll_results["processed_actions"] += 1
                    logging.info(f"[TURN_DEBUG] Successfully processed action ID {action['id']}, roll result: {result}")
                except Exception as action_error:
                    logging.error(f"[TURN_DEBUG] Error processing specific action ID {action['id']}: {str(action_error)}")
            
            logging.info(f"[TURN_DEBUG] Completed _process_action_rolls, processed {roll_results['processed_actions']} actions")
            return roll_results
        except Exception as e:
            logging.error(f"Error in _process_action_rolls: {str(e)}")
            return {"total_actions": 0, "processed_actions": 0, "results": [], "error": str(e)}
    
    def _all_conflicts_resolved(self, turn_number):
        """Check if all conflicts for the current turn have been resolved.
        
        Args:
            turn_number (int): Current turn number.
            
        Returns:
            bool: True if all conflicts resolved, False otherwise.
        """
        try:
            query = """
                SELECT COUNT(*) as pending_count
                FROM conflicts
                WHERE turn_number = :turn_number
                AND resolution_status = 'pending'
            """
            
            result = self.db_manager.execute_query(query, {"turn_number": turn_number})
            
            pending_count = result[0]["pending_count"] if result else 0
            
            return pending_count == 0
        except Exception as e:
            logging.error(f"Error in _all_conflicts_resolved: {str(e)}")
            return False
    
    def _process_action_resolution(self, turn_number):
        """Process action resolution based on rolls and conflict outcomes.
        
        Args:
            turn_number (int): Current turn number.
            
        Returns:
                dict: Results of action resolution.
        """
        try:
            logging.info(f"[TURN_DEBUG] Starting _process_action_resolution for turn {turn_number}")
            
            # Get all actions with rolls
            query = """
                SELECT id, piece_id, piece_type, faction_id, district_id, 
                    action_type, target_faction_id, roll_result, in_conflict, conflict_id,
                    attribute_used, skill_used, aptitude_used, dc, manual_modifier,
                    outcome_tier, conflict_penalty
                FROM actions
                WHERE turn_number = :turn_number
                AND roll_result IS NOT NULL
            """
            
            logging.info(f"[TURN_DEBUG] Executing query to get actions with rolls for turn {turn_number}")
            actions = self.db_manager.execute_query(query, {"turn_number": turn_number})
            logging.info(f"[TURN_DEBUG] Retrieved {len(actions)} actions with rolls")
            
            resolution_results = {
                "total_actions": len(actions),
                "processed_actions": 0,
                "results": [],
                "influence_changes": []
            }
            
            # Log a few sample actions for debugging
            for idx, action in enumerate(actions[:5]):  # Log up to 5 actions for debugging
                logging.info(f"[TURN_DEBUG] Sample action with roll {idx+1}: {json.dumps(dict(action))}")
            
            # Randomize the order of actions to ensure fair resolution
            action_list = [dict(row) for row in actions]
            random.shuffle(action_list)
            logging.info(f"[TURN_DEBUG] Randomized action resolution order for fair processing")
            
            # Process each action in random order
            for action in action_list:
                logging.info(f"[TURN_DEBUG] Resolving action ID {action['id']}, type: {action['action_type']}")
                
                try:
                    # Skip actions involved in unresolved conflicts
                    if action["in_conflict"]:
                        conflict_resolved = self._check_conflict_resolution(action["id"])
                        if not conflict_resolved:
                            logging.info(f"[TURN_DEBUG] Skipping action ID {action['id']} - unresolved conflict")
                            continue
                        else:
                            logging.info(f"[TURN_DEBUG] Action ID {action['id']} in resolved conflict - applying conflict outcome")
                            
                            # Get conflict outcome for this faction
                            conflict_outcome = self._get_conflict_outcome_for_faction(action["conflict_id"], action["faction_id"])
                            logging.info(f"[TURN_DEBUG] Conflict outcome for faction {action['faction_id']}: {conflict_outcome}")
                            
                            # If faction lost the conflict, action automatically fails
                            if conflict_outcome == "loss":
                                resolution_results["results"].append({
                                    "action_id": action["id"],
                                    "piece_id": action["piece_id"],
                                    "piece_type": action["piece_type"],
                                    "faction_id": action["faction_id"],
                                    "district_id": action["district_id"],
                                    "action_type": action["action_type"],
                                    "result": {
                                        "resolution": "failed",
                                        "result": "Action failed due to lost conflict"
                                    }
                                })
                                resolution_results["processed_actions"] += 1
                                continue
                    
                    # Apply conflict penalty to the effective roll result for decision making
                    # Note: The stored roll_result remains unchanged, but we use adjusted_roll for determining success
                    conflict_penalty = action["conflict_penalty"] or 0
                    adjusted_roll = action["roll_result"]
                    
                    # Only apply the conflict penalty for determining success if it's not already applied
                    # Note: conflict_penalty is stored as a positive number but applied as negative
                    if conflict_penalty > 0:
                        adjusted_roll -= conflict_penalty
                        logging.info(f"[TURN_DEBUG] Applied conflict penalty of -{conflict_penalty} to action {action['id']}")
                        logging.info(f"[TURN_DEBUG] Original roll: {action['roll_result']}, Adjusted roll: {adjusted_roll}")
                    
                    # Process action based on type
                    if action["action_type"] == "monitor":
                        # Use the monitoring result processing method
                        monitoring_result = self.monitoring_manager._process_monitoring_result(
                            turn_number, 
                            action["faction_id"], 
                            action["district_id"], 
                            adjusted_roll  # Use adjusted roll with penalty applied
                        )
                        # Get the quality tier for the result message
                        quality_tier = self.monitoring_manager._determine_quality_tier(adjusted_roll)
                        result = {"resolution": "success", "result": f"Monitoring processed: {quality_tier} quality", "monitoring_result": monitoring_result}
                        logging.info(f"[TURN_DEBUG] Monitoring action {action['id']} result quality: {quality_tier}")
                    elif action["action_type"] in ["gain_influence", "take_influence"]:
                        # Create an adjusted action copy with the penalty applied to roll_result
                        adjusted_action = action.copy()
                        adjusted_action["roll_result"] = adjusted_roll
                        
                        # Use the _resolve_influence_action method with adjusted roll
                        result = self._resolve_influence_action(adjusted_action)
                        logging.info(f"[TURN_DEBUG] Influence action {action['id']} result: {result}")
                        
                        # Add influence changes to the overall results if any
                        if "influence_changes" in result:
                            resolution_results["influence_changes"].extend(result["influence_changes"])
                    else:
                        # For other action types, determine success/failure using adjusted roll
                        outcome_tier = action["outcome_tier"] if action["outcome_tier"] else "unknown"
                        
                        # If we have a DC, recheck success/failure with adjusted roll
                        if action["dc"] is not None:
                            if adjusted_roll >= (action["dc"] + 10):
                                outcome_tier = "critical_success"
                            elif adjusted_roll >= action["dc"]:
                                outcome_tier = "success"
                            elif adjusted_roll <= (action["dc"] - 10):
                                outcome_tier = "critical_failure"
                            else:
                                outcome_tier = "failure"
                        
                        result = {
                            "resolution": outcome_tier,
                            "result": f"Action {'succeeded' if adjusted_roll >= (action['dc'] or 0) else 'failed'}"
                        }
                        
                        # Add detailed information about modifiers (including conflict and enemy penalties)
                        if conflict_penalty:
                            result["conflict_penalty"] = conflict_penalty
                            result["result"] += f" (with {conflict_penalty} conflict penalty applied)"
                            result["result"] += f" [Original roll: {action['roll_result']}, Adjusted: {adjusted_roll}]"
                        
                        logging.info(f"[TURN_DEBUG] Other action {action['id']} result: {result}")
                    
                    # Add to results
                    resolution_results["results"].append({
                        "action_id": action["id"],
                        "piece_id": action["piece_id"],
                        "piece_type": action["piece_type"],
                        "faction_id": action["faction_id"],
                        "district_id": action["district_id"],
                        "action_type": action["action_type"],
                        "result": result
                    })
                    
                    resolution_results["processed_actions"] += 1
                    logging.info(f"[TURN_DEBUG] Successfully resolved action ID {action['id']}")
                except Exception as action_error:
                    logging.error(f"[TURN_DEBUG] Error resolving specific action ID {action['id']}: {str(action_error)}")
            
            logging.info(f"[TURN_DEBUG] Completed _process_action_resolution, processed {resolution_results['processed_actions']} actions")
            return resolution_results
        except Exception as e:
            logging.error(f"Error in _process_action_resolution: {str(e)}")
            return {"total_actions": 0, "processed_actions": 0, "results": [], "error": str(e)}

    def _check_conflict_resolution(self, action_id):
        """Check if a conflict involving an action has been resolved.
        
        Args:
            action_id (str): Action ID to check.
            
        Returns:
            bool: True if conflict is resolved or action not in conflict, False otherwise.
        """
        try:
            # Get conflict information for the action
            query = """
                SELECT c.id, c.resolution_status, cf.outcome
                FROM actions a
                JOIN conflicts c ON a.conflict_id = c.id
                LEFT JOIN conflict_factions cf ON 
                    c.id = cf.conflict_id AND a.faction_id = cf.faction_id
                WHERE a.id = :action_id
            """
            
            result = self.db_manager.execute_query(query, {"action_id": action_id})
            
            if not result:
                # No conflict found for this action
                return True
            
            conflict = dict(result[0])
            logging.info(f"[TURN_DEBUG] Checking conflict resolution for action {action_id}: {json.dumps(conflict)}")
            
            # Check if conflict is resolved
            if conflict["resolution_status"] == "resolved":
                # We'll handle outcomes in the action resolution method
                return True
            else:
                logging.info(f"[TURN_DEBUG] Action {action_id} cannot proceed - conflict not resolved")
                return False
            
        except Exception as e:
            logging.error(f"Error checking conflict resolution for action {action_id}: {str(e)}")
            return False

    def _get_conflict_outcome_for_faction(self, conflict_id, faction_id):
        """Get the conflict outcome for a specific faction.
        
        Args:
            conflict_id (str): Conflict ID.
            faction_id (str): Faction ID.
            
        Returns:
            str: Outcome ('win', 'loss', 'draw', or None if not found).
        """
        try:
            query = """
                SELECT outcome
                FROM conflict_factions
                WHERE conflict_id = :conflict_id
                AND faction_id = :faction_id
            """
            
            result = self.db_manager.execute_query(query, {
                "conflict_id": conflict_id,
                "faction_id": faction_id
            })
            
            if result:
                return result[0]["outcome"]
            return None
        except Exception as e:
            logging.error(f"Error getting conflict outcome: {str(e)}")
            return None

    def _resolve_influence_action(self, action):
        """Resolve an influence action.
        
        Args:
            action (dict): Action data.
            
        Returns:
            dict: Result of influence resolution.
        """
        try:
            faction_id = action["faction_id"]
            district_id = action["district_id"]
            action_type = action["action_type"]
            target_faction_id = action["target_faction_id"]
            outcome_tier = action["outcome_tier"]
            
            # Get district
            district = self.district_repository.find_by_id(district_id)
            if not district:
                return {
                    "resolution": "failed",
                    "result": "District not found"
                }
            
            # Log all the penalties that affected this action
            penalty_info = ""
            if action["conflict_penalty"]:
                penalty_info += f" (Conflict Penalty: {action['conflict_penalty']})"
            
            # Get the roll value - we use this to determine outcome
            roll_value = action["roll_result"]
            
            # Get the DC for this action, calculate if not set
            dc = action["dc"]
            if dc is None:
                # Calculate DC for gain or take influence
                dc = self.influence_manager.calculate_dc_for_gain_control(district_id, faction_id, target_faction_id)
                
                # Update the action with the calculated DC
                with self.db_manager.connection:
                    self.db_manager.execute_update(
                        "UPDATE actions SET dc = :dc, updated_at = :updated_at WHERE id = :action_id",
                        {
                            "action_id": action["id"],
                            "dc": dc,
                            "updated_at": datetime.now().isoformat()
                        }
                    )
            
            # Determine outcome tier based on roll vs DC
            if not outcome_tier:
                if roll_value >= (dc + 10):
                    outcome_tier = "critical_success"
                elif roll_value >= dc:
                    outcome_tier = "success"
                elif roll_value <= (dc - 10):
                    outcome_tier = "critical_failure"
                else:
                    outcome_tier = "failure"
                
                # Update the action with the calculated outcome tier
                with self.db_manager.connection:
                    self.db_manager.execute_update(
                        "UPDATE actions SET outcome_tier = :outcome_tier, updated_at = :updated_at WHERE id = :action_id",
                        {
                            "action_id": action["id"],
                            "outcome_tier": outcome_tier,
                            "updated_at": datetime.now().isoformat()
                        }
                    )
            
            # Process outcome
            if outcome_tier == "critical_success":
                if action_type == "gain_influence":
                    # Gain 2 influence from pool
                    result = self.influence_manager.gain_influence(district_id, faction_id, 2)
                    
                    if result:
                        return {
                            "resolution": "critical_success",
                            "result": f"Gained 2 influence{penalty_info}",
                            "influence_changes": [{
                                "district_id": district_id,
                                "faction_id": faction_id,
                                "change": 2,
                                "new_value": district.get_faction_influence(faction_id)
                            }]
                        }
                    else:
                        return {
                            "resolution": "failed",
                            "result": f"Failed to gain influence{penalty_info}"
                        }
                
                elif action_type == "take_influence":
                    # Check if target faction has influence
                    target_influence = district.get_faction_influence(target_faction_id)
                    if target_influence == 0:
                        return {
                            "resolution": "failed",
                            "result": f"Target faction has no influence to take{penalty_info}"
                        }
                    
                    # Multiple possible outcomes
                    roll = random.random()
                    
                    if roll < 0.40 and target_influence >= 2:
                        # 40% chance: Gain 2, target loses 2
                        gained = 2
                        lost = 2
                    elif roll < 0.80:
                        # 40% chance: Gain 2, target loses 1 (if neutral pool has space)
                        if district.influence_pool >= 1:
                            gained = 2
                            lost = 1
                        else:
                            gained = 1
                            lost = 1
                    else:
                        # 20% chance: Gain 1, target loses 1
                        gained = 1
                        lost = 1
                    
                    # Ensure enough influence is available to take
                    if target_influence >= lost:
                        # Ensure taking faction can gain influence (max 10 total)
                        current_influence = district.get_faction_influence(faction_id)
                        if current_influence + gained > 10:
                            gained = 10 - current_influence
                        
                        # Update target faction first (losing influence)
                        new_target_value = target_influence - lost
                        district.set_faction_influence(target_faction_id, new_target_value)
                        
                        # Update acting faction (gaining influence)
                        new_faction_value = current_influence + gained
                        district.set_faction_influence(faction_id, new_faction_value)
                        
                        # Save changes
                        self.district_repository.update(district)
                        
                        return {
                            "resolution": "critical_success",
                            "result": f"Gained {gained} influence, target lost {lost} influence{penalty_info}",
                            "influence_changes": [
                                {
                                    "district_id": district_id,
                                    "faction_id": faction_id,
                                    "change": gained,
                                    "new_value": new_faction_value
                                },
                                {
                                    "district_id": district_id,
                                    "faction_id": target_faction_id,
                                    "change": -lost,
                                    "new_value": new_target_value
                                }
                            ]
                        }
                    else:
                        return {
                            "resolution": "failed",
                            "result": f"Target faction doesn't have {lost} influence to take{penalty_info}"
                        }
            
            elif outcome_tier == "success":
                if action_type == "gain_influence":
                    # Gain 1 influence from pool
                    result = self.influence_manager.gain_influence(district_id, faction_id, 1)
                    
                    if result:
                        return {
                            "resolution": "success",
                            "result": f"Gained 1 influence{penalty_info}",
                            "influence_changes": [{
                                "district_id": district_id,
                                "faction_id": faction_id,
                                "change": 1,
                                "new_value": district.get_faction_influence(faction_id)
                            }]
                        }
                    else:
                        return {
                            "resolution": "failed",
                            "result": f"Failed to gain influence{penalty_info}"
                        }
                
                elif action_type == "take_influence":
                    # Check if target faction has influence
                    target_influence = district.get_faction_influence(target_faction_id)
                    if target_influence == 0:
                        return {
                            "resolution": "failed",
                            "result": f"Target faction has no influence to take{penalty_info}"
                        }
                    
                    # 80% chance to gain 1 and target loses 1
                    if random.random() < 0.80:
                        # Take influence from target
                        result = self.influence_manager.take_influence(
                            district_id, faction_id, target_faction_id, 1
                        )
                        
                        if result:
                            return {
                                "resolution": "success",
                                "result": f"Gained 1 influence, target lost 1 influence{penalty_info}",
                                "influence_changes": [
                                    {
                                        "district_id": district_id,
                                        "faction_id": faction_id,
                                        "change": 1,
                                        "new_value": district.get_faction_influence(faction_id)
                                    },
                                    {
                                        "district_id": district_id,
                                        "faction_id": target_faction_id,
                                        "change": -1,
                                        "new_value": district.get_faction_influence(target_faction_id)
                                    }
                                ]
                            }
                        else:
                            return {
                                "resolution": "failed",
                                "result": f"Failed to take influence{penalty_info}"
                            }
                    else:
                        return {
                            "resolution": "failed",
                            "result": f"Failed to take influence (80% success chance missed){penalty_info}"
                        }
            
            elif outcome_tier == "failure":
                # No change
                return {
                    "resolution": "failed",
                    "result": f"Action failed, no influence changes{penalty_info}"
                }
            
            elif outcome_tier == "critical_failure":
                if action_type == "gain_influence":
                    # 50% chance to lose 1 influence (if available)
                    if random.random() < 0.50:
                        current_influence = district.get_faction_influence(faction_id)
                        if current_influence > 0:
                            district.set_faction_influence(faction_id, current_influence - 1)
                            self.district_repository.update(district)
                            
                            return {
                                "resolution": "critical_failure",
                                "result": f"Critical failure: Lost 1 influence{penalty_info}",
                                "influence_changes": [{
                                    "district_id": district_id,
                                    "faction_id": faction_id,
                                    "change": -1,
                                    "new_value": district.get_faction_influence(faction_id)
                                }]
                            }
                    
                    return {
                        "resolution": "critical_failure",
                        "result": f"Critical failure{penalty_info}"
                    }
                
                elif action_type == "take_influence":
                    # 30% chance to backfire: lose 1 influence, target gains 1
                    if random.random() < 0.30:
                        current_influence = district.get_faction_influence(faction_id)
                        if current_influence > 0:
                            # Lose 1 influence
                            district.set_faction_influence(faction_id, current_influence - 1)
                            
                            # Target gains 1 influence
                            target_influence = district.get_faction_influence(target_faction_id)
                            district.set_faction_influence(target_faction_id, target_influence + 1)
                            
                            # Save changes
                            self.district_repository.update(district)
                            
                            return {
                                "resolution": "critical_failure",
                                "result": f"Critical failure: Lost 1 influence, target gained 1 influence{penalty_info}",
                                "influence_changes": [
                                    {
                                        "district_id": district_id,
                                        "faction_id": faction_id,
                                        "change": -1,
                                        "new_value": district.get_faction_influence(faction_id)
                                    },
                                    {
                                        "district_id": district_id,
                                        "faction_id": target_faction_id,
                                        "change": 1,
                                        "new_value": district.get_faction_influence(target_faction_id)
                                    }
                                ]
                            }
                    
                    return {
                        "resolution": "critical_failure",
                        "result": f"Critical failure{penalty_info}"
                    }
            
            # Default case
            return {
                "resolution": "unknown",
                "result": f"Unknown outcome tier: {outcome_tier}{penalty_info}"
            }
        except Exception as e:
            logging.error(f"Error in _resolve_influence_action: {str(e)}")
            return {
                "resolution": "error",
                "result": f"Error resolving action: {str(e)}"
            }
    def process_influence_decay_phase(self):
        """Process the influence decay phase."""
        try:
            logging.info("[DECAY_DEBUG] Starting influence decay phase")
            decay_results = {
                "processed_districts": 0,
                "total_influence_lost": 0,
                "affected_factions": []
            }

            # Get all districts
            districts = self.district_repository.find_all()
            logging.info(f"[DECAY_DEBUG] Found {len(districts)} districts to process")
            
            for district in districts:
                logging.info(f"[DECAY_DEBUG] Processing district {district.id} ({district.name})")
                
                # Get all factions with influence in this district
                query = """
                    SELECT faction_id, influence_value
                    FROM district_influence
                    WHERE district_id = :district_id
                    AND influence_value > 2
                """
                results = self.db_manager.execute_query(query, {"district_id": district.id})
                logging.info(f"[DECAY_DEBUG] Found {len(results)} factions with influence > 2 in district {district.name}")
                
                for row in results:
                    faction_data = dict(row)
                    influence = faction_data["influence_value"]
                    faction_id = faction_data["faction_id"]
                    
                    # Get faction name for better logging
                    faction = self.faction_repository.find_by_id(faction_id)
                    faction_name = faction.name if faction else "Unknown faction"
                    
                    # Calculate decay chance
                    decay_chance = 0.05 * (influence - 2)
                    logging.info(f"[DECAY_DEBUG] Faction {faction_name} has influence {influence}, decay chance {decay_chance:.2f}")
                    
                    # Roll for decay
                    roll = random.random()
                    if roll < decay_chance:
                        logging.info(f"[DECAY_DEBUG] Decay triggered for faction {faction_name} in district {district.name} (roll: {roll:.4f}, threshold: {decay_chance:.4f})")
                        
                        # Create decay result record
                        decay_id = str(uuid.uuid4())
                        now = datetime.now().isoformat()
                        
                        query = """
                            INSERT INTO decay_results (
                                id, turn_number, district_id, faction_id,
                                influence_change, created_at, updated_at
                            ) VALUES (
                                :id, :turn_number, :district_id, :faction_id,
                                :influence_change, :created_at, :updated_at
                            )
                        """
                        
                        params = {
                            "id": decay_id,
                            "turn_number": self.turn_info["current_turn"],
                            "district_id": district.id,
                            "faction_id": faction_id,
                            "influence_change": -1,
                            "created_at": now,
                            "updated_at": now
                        }
                        
                        try:
                            # Check if the decay_results table exists
                            check_query = "SELECT name FROM sqlite_master WHERE type='table' AND name='decay_results';"
                            table_check = self.db_manager.execute_query(check_query)
                            if not table_check:
                                logging.error("[DECAY_DEBUG] decay_results table does not exist! Attempting to create it.")
                                create_table_query = """
                                    CREATE TABLE IF NOT EXISTS decay_results (
                                        id TEXT PRIMARY KEY,
                                        turn_number INTEGER NOT NULL,
                                        district_id TEXT NOT NULL,
                                        faction_id TEXT NOT NULL,
                                        influence_change INTEGER NOT NULL,
                                        created_at TEXT NOT NULL,
                                        updated_at TEXT NOT NULL,
                                        FOREIGN KEY (district_id) REFERENCES districts (id),
                                        FOREIGN KEY (faction_id) REFERENCES factions (id)
                                    )
                                """
                                self.db_manager.execute_update(create_table_query)
                                logging.info("[DECAY_DEBUG] Created decay_results table")
                            
                            self.db_manager.execute_update(query, params)
                            logging.info(f"[DECAY_DEBUG] Inserted decay result {decay_id} for faction {faction_name} in district {district.name}")
                            
                            # Update district influence
                            district.set_faction_influence(faction_id, influence - 1)
                            self.district_repository.update(district)
                            logging.info(f"[DECAY_DEBUG] Updated district influence for faction {faction_name} to {influence - 1}")
                            
                            # Update decay results
                            decay_results["total_influence_lost"] += 1
                            if faction_id not in decay_results["affected_factions"]:
                                decay_results["affected_factions"].append(faction_id)
                        except Exception as e:
                            logging.error(f"[DECAY_DEBUG] Error saving decay result: {str(e)}")
                            logging.error(f"[DECAY_DEBUG] Query: {query}")
                            logging.error(f"[DECAY_DEBUG] Params: {params}")
                            # Print full stack trace
                            import traceback
                            logging.error(f"[DECAY_DEBUG] Traceback: {traceback.format_exc()}")
                    else:
                        logging.info(f"[DECAY_DEBUG] No decay for faction {faction_name} (roll: {roll:.4f}, threshold: {decay_chance:.4f})")
                
                decay_results["processed_districts"] += 1
            
            logging.info(f"[DECAY_DEBUG] Completed influence decay phase. Results: {json.dumps(decay_results)}")
            return decay_results
        except Exception as e:
            logging.error(f"Error in process_influence_decay_phase: {str(e)}")
            # Print full stack trace
            import traceback
            logging.error(f"[DECAY_DEBUG] Traceback: {traceback.format_exc()}")
            return {"error": str(e)}
    
    def _generate_faction_maps(self, turn_number):
        """Generate faction-specific maps at the end of the turn.
        
        Args:
            turn_number (int): Current turn number.
            
        Returns:
            dict: Map generation results.
        """
        try:
            from .faction_map_generator import FactionMapGenerator
            
            # Create map generator
            map_generator = FactionMapGenerator(
                self.db_manager,
                self.district_repository,
                self.faction_repository,
                self.monitoring_manager
            )
            
            # Generate faction maps
            faction_maps = map_generator.generate_faction_maps(turn_number)
            
            # Generate DM map
            dm_map = map_generator.save_dm_map(turn_number)
            
            if dm_map:
                faction_maps["dm_map"] = dm_map
            
            return faction_maps
        except Exception as e:
            logging.error(f"Error generating faction maps: {str(e)}")
            return {"errors": [str(e)]}    