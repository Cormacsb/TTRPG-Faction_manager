import tkinter as tk
from tkinter import ttk, messagebox
import logging
import os
import json
from datetime import datetime
from PIL import Image, ImageTk
from src.logic.action import ActionManager

class ActionPanel(ttk.Frame):
    """Panel for creating and managing actions."""
    
    def __init__(self, parent, db_manager, turn_manager, district_repository, faction_repository, 
                 agent_repository, squadron_repository):
        """Initialize the action panel.
        
        Args:
            parent: Parent widget.
            db_manager: Database manager instance.
            turn_manager: Turn manager instance.
            district_repository: Repository for district operations.
            faction_repository: Repository for faction operations.
            agent_repository: Repository for agent operations.
            squadron_repository: Repository for squadron operations.
        """
        super().__init__(parent)
        self.parent = parent
        self.db_manager = db_manager
        self.turn_manager = turn_manager
        self.district_repository = district_repository
        self.faction_repository = faction_repository
        self.agent_repository = agent_repository
        self.squadron_repository = squadron_repository
        
        # Create the action manager
        self.action_manager = ActionManager(
            db_manager,
            district_repository,
            faction_repository,
            agent_repository,
            squadron_repository
        )
        
        # Internal state variables
        self.selected_piece = None
        self.selected_piece_type = None
        self.selected_district = None
        self.selected_action_type = None
        self.selected_faction = None
        self.selected_target_faction = None
        
        # Get current turn info
        self.turn_info = self.turn_manager.get_current_turn()
        
        # Initialize UI elements
        self._create_widgets()
        
        # Create right-click context menu
        self._create_context_menu()
        
        # Load initial data
        self._load_actions()
        self._update_available_pieces()

    def _check_faction_relationships(self):
        """Debug method to check faction relationships and potential enemy penalties."""
        try:
            # Create a diagnostic window
            diag_window = tk.Toplevel(self)
            diag_window.title("Faction Relationship Diagnostics")
            diag_window.geometry("800x600")
            
            # Create text widget to display results
            results_text = tk.Text(diag_window, wrap="word")
            results_text.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Add a scrollbar
            scrollbar = ttk.Scrollbar(results_text, orient="vertical", command=results_text.yview)
            results_text.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side="right", fill="y")
            
            # Get all factions
            factions = self.faction_repository.find_all()
            
            results_text.insert("end", f"Found {len(factions)} factions\n\n")
            
            # Create a relationship matrix
            results_text.insert("end", "RELATIONSHIP MATRIX:\n")
            results_text.insert("end", "-" * 80 + "\n")
            
            # Header row with faction names
            header = "          "
            for faction in factions:
                header += f"{faction.name[:10]:<12}"
            results_text.insert("end", header + "\n")
            
            # Relationship rows
            for faction1 in factions:
                row = f"{faction1.name[:10]:<12}"
                for faction2 in factions:
                    if faction1.id == faction2.id:
                        row += "----      "
                    else:
                        rel = faction1.get_relationship(faction2.id)
                        row += f"{rel:<10} "
                results_text.insert("end", row + "\n")
            
            results_text.insert("end", "\n\n")
            
            # Get current turn
            turn_info = self.turn_manager.get_current_turn()
            turn_number = turn_info["current_turn"]
            
            # Check for factions with agents/squadrons in the same district
            results_text.insert("end", "FACTIONS WITH PIECES IN SAME DISTRICTS:\n")
            results_text.insert("end", "-" * 80 + "\n")
            
            # Get all districts
            districts = self.district_repository.find_all()
            
            for district in districts:
                # Get agents in this district by faction
                query = """
                    SELECT faction_id, COUNT(*) as count
                    FROM agents
                    WHERE district_id = :district_id
                    GROUP BY faction_id
                """
                agent_counts = self.db_manager.execute_query(query, {"district_id": district.id})
                
                # Get squadrons in this district by faction
                query = """
                    SELECT faction_id, COUNT(*) as count
                    FROM squadrons
                    WHERE district_id = :district_id
                    GROUP BY faction_id
                """
                squadron_counts = self.db_manager.execute_query(query, {"district_id": district.id})
                
                # Combine counts
                faction_counts = {}
                for row in agent_counts:
                    faction_id = row["faction_id"]
                    count = row["count"]
                    faction_counts[faction_id] = {"agents": count, "squadrons": 0}
                
                for row in squadron_counts:
                    faction_id = row["faction_id"]
                    count = row["count"]
                    if faction_id in faction_counts:
                        faction_counts[faction_id]["squadrons"] = count
                    else:
                        faction_counts[faction_id] = {"agents": 0, "squadrons": count}
                
                # Skip if less than 2 factions
                if len(faction_counts) < 2:
                    continue
                
                results_text.insert("end", f"District: {district.name}\n")
                
                # Show faction counts
                for faction_id, counts in faction_counts.items():
                    faction = self.faction_repository.find_by_id(faction_id)
                    if faction:
                        results_text.insert("end", f"  - {faction.name}: {counts['agents']} agents, {counts['squadrons']} squadrons\n")
                
                # Check for negative relationships between factions in this district
                results_text.insert("end", "  Negative Relationships:\n")
                found_negative = False
                
                for faction1_id in faction_counts:
                    faction1 = self.faction_repository.find_by_id(faction1_id)
                    for faction2_id in faction_counts:
                        if faction1_id != faction2_id:
                            faction2 = self.faction_repository.find_by_id(faction2_id)
                            rel = faction1.get_relationship(faction2_id)
                            if rel < 0:
                                found_negative = True
                                results_text.insert("end", f"    {faction1.name} → {faction2.name}: {rel}\n")
                
                if not found_negative:
                    results_text.insert("end", "    None found\n")
                
                results_text.insert("end", "\n")
            
            # Check sample enemy penalties
            results_text.insert("end", "SAMPLE ENEMY PENALTY CALCULATIONS:\n")
            results_text.insert("end", "-" * 80 + "\n")
            
            # Create action manager for calculations
            from src.logic.action import ActionManager
            action_manager = ActionManager(
                self.db_manager,
                self.district_repository,
                self.faction_repository,
                self.agent_repository,
                self.squadron_repository
            )
            
            # Get a sample agent from each faction
            for faction in factions:
                query = """
                    SELECT id, name, district_id
                    FROM agents
                    WHERE faction_id = :faction_id
                    LIMIT 1
                """
                agent_result = self.db_manager.execute_query(query, {"faction_id": faction.id})
                
                if agent_result:
                    agent = dict(agent_result[0])
                    district = self.district_repository.find_by_id(agent["district_id"])
                    
                    results_text.insert("end", f"Agent: {agent['name']} (Faction: {faction.name}, District: {district.name if district else 'Unknown'})\n")
                    
                    # Calculate enemy penalties
                    enemy_penalty, penalty_breakdown = action_manager._calculate_enemy_piece_penalties(
                        agent["id"],
                        "agent",
                        faction.id,
                        agent["district_id"],
                        turn_number
                    )
                    
                    results_text.insert("end", f"  Total Enemy Penalty: {enemy_penalty}\n")
                    
                    if penalty_breakdown:
                        for penalty in penalty_breakdown:
                            source_type = penalty.get("source_type", "unknown")
                            source_name = penalty.get("source_name", "unknown")
                            penalty_value = penalty.get("penalty", 0)
                            reason = penalty.get("reason", "unknown")
                            results_text.insert("end", f"  - {source_type.title()} {source_name}: {penalty_value} ({reason})\n")
                    else:
                        results_text.insert("end", "  No penalties found\n")
                    
                    results_text.insert("end", "\n")
            
            # Make text widget read-only
            results_text.config(state="disabled")
            
        except Exception as e:
            logging.error(f"Error in faction relationship diagnostic: {str(e)}")
            logging.exception("Full traceback:")
            messagebox.showerror("Error", f"Error checking faction relationships: {str(e)}")

    def _create_context_menu(self):
        """Create the context menu for the action tree."""
        self.context_menu = tk.Menu(self.action_tree, tearoff=0)
        self.context_menu.add_command(label="Delete Action", command=self._delete_selected_action)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Check Faction Relationships", command=self._check_faction_relationships)
        
        # Add binding for right-click
        self.action_tree.bind("<Button-3>", self._show_context_menu)
    
    def _show_context_menu(self, event):
        """Show the context menu on right click."""
        self.context_menu.post(event.x_root, event.y_root) 