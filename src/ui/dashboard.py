import tkinter as tk
from tkinter import ttk
import logging


class DashboardPanel:
    """Dashboard panel showing game overview and quick actions."""
    
    def __init__(self, parent, db_manager, district_repository, faction_repository, 
                 agent_repository, squadron_repository):
        """Initialize the dashboard panel.
        
        Args:
            parent: Parent widget.
            db_manager: Database manager instance.
            district_repository: Repository for district operations.
            faction_repository: Repository for faction operations.
            agent_repository: Repository for agent operations.
            squadron_repository: Repository for squadron operations.
        """
        self.parent = parent
        self.db_manager = db_manager
        self.district_repository = district_repository
        self.faction_repository = faction_repository
        self.agent_repository = agent_repository
        self.squadron_repository = squadron_repository
        
        # Create main frame
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill=tk.BOTH, expand=True)
        
        # Create dashboard layout
        self.create_layout()
        
        # Load initial data
        self.load_data()
    
    def create_layout(self):
        """Create the dashboard layout."""
        # Top row for game info
        self.info_frame = ttk.LabelFrame(self.frame, text="Game Information")
        self.info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Game info grid
        self.game_title_label = ttk.Label(self.info_frame, text="Campaign:")
        self.game_title_label.grid(row=0, column=0, padx=5, pady=2, sticky=tk.W)
        
        self.game_title_value = ttk.Label(self.info_frame, text="Loading...")
        self.game_title_value.grid(row=0, column=1, padx=5, pady=2, sticky=tk.W)
        
        self.turn_label = ttk.Label(self.info_frame, text="Current Turn:")
        self.turn_label.grid(row=0, column=2, padx=5, pady=2, sticky=tk.W)
        
        self.turn_value = ttk.Label(self.info_frame, text="Loading...")
        self.turn_value.grid(row=0, column=3, padx=5, pady=2, sticky=tk.W)
        
        self.phase_label = ttk.Label(self.info_frame, text="Current Phase:")
        self.phase_label.grid(row=0, column=4, padx=5, pady=2, sticky=tk.W)
        
        self.phase_value = ttk.Label(self.info_frame, text="Loading...")
        self.phase_value.grid(row=0, column=5, padx=5, pady=2, sticky=tk.W)
        
        # Middle section with 3 columns
        self.middle_frame = ttk.Frame(self.frame)
        self.middle_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Configure grid
        self.middle_frame.columnconfigure(0, weight=1)
        self.middle_frame.columnconfigure(1, weight=1)
        self.middle_frame.columnconfigure(2, weight=1)
        self.middle_frame.rowconfigure(0, weight=1)
        
        # Faction summary
        self.faction_frame = ttk.LabelFrame(self.middle_frame, text="Factions")
        self.faction_frame.grid(row=0, column=0, padx=5, pady=5, sticky=tk.NSEW)
        
        # Faction treeview
        self.faction_tree = ttk.Treeview(
            self.faction_frame, 
            columns=("faction_id", "name", "districts", "agents", "squadrons"),
            show="headings",
            height=10
        )
        self.faction_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configure columns
        self.faction_tree.heading("faction_id", text="ID")
        self.faction_tree.heading("name", text="Name")
        self.faction_tree.heading("districts", text="Districts")
        self.faction_tree.heading("agents", text="Agents")
        self.faction_tree.heading("squadrons", text="Squadrons")
        
        self.faction_tree.column("faction_id", width=0, stretch=False)  # Hide ID column
        self.faction_tree.column("name", width=150)
        self.faction_tree.column("districts", width=80, anchor=tk.CENTER)
        self.faction_tree.column("agents", width=80, anchor=tk.CENTER)
        self.faction_tree.column("squadrons", width=80, anchor=tk.CENTER)
        
        # District summary
        self.district_frame = ttk.LabelFrame(self.middle_frame, text="Districts")
        self.district_frame.grid(row=0, column=1, padx=5, pady=5, sticky=tk.NSEW)
        
        # District treeview
        self.district_tree = ttk.Treeview(
            self.district_frame, 
            columns=("district_id", "name", "factions", "influence_remaining"),
            show="headings",
            height=10
        )
        self.district_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configure columns
        self.district_tree.heading("district_id", text="ID")
        self.district_tree.heading("name", text="Name")
        self.district_tree.heading("factions", text="Factions")
        self.district_tree.heading("influence_remaining", text="Influence Available")
        
        self.district_tree.column("district_id", width=0, stretch=False)  # Hide ID column
        self.district_tree.column("name", width=150)
        self.district_tree.column("factions", width=80, anchor=tk.CENTER)
        self.district_tree.column("influence_remaining", width=120, anchor=tk.CENTER)
        
        # Notifications area
        self.notification_frame = ttk.LabelFrame(self.middle_frame, text="Notifications")
        self.notification_frame.grid(row=0, column=2, padx=5, pady=5, sticky=tk.NSEW)
        
        # Notification list
        self.notification_text = tk.Text(self.notification_frame, height=10, width=40)
        self.notification_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Bottom row with action buttons
        self.action_frame = ttk.LabelFrame(self.frame, text="Quick Actions")
        self.action_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Action buttons
        self.process_turn_button = ttk.Button(
            self.action_frame, 
            text="Process Turn", 
            command=self.process_turn
        )
        self.process_turn_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.create_newspaper_button = ttk.Button(
            self.action_frame, 
            text="Create Newspaper", 
            command=self.create_newspaper
        )
        self.create_newspaper_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.save_game_button = ttk.Button(
            self.action_frame, 
            text="Save Game", 
            command=self.save_game
        )
        self.save_game_button.pack(side=tk.LEFT, padx=5, pady=5)
    
    def load_data(self):
        """Load data from the database."""
        try:
            # Load game state
            query = """
                SELECT current_turn, current_phase, campaign_name
                FROM game_state
                WHERE id = 'current'
            """
            
            result = self.db_manager.execute_query(query)
            
            if result:
                game_state = result[0]
                self.game_title_value.config(text=game_state["campaign_name"])
                self.turn_value.config(text=str(game_state["current_turn"]))
                self.phase_value.config(text=game_state["current_phase"])
            else:
                # Default values if no game state
                self.game_title_value.config(text="No game loaded")
                self.turn_value.config(text="N/A")
                self.phase_value.config(text="N/A")
            
            # Load faction data
            self.load_faction_data()
            
            # Load district data
            self.load_district_data()
            
            # Load notifications
            self.load_notifications()
        except Exception as e:
            logging.error(f"Error loading dashboard data: {str(e)}")
    
    def load_faction_data(self):
        """Load faction data into the faction treeview."""
        try:
            # Clear existing items
            for item in self.faction_tree.get_children():
                self.faction_tree.delete(item)
            
            # Get all factions
            factions = self.faction_repository.find_all()
            
            for faction in factions:
                # Count districts with any influence
                district_count = 0
                for district in self.district_repository.find_all():
                    if district.get_faction_influence(faction.id) > 0:
                        district_count += 1
                
                # Count agents
                agent_count = len(self.agent_repository.find_by_faction(faction.id))
                
                # Count squadrons
                squadron_count = len(self.squadron_repository.find_by_faction(faction.id))
                
                # Add to treeview
                self.faction_tree.insert(
                    "", 
                    tk.END, 
                    values=(faction.id, faction.name, district_count, agent_count, squadron_count)
                )
        except Exception as e:
            logging.error(f"Error loading faction data: {str(e)}")
    
    def load_district_data(self):
        """Load district data into the district treeview."""
        try:
            # Clear existing items
            for item in self.district_tree.get_children():
                self.district_tree.delete(item)
            
            # Get all districts
            districts = self.district_repository.find_all()
            
            for district in districts:
                # Count factions with any influence
                faction_count = len(district.faction_influence)
                
                # Get remaining influence
                influence_remaining = district.influence_pool
                
                # Add to treeview
                self.district_tree.insert(
                    "", 
                    tk.END, 
                    values=(district.id, district.name, faction_count, influence_remaining)
                )
        except Exception as e:
            logging.error(f"Error loading district data: {str(e)}")
    
    def load_notifications(self):
        """Load notifications into the notification area."""
        try:
            # Clear existing notifications
            self.notification_text.delete(1.0, tk.END)
            
            # Get current turn
            query = """
                SELECT current_turn
                FROM game_state
                WHERE id = 'current'
            """
            
            result = self.db_manager.execute_query(query)
            
            if not result:
                return
                
            current_turn = result[0]["current_turn"]
            
            # Get recent events from turn history
            query = """
                SELECT action_description, result_description, created_at
                FROM turn_history
                WHERE turn_number = :current_turn
                ORDER BY created_at DESC
                LIMIT 10
            """
            
            events = self.db_manager.execute_query(query, {"current_turn": current_turn})
            
            # Display events
            self.notification_text.insert(tk.END, "Recent Events:\n\n")
            
            for event in events:
                self.notification_text.insert(tk.END, f"• {event['action_description']}\n")
                if event["result_description"]:
                    self.notification_text.insert(tk.END, f"  Result: {event['result_description']}\n")
                self.notification_text.insert(tk.END, "\n")
            
            # Get pending conflicts
            query = """
                SELECT COUNT(*) as conflict_count
                FROM conflicts
                WHERE turn_number = :current_turn
                AND resolution_status = 'pending'
            """
            
            conflict_result = self.db_manager.execute_query(query, {"current_turn": current_turn})
            
            if conflict_result and conflict_result[0]["conflict_count"] > 0:
                self.notification_text.insert(
                    tk.END, 
                    f"ATTENTION: {conflict_result[0]['conflict_count']} conflicts need resolution!\n"
                )
        except Exception as e:
            logging.error(f"Error loading notifications: {str(e)}")
    
    def refresh(self):
        """Refresh all data in the dashboard."""
        self.load_data()
    
    # Action methods
    def process_turn(self):
        """Handle process turn button click."""
        # This should link to the Turn Resolution panel
        logging.info("Process turn action requested")
        pass
    
    def create_newspaper(self):
        """Handle create newspaper button click."""
        # This should link to the Newspaper panel
        logging.info("Create newspaper action requested")
        pass
    
    def save_game(self):
        """Handle save game button click."""
        # This should link to the save game functionality
        logging.info("Save game action requested")
        pass