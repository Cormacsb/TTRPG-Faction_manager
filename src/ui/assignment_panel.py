import tkinter as tk
from tkinter import ttk, messagebox
import logging
import uuid
from datetime import datetime


class AssignmentPanel(ttk.Frame):
    """Panel for assigning agents and squadrons to tasks."""
    
    def __init__(self, parent, db_manager, agent_repository, squadron_repository, 
                 faction_repository, district_repository):
        """Initialize the assignment panel.
        
        Args:
            parent: Parent widget.
            db_manager: Database manager instance.
            agent_repository: Repository for agent operations.
            squadron_repository: Repository for squadron operations.
            faction_repository: Repository for faction operations.
            district_repository: Repository for district operations.
        """
        super().__init__(parent)
        
        self.db_manager = db_manager
        self.agent_repository = agent_repository
        self.squadron_repository = squadron_repository
        self.faction_repository = faction_repository
        self.district_repository = district_repository
        
        # Initialize UI
        self._init_ui()
        
        # Load initial data
        self._load_factions()
        self._load_districts()
        self._load_pieces()
    
    def _init_ui(self):
        """Initialize UI components."""
        # Create main container
        self.main_frame = ttk.Frame(self)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create top filter frame
        self.filter_frame = ttk.LabelFrame(self.main_frame, text="Filters")
        self.filter_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Create piece type filter
        ttk.Label(self.filter_frame, text="Piece Type:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.piece_type_var = tk.StringVar(value="all")
        self.piece_type_combo = ttk.Combobox(self.filter_frame, textvariable=self.piece_type_var, state="readonly")
        self.piece_type_combo['values'] = ["all", "agent", "squadron"]
        self.piece_type_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        self.piece_type_combo.bind("<<ComboboxSelected>>", self._on_filter_changed)
        
        # Create faction filter
        ttk.Label(self.filter_frame, text="Faction:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.faction_filter_var = tk.StringVar(value="all")
        self.faction_filter = ttk.Combobox(self.filter_frame, textvariable=self.faction_filter_var, state="readonly")
        self.faction_filter.grid(row=0, column=3, sticky=(tk.W, tk.E), padx=5, pady=5)
        self.faction_filter.bind("<<ComboboxSelected>>", self._on_filter_changed)
        
        # Create district filter
        ttk.Label(self.filter_frame, text="District:").grid(row=0, column=4, sticky=tk.W, padx=5, pady=5)
        self.district_filter_var = tk.StringVar(value="all")
        self.district_filter = ttk.Combobox(self.filter_frame, textvariable=self.district_filter_var, state="readonly")
        self.district_filter.grid(row=0, column=5, sticky=(tk.W, tk.E), padx=5, pady=5)
        self.district_filter.bind("<<ComboboxSelected>>", self._on_filter_changed)
        
        # Create task filter
        ttk.Label(self.filter_frame, text="Task:").grid(row=0, column=6, sticky=tk.W, padx=5, pady=5)
        self.task_filter_var = tk.StringVar(value="all")
        self.task_filter = ttk.Combobox(self.filter_frame, textvariable=self.task_filter_var, state="readonly")
        self.task_filter['values'] = ["all", "unassigned", "monitor", "gain_influence", "take_influence", "freeform", "initiate_conflict"]
        self.task_filter.grid(row=0, column=7, sticky=(tk.W, tk.E), padx=5, pady=5)
        self.task_filter.bind("<<ComboboxSelected>>", self._on_filter_changed)
        
        # Create search filter
        ttk.Label(self.filter_frame, text="Search:").grid(row=0, column=8, sticky=tk.W, padx=5, pady=5)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(self.filter_frame, textvariable=self.search_var)
        self.search_entry.grid(row=0, column=9, sticky=(tk.W, tk.E), padx=5, pady=5)
        self.search_var.trace_add("write", lambda name, index, mode: self._on_filter_changed(None))
        
        # Add refresh button
        self.refresh_button = ttk.Button(self.filter_frame, text="Refresh", command=self._load_pieces)
        self.refresh_button.grid(row=0, column=10, padx=5, pady=5)
        
        # Configure grid columns in filter frame
        self.filter_frame.columnconfigure(1, weight=1)
        self.filter_frame.columnconfigure(3, weight=1)
        self.filter_frame.columnconfigure(5, weight=1)
        self.filter_frame.columnconfigure(7, weight=1)
        self.filter_frame.columnconfigure(9, weight=3)
        
        # Create split pane for pieces list and assignment form
        self.paned_window = ttk.PanedWindow(self.main_frame, orient=tk.HORIZONTAL)
        self.paned_window.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create pieces tree frame
        self.pieces_frame = ttk.Frame(self.paned_window)
        self.paned_window.add(self.pieces_frame, weight=3)
        
        # Create pieces tree
        self._create_pieces_tree()
        
        # Create assignment form frame
        self.assignment_frame = ttk.LabelFrame(self.paned_window, text="Assignment")
        self.paned_window.add(self.assignment_frame, weight=2)
        
        # Create assignment form
        self._create_assignment_form()
        
        # Create status bar
        self.status_frame = ttk.Frame(self.main_frame)
        self.status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.status_label = ttk.Label(self.status_frame, text="Ready")
        self.status_label.pack(side=tk.LEFT, padx=5)
        
        # Disable assignment controls initially
        self._disable_assignment_controls()
    
    def _create_pieces_tree(self):
        """Create the tree view for pieces and their assignments."""
        # Create tree and scrollbar
        columns = ("name", "type", "faction", "district", "task", "details")
        self.pieces_tree = ttk.Treeview(self.pieces_frame, columns=columns, show="headings", selectmode="browse")
        
        # Configure columns
        self.pieces_tree.heading("name", text="Name")
        self.pieces_tree.heading("type", text="Type")
        self.pieces_tree.heading("faction", text="Faction")
        self.pieces_tree.heading("district", text="District")
        self.pieces_tree.heading("task", text="Task")
        self.pieces_tree.heading("details", text="Details")
        
        # Set column widths
        self.pieces_tree.column("name", width=150, minwidth=100)
        self.pieces_tree.column("type", width=80, minwidth=80)
        self.pieces_tree.column("faction", width=120, minwidth=100)
        self.pieces_tree.column("district", width=120, minwidth=100)
        self.pieces_tree.column("task", width=120, minwidth=100)
        self.pieces_tree.column("details", width=250, minwidth=150)
        
        # Create scrollbars
        vsb = ttk.Scrollbar(self.pieces_frame, orient="vertical", command=self.pieces_tree.yview)
        hsb = ttk.Scrollbar(self.pieces_frame, orient="horizontal", command=self.pieces_tree.xview)
        self.pieces_tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Grid layout
        self.pieces_tree.grid(row=0, column=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        vsb.grid(row=0, column=1, sticky=(tk.N, tk.S))
        hsb.grid(row=1, column=0, sticky=(tk.E, tk.W))
        
        # Configure grid weights
        self.pieces_frame.rowconfigure(0, weight=1)
        self.pieces_frame.columnconfigure(0, weight=1)
        
        # Bind selection event
        self.pieces_tree.bind("<<TreeviewSelect>>", self._on_piece_selected)
    
    def _create_assignment_form(self):
        """Create the assignment form."""
        # Current piece label
        ttk.Label(self.assignment_frame, text="Selected Piece:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.selected_piece_label = ttk.Label(self.assignment_frame, text="None")
        self.selected_piece_label.grid(row=0, column=1, columnspan=3, sticky=tk.W, padx=5, pady=5)
        
        # Piece type label
        ttk.Label(self.assignment_frame, text="Type:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.piece_type_label = ttk.Label(self.assignment_frame, text="")
        self.piece_type_label.grid(row=1, column=1, columnspan=3, sticky=tk.W, padx=5, pady=5)
        
        # Faction label
        ttk.Label(self.assignment_frame, text="Faction:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.faction_label = ttk.Label(self.assignment_frame, text="")
        self.faction_label.grid(row=2, column=1, columnspan=3, sticky=tk.W, padx=5, pady=5)
        
        # Separator
        ttk.Separator(self.assignment_frame, orient=tk.HORIZONTAL).grid(row=3, column=0, columnspan=4, sticky=(tk.E, tk.W), padx=5, pady=10)
        
        # District Assignment
        ttk.Label(self.assignment_frame, text="District:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        self.district_var = tk.StringVar()
        self.district_combo = ttk.Combobox(self.assignment_frame, textvariable=self.district_var, state="readonly")
        self.district_combo.grid(row=4, column=1, columnspan=3, sticky=(tk.W, tk.E), padx=5, pady=5)
        self.district_combo.bind("<<ComboboxSelected>>", self._on_district_changed)
        
        # Task type
        ttk.Label(self.assignment_frame, text="Task:").grid(row=5, column=0, sticky=tk.W, padx=5, pady=5)
        self.task_var = tk.StringVar(value="monitor")
        self.task_combo = ttk.Combobox(self.assignment_frame, textvariable=self.task_var, state="readonly")
        self.task_combo['values'] = ["monitor", "gain_influence", "take_influence", "freeform", "initiate_conflict"]
        self.task_combo.grid(row=5, column=1, columnspan=3, sticky=(tk.W, tk.E), padx=5, pady=5)
        self.task_combo.bind("<<ComboboxSelected>>", self._on_task_changed)
        
        # Target faction (for take_influence and initiate_conflict)
        ttk.Label(self.assignment_frame, text="Target Faction:").grid(row=6, column=0, sticky=tk.W, padx=5, pady=5)
        self.target_faction_var = tk.StringVar()
        self.target_faction_combo = ttk.Combobox(self.assignment_frame, textvariable=self.target_faction_var, state="readonly")
        self.target_faction_combo.grid(row=6, column=1, columnspan=3, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # Manual modifier
        ttk.Label(self.assignment_frame, text="Manual Modifier:").grid(row=7, column=0, sticky=tk.W, padx=5, pady=5)
        self.manual_modifier_var = tk.StringVar(value="0")
        self.manual_modifier_spin = ttk.Spinbox(self.assignment_frame, from_=-10, to=10, width=5, textvariable=self.manual_modifier_var)
        self.manual_modifier_spin.grid(row=7, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Description (for freeform and initiate_conflict)
        ttk.Label(self.assignment_frame, text="Description:").grid(row=8, column=0, sticky=tk.W, padx=5, pady=5)
        self.description_var = tk.StringVar()
        self.description_entry = ttk.Entry(self.assignment_frame, textvariable=self.description_var)
        self.description_entry.grid(row=8, column=1, columnspan=3, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # DC (for freeform and initiate_conflict)
        ttk.Label(self.assignment_frame, text="DC:").grid(row=9, column=0, sticky=tk.W, padx=5, pady=5)
        self.dc_var = tk.StringVar(value="15")
        self.dc_spin = ttk.Spinbox(self.assignment_frame, from_=5, to=30, width=5, textvariable=self.dc_var)
        self.dc_spin.grid(row=9, column=1, sticky=tk.W, padx=5, pady=5)
        
        # Separator for agent/squadron specific controls
        ttk.Separator(self.assignment_frame, orient=tk.HORIZONTAL).grid(row=10, column=0, columnspan=4, sticky=(tk.E, tk.W), padx=5, pady=10)
        
        # Agent-specific controls
        self.agent_frame = ttk.LabelFrame(self.assignment_frame, text="Agent Parameters")
        self.agent_frame.grid(row=11, column=0, columnspan=4, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # Agent attribute
        ttk.Label(self.agent_frame, text="Attribute:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.agent_attr_var = tk.StringVar()
        self.agent_attr_combo = ttk.Combobox(self.agent_frame, textvariable=self.agent_attr_var, state="readonly")
        self.agent_attr_combo['values'] = ["might", "finesse", "presence", "intellect", "attunement"]
        self.agent_attr_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # Agent skill
        ttk.Label(self.agent_frame, text="Skill:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.agent_skill_var = tk.StringVar()
        self.agent_skill_combo = ttk.Combobox(self.agent_frame, textvariable=self.agent_skill_var, state="readonly")
        self.agent_skill_combo['values'] = ["combat", "infiltration", "persuasion", "streetwise", "survival", "artifice", "arcana"]
        self.agent_skill_combo.grid(row=0, column=3, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # Squadron-specific controls
        self.squadron_frame = ttk.LabelFrame(self.assignment_frame, text="Squadron Parameters")
        self.squadron_frame.grid(row=12, column=0, columnspan=4, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # Squadron aptitude
        ttk.Label(self.squadron_frame, text="Aptitude:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.squadron_apt_var = tk.StringVar()
        self.squadron_apt_combo = ttk.Combobox(self.squadron_frame, textvariable=self.squadron_apt_var, state="readonly")
        self.squadron_apt_combo['values'] = ["combat", "underworld", "social", "technical", "labor", "arcane", "wilderness", "monitoring"]
        self.squadron_apt_combo.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # Mobility display (informational)
        ttk.Label(self.squadron_frame, text="Mobility:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        self.mobility_label = ttk.Label(self.squadron_frame, text="")
        self.mobility_label.grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        
        # Action buttons
        self.button_frame = ttk.Frame(self.assignment_frame)
        self.button_frame.grid(row=13, column=0, columnspan=4, sticky=(tk.E, tk.W), padx=5, pady=10)
        
        self.clear_button = ttk.Button(self.button_frame, text="Clear Assignment", command=self._clear_assignment)
        self.clear_button.pack(side=tk.LEFT, padx=5)
        
        self.assign_all_button = ttk.Button(self.button_frame, text="Assign All Tasks", command=self._assign_all_tasks)
        self.assign_all_button.pack(side=tk.LEFT, padx=5)
        
        self.assign_button = ttk.Button(self.button_frame, text="Assign Task", command=self._assign_task)
        self.assign_button.pack(side=tk.RIGHT, padx=5)
        
        # Configure grid weights in the assignment frame
        self.assignment_frame.columnconfigure(1, weight=1)
        self.assignment_frame.columnconfigure(2, weight=1)
        self.assignment_frame.columnconfigure(3, weight=1)
    
    def _load_factions(self):
        """Load factions into the filter and assignment dropdowns."""
        try:
            # Get all factions
            factions = self.faction_repository.find_all()
            logging.info(f"Assignment Panel - Loading {len(factions)} factions")
            
            # Create faction options for filter
            faction_values = [("all", "All Factions")]
            faction_values.extend([(f.id, f.name) for f in factions])
            
            # Update faction filter
            self.faction_filter['values'] = [f[1] for f in faction_values]
            self.faction_filter.set("All Factions")  # Set the actual text value, not the ID
            
            # Store mapping for lookup
            self._faction_filter_map = {f[1]: f[0] for f in faction_values}
            logging.info(f"Assignment Panel - Created faction filter map: {self._faction_filter_map}")
            
            # Create faction options for target faction combo (excluding "All")
            target_faction_values = [(f.id, f.name) for f in factions]
            self.target_faction_combo['values'] = [f[1] for f in target_faction_values]
            if target_faction_values:
                self.target_faction_combo.set(target_faction_values[0][1])  # Set first faction as default
            
            self._target_faction_map = {f[1]: f[0] for f in target_faction_values}
            logging.info(f"Assignment Panel - Created target faction map: {self._target_faction_map}")
            
        except Exception as e:
            logging.error(f"Error loading factions: {str(e)}")
            messagebox.showerror("Error", "Failed to load factions")
    
    def _load_districts(self):
        """Load districts into the filter and assignment dropdowns."""
        try:
            # Get all districts
            districts = self.district_repository.find_all()
            logging.info(f"Assignment Panel - Loading {len(districts)} districts")
            
            # Create district options for filter
            district_values = [("all", "All Districts"), ("none", "Unassigned")]
            district_values.extend([(d.id, d.name) for d in districts])
            
            # Update district filter
            self.district_filter['values'] = [d[1] for d in district_values]
            self.district_filter.set("All Districts")  # Set the actual text value, not the ID
            
            # Store mapping for lookup
            self._district_filter_map = {d[1]: d[0] for d in district_values}
            logging.info(f"Assignment Panel - Created district filter map: {self._district_filter_map}")
            
            # Create district options for assignment combo (excluding "All" and "Unassigned")
            district_assign_values = [(d.id, d.name) for d in districts]
            self.district_combo['values'] = [d[1] for d in district_assign_values]
            if district_assign_values:
                self.district_combo.set(district_assign_values[0][1])  # Set first district as default
            
            self._district_combo_map = {d[1]: d[0] for d in district_assign_values}
            logging.info(f"Assignment Panel - Created district combo map: {self._district_combo_map}")
            
        except Exception as e:
            logging.error(f"Error loading districts: {str(e)}")
            messagebox.showerror("Error", "Failed to load districts")
    
    def _load_pieces(self):
        """Load pieces into the tree view based on current filters."""
        try:
            # Clear existing items
            for item in self.pieces_tree.get_children():
                self.pieces_tree.delete(item)
            
            # Get filter values
            piece_type_filter = self.piece_type_var.get()
            faction_filter = self.faction_filter.get()  # Use the actual combobox value, not the variable
            district_filter = self.district_filter.get()  # Use the actual combobox value, not the variable
            task_filter = self.task_filter_var.get()
            search_text = self.search_var.get().lower()
            
            # Log the filter values for debugging
            logging.info(f"Assignment Panel - Loading pieces with filters: type={piece_type_filter}, faction={faction_filter}, district={district_filter}, task={task_filter}")
            
            # Get faction and district IDs from filter values
            faction_id = self._faction_filter_map.get(faction_filter)
            district_id = self._district_filter_map.get(district_filter)
            
            # If faction_id or district_id is None, try with default value
            if faction_id is None and faction_filter == "":
                faction_id = "all"
                logging.info(f"Assignment Panel - Using default 'all' for empty faction filter")
            
            if district_id is None and district_filter == "":
                district_id = "all"
                logging.info(f"Assignment Panel - Using default 'all' for empty district filter")
            
            # Log the resolved IDs for debugging
            logging.info(f"Assignment Panel - Resolved faction_id={faction_id}, district_id={district_id}")
            
            # Load agents if needed
            agents = []
            if piece_type_filter in ["all", "agent"]:
                agents = self.agent_repository.find_all()
                logging.info(f"Assignment Panel - Found {len(agents)} agents")
                for agent in agents:
                    logging.info(f"Assignment Panel - Agent: {agent.id}, {agent.name}, faction={agent.faction_id}, district={agent.district_id}")
            
            # Load squadrons if needed
            squadrons = []
            if piece_type_filter in ["all", "squadron"]:
                squadrons = self.squadron_repository.find_all()
                logging.info(f"Assignment Panel - Found {len(squadrons)} squadrons")
                for squadron in squadrons:
                    logging.info(f"Assignment Panel - Squadron: {squadron.id}, {squadron.name}, faction={squadron.faction_id}, district={squadron.district_id}")
            
            # Process agents
            for agent in agents:
                if self._passes_filters(agent, "agent", faction_id, district_id, task_filter, search_text):
                    self._add_piece_to_tree(agent, "Agent")
                else:
                    logging.info(f"Assignment Panel - Agent {agent.name} does not pass filters")
            
            # Process squadrons
            for squadron in squadrons:
                if self._passes_filters(squadron, "squadron", faction_id, district_id, task_filter, search_text):
                    self._add_piece_to_tree(squadron, "Squadron")
                else:
                    logging.info(f"Assignment Panel - Squadron {squadron.name} does not pass filters")
            
            # Update status
            piece_count = len(self.pieces_tree.get_children())
            self.status_label.config(text=f"Loaded {piece_count} pieces")
            
        except Exception as e:
            logging.error(f"Error loading pieces: {str(e)}")
            messagebox.showerror("Error", "Failed to load pieces")
    
    def _passes_filters(self, piece, piece_type, faction_id, district_id, task_filter, search_text):
        """Check if a piece passes the current filters.
        
        Args:
            piece: The piece to check.
            piece_type: Type of the piece ("agent" or "squadron").
            faction_id: Faction ID filter (or "all").
            district_id: District ID filter (or "all" or "none").
            task_filter: Task type filter.
            search_text: Search text filter.
            
        Returns:
            bool: True if the piece passes all filters, False otherwise.
        """
        # Check faction filter
        if faction_id != "all" and piece.faction_id != faction_id:
            logging.info(f"Assignment Panel - {piece_type.capitalize()} {piece.name} failed faction filter: expected {faction_id}, got {piece.faction_id}")
            return False
        
        # Check district filter
        if district_id == "none" and piece.district_id is not None:
            logging.info(f"Assignment Panel - {piece_type.capitalize()} {piece.name} failed 'Unassigned' district filter: has district {piece.district_id}")
            return False
        elif district_id != "all" and district_id != "none" and piece.district_id != district_id:
            logging.info(f"Assignment Panel - {piece_type.capitalize()} {piece.name} failed district filter: expected {district_id}, got {piece.district_id}")
            return False
        
        # Check task filter
        if task_filter != "all":
            if task_filter == "unassigned" and piece.current_task is not None:
                logging.info(f"Assignment Panel - {piece_type.capitalize()} {piece.name} failed 'Unassigned' task filter: has task {piece.current_task.get('type')}")
                return False
            elif task_filter != "unassigned" and (piece.current_task is None or piece.current_task.get("type") != task_filter):
                current_task_type = piece.current_task.get("type") if piece.current_task else "None"
                logging.info(f"Assignment Panel - {piece_type.capitalize()} {piece.name} failed task filter: expected {task_filter}, got {current_task_type}")
                return False
        
        # Check search text
        if search_text:
            # Get faction name
            faction = self.faction_repository.find_by_id(piece.faction_id)
            faction_name = faction.name.lower() if faction else ""
            
            # Get district name
            district_name = ""
            if piece.district_id:
                district = self.district_repository.find_by_id(piece.district_id)
                district_name = district.name.lower() if district else ""
            
            # Check if search text appears in any relevant field
            search_fields = {
                "name": piece.name.lower(),
                "faction": faction_name,
                "district": district_name,
                "type": piece_type.lower()
            }
            
            if not any(search_text in value for value in search_fields.values()):
                logging.info(f"Assignment Panel - {piece_type.capitalize()} {piece.name} failed search filter: '{search_text}' not found in {search_fields}")
                return False
        
        # Piece passed all filters
        logging.info(f"Assignment Panel - {piece_type.capitalize()} {piece.name} PASSED all filters")
        return True
    
    def _add_piece_to_tree(self, piece, piece_type_label):
        """Add a piece to the tree view.
        
        Args:
            piece: The piece to add.
            piece_type_label: Display label for the piece type.
        """
        # Get faction name
        faction = self.faction_repository.find_by_id(piece.faction_id)
        faction_name = faction.name if faction else "Unknown"
        
        # Get district name
        district_name = "Unassigned"
        if piece.district_id:
            district = self.district_repository.find_by_id(piece.district_id)
            district_name = district.name if district else "Unknown"
        
        # Get task info
        task_name = "None"
        details = ""
        
        if piece.current_task:
            task_type = piece.current_task.get("type")
            task_name = task_type.replace("_", " ").title() if task_type else "Unknown"
            
            # Build details string based on task type
            if task_type == "monitor":
                if piece_type_label == "Agent":
                    attr = piece.current_task.get("attribute", "")
                    skill = piece.current_task.get("skill", "")
                    details = f"Using {attr.title()} + {skill.title()}"
                else:  # Squadron
                    aptitude = piece.current_task.get("primary_aptitude", "")
                    details = f"Using {aptitude.title()} aptitude"
            
            elif task_type in ["gain_influence", "take_influence"]:
                if task_type == "take_influence":
                    target_id = piece.current_task.get("target_faction")
                    target = self.faction_repository.find_by_id(target_id)
                    target_name = target.name if target else "Unknown"
                    details = f"Target: {target_name}"
                    
                    if piece_type_label == "Agent":
                        attr = piece.current_task.get("attribute", "")
                        skill = piece.current_task.get("skill", "")
                        details += f", Using {attr.title()} + {skill.title()}"
                    else:  # Squadron
                        aptitude = piece.current_task.get("primary_aptitude", "")
                        details += f", Using {aptitude.title()} aptitude"
                else:
                    if piece_type_label == "Agent":
                        attr = piece.current_task.get("attribute", "")
                        skill = piece.current_task.get("skill", "")
                        details = f"Using {attr.title()} + {skill.title()}"
                    else:  # Squadron
                        aptitude = piece.current_task.get("primary_aptitude", "")
                        details = f"Using {aptitude.title()} aptitude"
            
            elif task_type in ["freeform", "initiate_conflict"]:
                dc = piece.current_task.get("dc", "?")
                details = f"DC: {dc}"
                
                if task_type == "initiate_conflict":
                    target_id = piece.current_task.get("target_faction")
                    target = self.faction_repository.find_by_id(target_id)
                    target_name = target.name if target else "Unknown"
                    details += f", Target: {target_name}"
                
                desc = piece.current_task.get("description", "")
                if desc:
                    details += f", {desc[:30]}..." if len(desc) > 30 else f", {desc}"
        
        # Insert into tree
        self.pieces_tree.insert("", "end", piece.id, values=(
            piece.name,
            piece_type_label,
            faction_name,
            district_name,
            task_name,
            details
        ), tags=(piece_type_label.lower(),))
    
    def _on_filter_changed(self, event):
        """Handle filter change event."""
        # Log current filter values
        logging.info(f"Assignment Panel - Filter changed: type={self.piece_type_var.get()}, " + 
                     f"faction={self.faction_filter.get()}, district={self.district_filter.get()}, task={self.task_filter_var.get()}")
        
        # Clear any current selection
        if self.pieces_tree.selection():
            self.pieces_tree.selection_remove(self.pieces_tree.selection())
            self._disable_assignment_controls()
        
        # Reload the pieces with the new filters
        self._load_pieces()
    
    def _on_piece_selected(self, event):
        """Handle piece selection event."""
        try:
            # Get selected item
            selection = self.pieces_tree.selection()
            if not selection:
                self._disable_assignment_controls()
                return
            
            piece_id = selection[0]
            
            # Get piece values from tree
            values = self.pieces_tree.item(piece_id, "values")
            piece_type = values[1].lower()  # "Agent" or "Squadron"
            
            # Load piece data
            if piece_type == "agent":
                piece = self.agent_repository.find_by_id(piece_id)
                self.agent_frame.grid()
                self.squadron_frame.grid_remove()
            else:
                piece = self.squadron_repository.find_by_id(piece_id)
                self.agent_frame.grid_remove()
                self.squadron_frame.grid()
                
                # Update mobility display for squadrons
                self.mobility_label.config(text=str(piece.mobility))
            
            if not piece:
                self._disable_assignment_controls()
                self.status_label.config(text=f"Error: Could not load piece {piece_id}")
                return
            
            # Store selected piece info
            self.selected_piece = piece
            self.selected_piece_type = piece_type
            
            # Update piece info display
            self.selected_piece_label.config(text=piece.name)
            self.piece_type_label.config(text=piece_type.title())
            
            # Update faction display
            faction = self.faction_repository.find_by_id(piece.faction_id)
            faction_name = faction.name if faction else "Unknown"
            self.faction_label.config(text=faction_name)
            
            # Update assignment form with current values
            self._update_assignment_form(piece)
            
            # Enable assignment controls
            self._enable_assignment_controls()
            
        except Exception as e:
            logging.error(f"Error selecting piece: {str(e)}")
            self._disable_assignment_controls()
    
    def _update_assignment_form(self, piece):
        """Update the assignment form with the piece's current assignment.
        
        Args:
            piece: The selected piece.
        """
        # Clear form
        self.district_combo.set("")
        self.task_combo.set("monitor")
        self.target_faction_combo.set("")
        self.description_var.set("")
        self.dc_var.set("15")
        self.manual_modifier_var.set("0")
        self.agent_attr_combo.set("")
        self.agent_skill_combo.set("")
        self.squadron_apt_combo.set("")
        
        # If piece has a district assignment
        if piece.district_id:
            district = self.district_repository.find_by_id(piece.district_id)
            if district:
                # Find district name in combo values
                for name, id in self._district_combo_map.items():
                    if id == piece.district_id:
                        self.district_combo.set(name)
                        break
        
        # If piece has a task assignment
        if piece.current_task:
            task = piece.current_task
            
            # Set task type
            task_type = task.get("type", "monitor")
            self.task_combo.set(task_type)
            
            # Set target faction if applicable
            target_faction_id = task.get("target_faction")
            if target_faction_id:
                for name, id in self._target_faction_map.items():
                    if id == target_faction_id:
                        self.target_faction_combo.set(name)
                        break
            
            # Set description if applicable
            description = task.get("description", "")
            self.description_var.set(description)
            
            # Set DC if applicable
            dc = task.get("dc")
            if dc is not None:
                self.dc_var.set(str(dc))
            
            # Set manual modifier if applicable
            manual_modifier = task.get("manual_modifier", 0)
            self.manual_modifier_var.set(str(manual_modifier))
            
            # Set agent-specific fields
            if self.selected_piece_type == "agent":
                attribute = task.get("attribute")
                if attribute:
                    self.agent_attr_combo.set(attribute)
                
                skill = task.get("skill")
                if skill:
                    self.agent_skill_combo.set(skill)
            
            # Set squadron-specific fields
            else:
                aptitude = task.get("primary_aptitude")
                if aptitude:
                    self.squadron_apt_combo.set(aptitude)
        
        # Update form visibility based on task type
        self._update_form_visibility()
    
    def _update_form_visibility(self):
        """Update form field visibility based on current task type."""
        task_type = self.task_var.get()
        
        # Target faction visibility
        if task_type in ["take_influence", "initiate_conflict"]:
            self.target_faction_combo.config(state="readonly")
        else:
            self.target_faction_combo.config(state="disabled")
        
        # Description and DC visibility
        if task_type in ["freeform", "initiate_conflict"]:
            self.description_entry.config(state="normal")
            self.dc_spin.config(state="normal")
        else:
            self.description_entry.config(state="disabled")
            self.dc_spin.config(state="disabled")
    
    def _on_district_changed(self, event):
        """Handle district selection change."""
        district_name = self.district_combo.get()
        if not district_name:
            return
        
        district_id = self._district_combo_map.get(district_name)
        if not district_id:
            return
        
        # Update statistics based on selected district and task
        task_type = self.task_var.get()
        self._set_preferred_statistics(district_id, task_type)
    
    def _on_task_changed(self, event):
        """Handle task type change."""
        task_type = self.task_var.get()
        district_name = self.district_combo.get()
        
        # Get district ID if selected
        district_id = None
        if district_name:
            district_id = self._district_combo_map.get(district_name)
        
        # Update preferred statistics if district is selected
        if district_id:
            self._set_preferred_statistics(district_id, task_type)
        
        # Update form visibility
        self._update_form_visibility()
    
    def _set_preferred_statistics(self, district_id, task_type):
        """Set preferred attributes/skills/aptitudes based on district preferences and task type.
        
        Args:
            district_id (str): District ID
            task_type (str): Task type (monitor, gain_influence, etc.)
        """
        try:
            district = self.district_repository.find_by_id(district_id)
            if not district:
                return
            
            # Set appropriate attributes/skills/aptitudes based on task type
            if task_type == "monitor":
                if self.selected_piece_type == "agent":
                    # Set preferred monitoring attribute/skill for agent
                    self.agent_attr_combo.set(district.preferred_monitor_attribute)
                    self.agent_skill_combo.set(district.preferred_monitor_skill)
                else:
                    # Set preferred monitoring aptitude for squadron
                    self.squadron_apt_combo.set(district.preferred_monitor_squadron_aptitude)
            elif task_type in ["gain_influence", "take_influence"]:
                if self.selected_piece_type == "agent":
                    # Set preferred gain attribute/skill for agent
                    self.agent_attr_combo.set(district.preferred_gain_attribute)
                    self.agent_skill_combo.set(district.preferred_gain_skill)
                else:
                    # Set preferred gain aptitude for squadron
                    self.squadron_apt_combo.set(district.preferred_gain_squadron_aptitude)
        except Exception as e:
            logging.error(f"Error setting preferred statistics: {str(e)}")
    
    def _assign_task(self):
        """Update the current task for the selected piece."""
        try:
            if not hasattr(self, 'selected_piece') or not self.selected_piece:
                messagebox.showinfo("Info", "No piece selected")
                return
            
            # Get district
            district_name = self.district_combo.get()
            if not district_name:
                messagebox.showinfo("Info", "Please select a district")
                return
            
            district_id = self._district_combo_map.get(district_name)
            if not district_id:
                messagebox.showinfo("Info", "Invalid district selected")
                return
            
            # Get task type
            task_type = self.task_combo.get()
            if not task_type:
                messagebox.showinfo("Info", "Please select a task type")
                return
            
            # Get target faction for take_influence and initiate_conflict
            target_faction_id = None
            if task_type in ["take_influence", "initiate_conflict"]:
                target_name = self.target_faction_combo.get()
                if not target_name:
                    messagebox.showinfo("Info", "Please select a target faction")
                    return
                
                target_faction_id = self._target_faction_map.get(target_name)
                if not target_faction_id:
                    messagebox.showinfo("Info", "Invalid target faction selected")
                    return
                
            # Get DC for freeform and initiate_conflict
            dc = None
            if task_type in ["freeform", "initiate_conflict"]:
                try:
                    dc = int(self.dc_var.get())
                    if dc < 5 or dc > 30:
                        messagebox.showinfo("Info", "DC must be between 5 and 30")
                        return
                except ValueError:
                    messagebox.showinfo("Info", "DC must be a valid number")
                    return
            
            # Get manual modifier
            try:
                manual_modifier = int(self.manual_modifier_var.get())
                if manual_modifier < -10 or manual_modifier > 10:
                    messagebox.showinfo("Info", "Manual modifier must be between -10 and 10")
                    return
            except ValueError:
                messagebox.showinfo("Info", "Manual modifier must be a valid number")
                return
            
            # Get description for freeform and initiate_conflict
            description = None
            if task_type in ["freeform", "initiate_conflict"]:
                description = self.description_var.get()
                if not description:
                    messagebox.showinfo("Info", "Description is required for this task type")
                    return
            
            # Get attribute/skill/aptitude based on piece type
            attribute = None
            skill = None
            aptitude = None
            
            if self.selected_piece_type == "agent":
                attribute = self.agent_attr_combo.get()
                skill = self.agent_skill_combo.get()
                
                if not attribute or not skill:
                    messagebox.showinfo("Info", "Attribute and skill are required")
                    return
            else:  # Squadron
                aptitude = self.squadron_apt_combo.get()
                
                if not aptitude:
                    messagebox.showinfo("Info", "Aptitude is required")
                    return
            
            # Update task
            success = False
            if self.selected_piece_type == "agent":
                success = self.agent_repository.update_task(
                    self.selected_piece.id, district_id, task_type, target_faction_id,
                    attribute, skill, dc, True, manual_modifier
                )
            else:  # Squadron
                # For squadrons, always set monitoring=True for secondary monitoring
                success = self.squadron_repository.update_task(
                    self.selected_piece.id, district_id, task_type, target_faction_id,
                    aptitude, dc, True, manual_modifier
                )
            
            if success:
                # Reload pieces to show updated assignment
                self._load_pieces()
                
                # Reselect the piece
                self.pieces_tree.selection_set(self.selected_piece.id)
                self.pieces_tree.see(self.selected_piece.id)
                
                # Show success message
                self.status_label.config(text=f"Task updated successfully")
            else:
                messagebox.showerror("Error", "Failed to update task")
                
        except Exception as e:
            logging.error(f"Error updating task: {str(e)}")
            messagebox.showerror("Error", f"Error updating task: {str(e)}")
    
    def _clear_assignment(self):
        """Clear the selected piece's assignment."""
        try:
            if not hasattr(self, 'selected_piece') or not self.selected_piece:
                messagebox.showinfo("Info", "No piece selected")
                return
            
            # Confirm clear
            if not messagebox.askyesno("Confirm", "Clear assignment for this piece?"):
                return
            
            # Clear assignment
            success = False
            if self.selected_piece_type == "agent":
                success = self.agent_repository.clear_task(self.selected_piece.id)
            else:  # Squadron
                success = self.squadron_repository.clear_task(self.selected_piece.id)
            
            if success:
                # Reload pieces to show updated assignment
                self._load_pieces()
                
                # Reselect the piece
                self.pieces_tree.selection_set(self.selected_piece.id)
                self.pieces_tree.see(self.selected_piece.id)
                
                # Show success message
                self.status_label.config(text=f"Assignment cleared successfully")
                
                # Clear assignment form
                self.district_combo.set("")
                self.task_combo.set("monitor")
                self.target_faction_combo.set("")
                self.description_var.set("")
                self.dc_var.set("15")
                self.manual_modifier_var.set("0")
                self.agent_attr_combo.set("")
                self.agent_skill_combo.set("")
                self.squadron_apt_combo.set("")
            else:
                messagebox.showerror("Error", "Failed to clear assignment")
                
        except Exception as e:
            logging.error(f"Error clearing assignment: {str(e)}")
            messagebox.showerror("Error", f"Error clearing assignment: {str(e)}")
    
    def _enable_assignment_controls(self):
        """Enable assignment form controls."""
        self.district_combo.config(state="readonly")
        self.task_combo.config(state="readonly")
        
        # Update visibility based on task type
        self._update_form_visibility()
        
        # Enable other controls based on piece type
        if self.selected_piece_type == "agent":
            self.agent_attr_combo.config(state="readonly")
            self.agent_skill_combo.config(state="readonly")
        else:  # Squadron
            self.squadron_apt_combo.config(state="readonly")
        
        # Enable spinner
        self.manual_modifier_spin.config(state="normal")
        
        # Enable buttons
        self.assign_button.config(state="normal")
        self.clear_button.config(state="normal")
    
    def _disable_assignment_controls(self):
        """Disable assignment form controls."""
        # Clear selected piece info
        self.selected_piece_label.config(text="None")
        self.piece_type_label.config(text="")
        self.faction_label.config(text="")
        
        # Disable district and task selectors
        self.district_combo.config(state="disabled")
        self.task_combo.config(state="disabled")
        
        # Disable target faction selector
        self.target_faction_combo.config(state="disabled")
        
        # Disable description and DC
        self.description_entry.config(state="disabled")
        self.dc_spin.config(state="disabled")
        
        # Disable attribute/skill/aptitude selectors
        self.agent_attr_combo.config(state="disabled")
        self.agent_skill_combo.config(state="disabled")
        self.squadron_apt_combo.config(state="disabled")
        
        # Disable manual modifier
        self.manual_modifier_spin.config(state="disabled")
        
        # Disable buttons
        self.assign_button.config(state="disabled")
        self.clear_button.config(state="disabled")
        
        # Hide both frames
        self.agent_frame.grid_remove()
        self.squadron_frame.grid_remove()
    
    def _assign_all_tasks(self):
        """Assign all non-unassigned pieces to their currently set tasks."""
        if not messagebox.askyesno("Confirm", "This will assign all non-unassigned pieces to their current tasks. Continue?"):
            return
            
        try:
            assigned_count = 0
            errors = []
            
            # Get all agents
            agents = self.agent_repository.find_all()
            for agent in agents:
                # Skip if no current task or agent is unassigned
                if not agent.current_task or not agent.district_id:
                    continue
                    
                task = agent.current_task
                task_type = task.get("type", "monitor")
                district_id = agent.district_id
                target_faction_id = task.get("target_faction")
                attribute = task.get("attribute")
                skill = task.get("skill")
                dc = task.get("dc")
                manual_modifier = task.get("manual_modifier", 0)
                
                # Update the task
                success = self.agent_repository.update_task(
                    agent.id, district_id, task_type, target_faction_id,
                    attribute, skill, dc, True, manual_modifier
                )
                
                if success:
                    assigned_count += 1
                else:
                    errors.append(f"Failed to assign task to agent {agent.name}")
            
            # Get all squadrons
            squadrons = self.squadron_repository.find_all()
            for squadron in squadrons:
                # Skip if no current task or squadron is unassigned
                if not squadron.current_task or not squadron.district_id:
                    continue
                    
                task = squadron.current_task
                task_type = task.get("type", "monitor")
                district_id = squadron.district_id
                target_faction_id = task.get("target_faction")
                aptitude = task.get("primary_aptitude")
                dc = task.get("dc")
                manual_modifier = task.get("manual_modifier", 0)
                
                # Update the task
                success = self.squadron_repository.update_task(
                    squadron.id, district_id, task_type, target_faction_id,
                    aptitude, dc, True, manual_modifier
                )
                
                if success:
                    assigned_count += 1
                else:
                    errors.append(f"Failed to assign task to squadron {squadron.name}")
            
            # Reload the pieces to reflect changes
            self._load_pieces()
            
            # Show result
            if errors:
                error_message = "\n".join(errors[:5])
                if len(errors) > 5:
                    error_message += f"\n...and {len(errors) - 5} more errors"
                messagebox.showwarning("Assignment Results", 
                                      f"Assigned {assigned_count} tasks successfully.\nErrors: {error_message}")
            else:
                messagebox.showinfo("Assignment Complete", f"Successfully assigned {assigned_count} tasks.")
            
            self.status_label.config(text=f"Assigned {assigned_count} tasks")
            
        except Exception as e:
            logging.error(f"Error in bulk task assignment: {str(e)}")
            messagebox.showerror("Error", f"Error assigning tasks: {str(e)}")
            self.status_label.config(text="Error assigning tasks")
