import random
import logging
from datetime import datetime


class InfluenceManager:
    """Manages faction influence mechanics in districts."""
    
    def __init__(self, district_repository, faction_repository):
        """Initialize the influence manager.
        
        Args:
            district_repository: Repository for district operations.
            faction_repository: Repository for faction operations.
        """
        self.district_repository = district_repository
        self.faction_repository = faction_repository
    
    def gain_influence(self, district_id, faction_id, amount=1):
        """Add influence for a faction in a district from the pool.
        
        Args:
            district_id (str): District ID.
            faction_id (str): Faction ID.
            amount (int, optional): Amount to add. Defaults to 1.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            district = self.district_repository.find_by_id(district_id)
            if not district:
                logging.error(f"District {district_id} not found")
                return False
            
            # Check if enough influence is available in the pool
            if district.influence_pool < amount:
                logging.warning(f"Not enough influence in pool: {district.influence_pool} < {amount}")
                return False
            
            # Calculate new influence value for the faction
            current = district.get_faction_influence(faction_id)
            new_value = current + amount
            
            # Update faction influence in district
            if district.set_faction_influence(faction_id, new_value):
                # Commit changes to the database
                return self.district_repository.update(district)
            
            return False
        except Exception as e:
            logging.error(f"Error in gain_influence: {str(e)}")
            return False
    
    def take_influence(self, district_id, faction_id, target_faction_id, amount=1):
        """Take influence from another faction in a district.
        
        Args:
            district_id (str): District ID.
            faction_id (str): Faction ID gaining influence.
            target_faction_id (str): Faction ID losing influence.
            amount (int, optional): Amount to transfer. Defaults to 1.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            district = self.district_repository.find_by_id(district_id)
            if not district:
                logging.error(f"District {district_id} not found")
                return False
            
            # Ensure target faction has enough influence
            target_influence = district.get_faction_influence(target_faction_id)
            if target_influence < amount:
                logging.warning(f"Target faction {target_faction_id} has insufficient influence: {target_influence} < {amount}")
                return False
            
            # Calculate new influence values
            current_value = district.get_faction_influence(faction_id)
            new_value = current_value + amount
            new_target_value = target_influence - amount
            
            # Begin atomic operation
            success = True
            
            # Update target faction influence
            if not district.set_faction_influence(target_faction_id, new_target_value):
                success = False
            
            # Update acting faction influence
            if success and not district.set_faction_influence(faction_id, new_value):
                # Roll back target faction change
                district.set_faction_influence(target_faction_id, target_influence)
                success = False
            
            # Commit changes to the database if successful
            if success:
                return self.district_repository.update(district)
            
            return False
        except Exception as e:
            logging.error(f"Error in take_influence: {str(e)}")
            return False
    
    def calculate_decay(self, district_id, game_state):
        """Calculate influence decay for all factions in a district.
        
        Args:
            district_id (str): District ID.
            game_state: Current game state information.
            
        Returns:
            dict: Dictionary of faction_id -> decay_amount
        """
        try:
            district = self.district_repository.find_by_id(district_id)
            if not district:
                logging.error(f"District {district_id} not found")
                return {}
            
            decay_results = {}
            
            # Base decay: 5% chance to lose 1 influence for each point above 2
            for faction_id, influence in district.faction_influence.items():
                # Skip decay if faction has 2 or less influence
                if influence <= 2:
                    continue
                
                # Check for stronghold protection
                has_stronghold = district.has_stronghold(faction_id)
                
                # Calculate decay for this faction
                decay_amount = 0
                
                # If faction has a stronghold, only apply decay to influence above 5
                if has_stronghold:
                    excess_influence = max(0, influence - 5)
                    for _ in range(excess_influence):
                        if random.random() < 0.05:  # 5% chance
                            decay_amount += 1
                else:
                    excess_influence = max(0, influence - 2)
                    for _ in range(excess_influence):
                        if random.random() < 0.05:  # 5% chance
                            decay_amount += 1
                
                if decay_amount > 0:
                    decay_results[faction_id] = decay_amount
            
            # Saturation decay
            total_influence = sum(district.faction_influence.values())
            
            if total_influence == 10:  # All slots filled
                if random.random() < 0.35:  # 35% chance
                    # Select a faction weighted by their proportion of influence
                    choices = []
                    for faction_id, influence in district.faction_influence.items():
                        choices.extend([faction_id] * influence)
                    
                    if choices:
                        chosen_faction = random.choice(choices)
                        decay_results[chosen_faction] = decay_results.get(chosen_faction, 0) + 1
            
            elif total_influence == 9:  # Almost full
                if random.random() < 0.10:  # 10% chance
                    # Select a faction weighted by their proportion of influence
                    choices = []
                    for faction_id, influence in district.faction_influence.items():
                        choices.extend([faction_id] * influence)
                    
                    if choices:
                        chosen_faction = random.choice(choices)
                        decay_results[chosen_faction] = decay_results.get(chosen_faction, 0) + 1
            
            return decay_results
        except Exception as e:
            logging.error(f"Error in calculate_decay: {str(e)}")
            return {}
    
    def apply_decay(self, district_id, decay_results):
        """Apply calculated decay to factions in a district.
        
        Args:
            district_id (str): District ID.
            decay_results (dict): Dictionary of faction_id -> decay_amount.
            
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            district = self.district_repository.find_by_id(district_id)
            if not district:
                logging.error(f"District {district_id} not found")
                return False
            
            # Apply all decay values
            for faction_id, decay_amount in decay_results.items():
                current = district.get_faction_influence(faction_id)
                new_value = max(0, current - decay_amount)
                district.set_faction_influence(faction_id, new_value)
            
            # Commit changes to the database
            return self.district_repository.update(district)
        except Exception as e:
            logging.error(f"Error in apply_decay: {str(e)}")
            return False
    
    def calculate_dc_for_gain_control(self, district_id, faction_id, target_faction_id=None):
        """Calculate the DC for gaining or taking control in a district.
        
        Args:
            district_id (str): District ID.
            faction_id (str): Faction ID attempting action.
            target_faction_id (str, optional): Target faction ID (for take control). Defaults to None.
            
        Returns:
            int: Calculated DC value.
        """
        try:
            district = self.district_repository.find_by_id(district_id)
            if not district:
                logging.error(f"District {district_id} not found")
                return 20  # Default high DC
            
            # Base DC is 11
            dc = 11
            
            # Apply district likeability modifier
            likeability = district.get_faction_likeability(faction_id)
            dc += -likeability  # Negative likeability increases DC
            
            # Apply current influence modifier
            influence = district.get_faction_influence(faction_id)
            
            if influence == 0:
                dc += 3
            elif influence == 1:
                dc += 1
            elif 2 <= influence <= 3:
                dc -= 1
            elif 4 <= influence <= 5:
                dc += 0  # No modifier
            elif influence == 6:
                dc += 1
            elif influence == 7:
                dc += 2
            elif influence == 8:
                dc += 3
            elif influence == 9:
                dc += 4
            
            # Apply stronghold bonus
            if district.has_stronghold(faction_id):
                dc -= 2
            
            # Apply weekly fluctuation
            dc += district.weekly_dc_modifier
            
            # If targeting a specific faction, add +3
            if target_faction_id:
                dc += 3
                
                # Check relationship with target
                faction = self.faction_repository.find_by_id(faction_id)
                if faction:
                    relationship = faction.get_relationship(target_faction_id)
                    dc += relationship  # Negative relationships make it easier
            
            # Ensure DC is at least 5
            return max(5, dc)
        except Exception as e:
            logging.error(f"Error in calculate_dc_for_gain_control: {str(e)}")
            return 15  # Default medium DC if error