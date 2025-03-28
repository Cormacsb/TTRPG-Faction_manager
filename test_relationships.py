#!/usr/bin/env python
import logging
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO)

# Add the parent directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import necessary modules
from src.db.db_manager import DatabaseManager
from src.db.repositories.faction import FactionRepository
from src.db.repositories.district import DistrictRepository
from src.db.repositories.agent import AgentRepository
from src.db.repositories.squadron import SquadronRepository
from src.logic.action import ActionManager

def main():
    # Connect to the database
    db_manager = DatabaseManager("faction_manager.db")
    
    # Create repositories
    faction_repo = FactionRepository(db_manager)
    district_repo = DistrictRepository(db_manager)
    agent_repo = AgentRepository(db_manager)
    squadron_repo = SquadronRepository(db_manager)
    
    # Create action manager for enemy penalty calculation
    action_manager = ActionManager(
        db_manager,
        district_repo,
        faction_repo,
        agent_repo,
        squadron_repo
    )
    
    # Get all factions
    factions = faction_repo.find_all()
    
    if not factions:
        logging.error("No factions found in database!")
        return
    
    logging.info(f"Found {len(factions)} factions:")
    for faction in factions:
        logging.info(f"- {faction.name} (ID: {faction.id})")
    
    # Display all current relationships
    logging.info("\nCURRENT RELATIONSHIPS:")
    
    relationship_matrix = {}
    
    for faction in factions:
        relationship_matrix[faction.id] = {}
        for other_faction in factions:
            if faction.id != other_faction.id:
                rel = faction.get_relationship(other_faction.id)
                relationship_matrix[faction.id][other_faction.id] = rel
                logging.info(f"{faction.name} → {other_faction.name}: {rel}")
    
    # Set a negative relationship if none exists
    negative_relationship_exists = False
    
    for faction in factions:
        for other_faction in factions:
            if faction.id != other_faction.id:
                rel = relationship_matrix[faction.id][other_faction.id]
                if rel < 0:
                    negative_relationship_exists = True
                    logging.info(f"\nNegative relationship found: {faction.name} → {other_faction.name}: {rel}")
    
    # Find a pair of factions without negative relationships to set one
    if not negative_relationship_exists and len(factions) >= 2:
        f1 = factions[0]
        f2 = factions[1]
        
        # Set negative relationships
        logging.info(f"\nSetting negative relationship: {f1.name} → {f2.name}: -2 (Hot War)")
        faction_repo.set_relationship(f1.id, f2.id, -2)
        
        # Verify the relationship was set
        f1_updated = faction_repo.find_by_id(f1.id)
        rel = f1_updated.get_relationship(f2.id)
        logging.info(f"After update: {f1.name} → {f2.name}: {rel}")
        
        # Test the reverse direction
        logging.info(f"Setting negative relationship: {f2.name} → {f1.name}: -1 (Cold War)")
        faction_repo.set_relationship(f2.id, f1.id, -1)
        
        # Verify the relationship was set
        f2_updated = faction_repo.find_by_id(f2.id)
        rel = f2_updated.get_relationship(f1.id)
        logging.info(f"After update: {f2.name} → {f1.name}: {rel}")
    
    # Get districts for testing enemy penalty calculation
    districts = district_repo.find_all()
    
    if not districts:
        logging.error("No districts found!")
        return
    
    # Find agents to test enemy penalty calculation
    logging.info("\nTESTING ENEMY PENALTY CALCULATION")
    
    # Get agents from different factions in the same district
    for district in districts:
        logging.info(f"\nChecking district: {district.name} (ID: {district.id})")
        
        # Get all agents in this district
        agents_by_faction = {}
        for faction in factions:
            # Get agents for this faction in this district
            query = """
                SELECT id, name, faction_id
                FROM agents
                WHERE district_id = :district_id
                AND faction_id = :faction_id
            """
            
            results = db_manager.execute_query(query, {
                "district_id": district.id,
                "faction_id": faction.id
            })
            
            if results:
                agents_by_faction[faction.id] = [dict(row) for row in results]
                logging.info(f"Faction {faction.name} has {len(agents_by_faction[faction.id])} agents in district {district.name}")
        
        # Test enemy penalty calculation for each faction with agents
        for faction_id, agents in agents_by_faction.items():
            if not agents:
                continue
                
            faction = faction_repo.find_by_id(faction_id)
            logging.info(f"\nCalculating enemy penalties for faction: {faction.name}")
            
            # Get an agent to test with
            agent = agents[0]
            
            # Calculate enemy penalties
            total_penalty, breakdown = action_manager._calculate_enemy_piece_penalties(
                agent["id"],
                "agent",
                faction_id,
                district.id,
                1  # assuming turn 1
            )
            
            logging.info(f"Total enemy penalty: {total_penalty}")
            if breakdown:
                for entry in breakdown:
                    logging.info(f"- {entry['source_type']} {entry['source_name']}: -{entry['penalty']} ({entry['reason']})")
            else:
                logging.info("No penalty breakdown found.")
                
            # Check if there should be penalties based on relationships
            any_negative = False
            for other_id in faction_repo.get_all_faction_ids():
                if other_id != faction_id:
                    rel = faction.get_relationship(other_id)
                    if rel < 0:
                        any_negative = True
                        other_faction = faction_repo.find_by_id(other_id)
                        # Check if other faction has agents in the same district
                        if other_id in agents_by_faction and agents_by_faction[other_id]:
                            logging.info(f"Faction {faction.name} has relationship {rel} with {other_faction.name}, " +
                                         f"which has {len(agents_by_faction[other_id])} agents in the same district")
            
            if not any_negative:
                logging.info(f"Faction {faction.name} has no negative relationships, so no penalties expected")
    
    logging.info("\nTest completed")

if __name__ == "__main__":
    main() 